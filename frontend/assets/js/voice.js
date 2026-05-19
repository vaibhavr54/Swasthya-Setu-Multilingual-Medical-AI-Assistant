let mediaRecorder = null;
let audioChunks = [];
let timerInterval = null;
let seconds = 0;
let audioBlob = null;

const micBtn = document.getElementById("mic-btn");
// These buttons may not exist in the HTML — guard every reference
const stopBtn = document.getElementById("stop-btn");
const analyzeBtn = document.getElementById("analyze-btn");
const resetBtn = document.getElementById("reset-btn");
const micStatus = document.getElementById("mic-status");
const timerEl = document.getElementById("timer");
const timerCount = document.getElementById("timer-count");

// ─── Helpers ───────────────────────────────────────────────

function setAnalyzeDisabled(val) {
  if (analyzeBtn) analyzeBtn.disabled = val;
}
function setStopDisabled(val) {
  if (stopBtn) stopBtn.disabled = val;
}

// ─── Recording ─────────────────────────────────────────────

// ─── Check mic permission state on load ───────────────────
(async () => {
  if (!navigator.permissions) return;
  try {
    const perm = await navigator.permissions.query({ name: "microphone" });
    if (perm.state === "denied") {
      showMicDenied();
    }
    perm.onchange = () => {
      if (perm.state === "denied") showMicDenied();
      else clearMicError();
    };
  } catch (_) {}
})();

function showMicDenied() {
  if (micStatus) {
    micStatus.innerHTML = `
      🚫 Mic blocked by browser.<br>
      <small style="color:var(--text-muted)">Click the 🔒 lock icon in your address bar → <b>Microphone</b> → <b>Allow</b>, then refresh.</small>`;
  }
  micBtn.classList.add("mic-denied");
  const stickyStatus = document.getElementById("sticky-status-text");
  if (stickyStatus) stickyStatus.innerHTML = "🚫 Mic blocked — click 🔒 in address bar → Allow mic → Refresh";
  const mobileMicStatus = document.getElementById("mic-status-mobile");
  if (mobileMicStatus) mobileMicStatus.innerHTML = micStatus ? micStatus.innerHTML : "";
}

function clearMicError() {
  if (micStatus) micStatus.textContent = "Tap mic and speak your symptoms";
  micBtn.classList.remove("mic-denied");
}

micBtn.addEventListener("click", async () => {
  // ── TOGGLE: if already recording, stop it ──
  if (mediaRecorder && mediaRecorder.state === "recording") {
    stopRecording();
    return;
  }

  // Pre-check permission before attempting
  if (navigator.permissions) {
    try {
      const perm = await navigator.permissions.query({ name: "microphone" });
      if (perm.state === "denied") {
        showMicDenied();
        return;
      }
    } catch (_) {}
  }

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    clearMicError();
    audioChunks = [];
    mediaRecorder = new MediaRecorder(stream);

    mediaRecorder.ondataavailable = e => {
      if (e.data.size > 0) audioChunks.push(e.data);
    };

    mediaRecorder.onstop = () => {
      audioBlob = new Blob(audioChunks, { type: "audio/wav" });
      const url = URL.createObjectURL(audioBlob);
      const preview = document.getElementById("audio-preview");
      if (preview) preview.src = url;
      showElement("audio-preview-card");
      // Auto-analyze immediately — no manual button needed
      analyzeAudio();
    };

    mediaRecorder.start();
    micBtn.classList.add("recording");
    if (micStatus) micStatus.textContent = "Recording… tap mic again to stop";
    setStopDisabled(false);
    setAnalyzeDisabled(true);
    showElement("timer");
    seconds = 0;
    if (timerCount) timerCount.textContent = "0";
    timerInterval = setInterval(() => {
      seconds++;
      if (timerCount) timerCount.textContent = seconds;
      if (seconds >= 60) stopRecording();
    }, 1000);

  } catch (err) {
    console.error("Mic error:", err);
    if (err.name === "NotAllowedError" || err.name === "PermissionDeniedError") {
      showMicDenied();
    } else if (err.name === "NotFoundError") {
      if (micStatus) micStatus.textContent = "No microphone found. Please connect a mic and try again.";
    } else {
      if (micStatus) micStatus.textContent = `Mic error: ${err.message}`;
    }
  }
});

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    mediaRecorder.stop();
    mediaRecorder.stream.getTracks().forEach(t => t.stop());
  }
  clearInterval(timerInterval);
  micBtn.classList.remove("recording");
  setStopDisabled(true);
  hideElement("timer");
}

if (stopBtn) stopBtn.addEventListener("click", stopRecording);

if (resetBtn) {
  resetBtn.addEventListener("click", () => {
    stopRecording();
    audioBlob = null;
    audioChunks = [];
    setAnalyzeDisabled(true);
    if (micStatus) micStatus.textContent = "Tap the mic and speak your symptoms";
    hideElement("audio-preview-card");
    hideElement("results-panel");
    hideElement("status-bar");
    const preview = document.getElementById("audio-preview");
    if (preview) preview.src = "";
  });
}

// ─── Analyze (auto-called after recording stops) ───────────

function setStatus(msg) {
  if (micStatus) micStatus.textContent = msg;
  const sticky = document.getElementById("sticky-status-text");
  if (sticky) sticky.textContent = msg;
  const mob = document.getElementById("mic-status-mobile");
  if (mob) mob.textContent = msg;
}

async function analyzeAudio() {
  if (!audioBlob) return;

  const langCode = document.getElementById("language-select").value;
  const formData = new FormData();
  formData.append("audio", audioBlob, "recording.wav");
  formData.append("language_code", langCode);

  micBtn.disabled = true;
  setStatus("Transcribing your voice...");
  showStatus("Transcribing your voice...");
  hideElement("results-panel");

  try {
    setStatus("Analyzing symptoms...");
    showStatus("Analyzing symptoms...");

    const response = await fetch(`${API_BASE}/voice/triage`, {
      method: "POST", body: formData
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || "Analysis failed");
    }

    const data = await response.json();
    renderTriageResults(data);
    hideStatus();
    setStatus("Analysis complete. Tap mic to record again.");
    showElement("results-panel");

  } catch (err) {
    hideStatus();
    setStatus(`Error: ${err.message}`);
  }

  micBtn.disabled = false;
}

// Keep analyze button wired up as fallback if it exists in HTML
if (analyzeBtn) {
  analyzeBtn.addEventListener("click", analyzeAudio);
}

// ─── Render Results ────────────────────────────────────────

function renderTriageResults(data) {
  const triage = data.triage;
  const detectedLang = data.detected_language || "en-IN";

  // Triage level box
  const levelBox = document.getElementById("triage-level-box");
  const level = triage.triage_level || "LOW";
  if (levelBox) {
    levelBox.textContent = level;
    levelBox.className = `triage-level-box level-${level.toLowerCase()}`;
  }

  const titleEl = document.getElementById("triage-level-title");
  if (titleEl) titleEl.textContent = level === "HIGH" ? "Urgent" : level === "MEDIUM" ? "Moderate" : "Low Priority";

  const urgencyEl = document.getElementById("urgency-message");
  if (urgencyEl) urgencyEl.textContent = triage.urgency_message || "—";

  const transcriptEl = document.getElementById("transcript-text");
  if (transcriptEl) transcriptEl.textContent = data.transcript || "—";

  const langBadge = document.getElementById("detected-lang-badge");
  if (langBadge) langBadge.textContent = LANGUAGE_NAMES[detectedLang] || detectedLang;

  const summaryEl = document.getElementById("summary-text");
  if (summaryEl) summaryEl.textContent = triage.summary || "—";

  const voicePreview = document.getElementById("voice-preview-text");
  if (voicePreview) voicePreview.textContent = triage.urgency_message || "";

  const condList = document.getElementById("conditions-list");
  if (condList) {
    condList.innerHTML = "";
    (triage.possible_conditions || []).forEach(c => {
      const li = document.createElement("li");
      li.textContent = c;
      condList.appendChild(li);
    });
  }

  const actionEl = document.getElementById("recommended-action");
  if (actionEl) actionEl.textContent = triage.recommended_action || "—";

  const fqList = document.getElementById("followup-list");
  if (fqList) {
    fqList.innerHTML = "";
    (triage.follow_up_questions || []).forEach(q => {
      const li = document.createElement("li");
      li.textContent = q;
      fqList.appendChild(li);
    });
  }

  // Speak button
  const speakBtn = document.getElementById("speak-btn");
  if (speakBtn) {
    speakBtn.onclick = async () => {
      speakBtn.disabled = true;
      speakBtn.textContent = "Loading...";
      try {
        const fd = new FormData();
        fd.append("text", triage.summary);
        fd.append("language_code", detectedLang);
        fd.append("speaker", "anushka");

        const response = await fetch(`${API_BASE}/voice/speak`, {
          method: "POST", body: fd
        });

        if (!response.ok) throw new Error("TTS request failed");

        const blob = await response.blob();
        const url = URL.createObjectURL(blob);
        const audio = document.getElementById("tts-audio");
        if (audio) {
          audio.src = url;
          audio.classList.remove("hidden");
          audio.play();
        }
      } catch (e) {
        alert("TTS failed: " + e.message);
      }

      speakBtn.disabled = false;
      speakBtn.innerHTML = `
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/>
          <path d="M15.54 8.46a5 5 0 0 1 0 7.07"/>
        </svg> Speak`;
    };
  }

  initFollowup(triage, detectedLang);
}

// ─── Follow-up Chat (Voice + Text) ────────────────────────

let followupHistory = [];
let triageContext = null;
let followupLang = "en-IN";
let followupRecorder = null;
let followupChunks = [];

function initFollowup(context, lang) {
  triageContext = context;
  followupLang = lang;
  followupHistory = [];
  const ch = document.getElementById("chat-history");
  if (ch) ch.innerHTML = "";
}

function addBubble(text, role) {
  const history = document.getElementById("chat-history");
  if (!history) return;
  const bubble = document.createElement("div");
  bubble.className = `chat-bubble ${role}`;
  bubble.innerHTML = `<div class="bubble-label">${role === "user" ? "You" : "Swasthya Setu"}</div>${text}`;
  history.appendChild(bubble);
  history.scrollTop = history.scrollHeight;
}

async function sendFollowup(questionText, audioBlob = null) {
  if (!triageContext) return;

  const status = document.getElementById("followup-status");
  const sendBtn = document.getElementById("followup-send-btn");
  if (status) { status.style.display = "block"; status.textContent = "Thinking..."; }
  if (sendBtn) sendBtn.disabled = true;

  const formData = new FormData();
  if (audioBlob) {
    formData.append("question_audio", audioBlob, "followup.wav");
    formData.append("question_text", "");
  } else {
    formData.append("question_text", questionText);
  }
  formData.append("language_code", followupLang);
  formData.append("triage_context", JSON.stringify(triageContext));
  formData.append("history", JSON.stringify(followupHistory));

  try {
    const res = await fetch(`${API_BASE}/voice/followup`, {
      method: "POST", body: formData
    });
    if (!res.ok) throw new Error("Follow-up failed");
    const data = await res.json();

    const displayQuestion = data.question || questionText || "🎙️ Voice question";
    addBubble(displayQuestion, "user");

    const history = document.getElementById("chat-history");
    const aiBubble = document.createElement("div");
    aiBubble.className = "chat-bubble assistant";
    aiBubble.innerHTML = `<div class="bubble-label">Swasthya Setu</div>${data.answer}`;
    if (history) { history.appendChild(aiBubble); history.scrollTop = history.scrollHeight; }

    followupHistory.push({ question: displayQuestion, answer: data.answer });

    if (status) status.textContent = "Speaking...";
    const ttsForm = new FormData();
    ttsForm.append("text", data.answer);
    ttsForm.append("language_code", data.detected_language || followupLang);
    ttsForm.append("speaker", "auto");

    const ttsRes = await fetch(`${API_BASE}/voice/speak`, {
      method: "POST", body: ttsForm
    });

    if (ttsRes.ok) {
      const blob = await ttsRes.blob();
      const url = URL.createObjectURL(blob);
      const audioEl = document.createElement("audio");
      audioEl.src = url;
      audioEl.controls = true;
      audioEl.style.cssText = "width:100%; height:32px; margin-top:6px;";
      aiBubble.appendChild(audioEl);
      new Audio(url).play();
    }

  } catch (e) {
    addBubble("Sorry, something went wrong. Please try again.", "assistant");
    console.error(e);
  }

  if (status) status.style.display = "none";
  if (sendBtn) sendBtn.disabled = false;
  const textInput = document.getElementById("followup-text-input");
  if (textInput) textInput.value = "";
}

// ─── Follow-up Voice Input ───────────────────────────────

const followupMicBtn = document.getElementById("followup-mic-btn");

if (followupMicBtn) {
  followupMicBtn.addEventListener("click", async () => {
    if (followupRecorder && followupRecorder.state === "recording") {
      stopFollowupRecording();
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      followupChunks = [];
      followupRecorder = new MediaRecorder(stream);

      followupRecorder.ondataavailable = e => {
        if (e.data.size > 0) followupChunks.push(e.data);
      };

      followupRecorder.onstop = () => {
        const blob = new Blob(followupChunks, { type: "audio/wav" });
        stream.getTracks().forEach(t => t.stop());
        sendFollowup("", blob);
      };

      followupRecorder.start();
      followupMicBtn.classList.add("recording");
      const fs = document.getElementById("followup-status");
      if (fs) { fs.style.display = "block"; fs.textContent = "● Recording… tap mic again to stop"; }

    } catch (err) {
      const fs = document.getElementById("followup-status");
      if (fs) fs.textContent = "Microphone access denied.";
    }
  });
}

function stopFollowupRecording() {
  if (followupRecorder && followupRecorder.state !== "inactive") {
    followupRecorder.stop();
  }
  if (followupMicBtn) followupMicBtn.classList.remove("recording");
  const fs = document.getElementById("followup-status");
  if (fs) fs.textContent = "Processing...";
}

// ─── Text follow-up send ─────────────────────────────────

const followupSendBtn = document.getElementById("followup-send-btn");
if (followupSendBtn) {
  followupSendBtn.addEventListener("click", () => {
    const input = document.getElementById("followup-text-input");
    const text = input ? input.value.trim() : "";
    if (text) sendFollowup(text);
  });
}

const followupTextInput = document.getElementById("followup-text-input");
if (followupTextInput) {
  followupTextInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
      const text = e.target.value.trim();
      if (text) sendFollowup(text);
    }
  });
}