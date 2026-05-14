let mediaRecorder = null;
let audioChunks = [];
let timerInterval = null;
let seconds = 0;
let audioBlob = null;

const micBtn = document.getElementById("mic-btn");
const stopBtn = document.getElementById("stop-btn");
const analyzeBtn = document.getElementById("analyze-btn");
const resetBtn = document.getElementById("reset-btn");
const micStatus = document.getElementById("mic-status");
const timerEl = document.getElementById("timer");
const timerCount = document.getElementById("timer-count");

// ─── Recording ─────────────────────────────────────────────

micBtn.addEventListener("click", async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioChunks = [];
    mediaRecorder = new MediaRecorder(stream);

    mediaRecorder.ondataavailable = e => {
      if (e.data.size > 0) audioChunks.push(e.data);
    };

    mediaRecorder.onstop = () => {
      audioBlob = new Blob(audioChunks, { type: "audio/wav" });
      const url = URL.createObjectURL(audioBlob);
      const preview = document.getElementById("audio-preview");
      preview.src = url;
      showElement("audio-preview-card");
      analyzeBtn.disabled = false;
      micStatus.textContent = "Recording saved. Click Analyze to continue.";
    };

    mediaRecorder.start();
    micBtn.classList.add("recording");
    micStatus.textContent = "Recording... speak your symptoms clearly";
    stopBtn.disabled = false;
    analyzeBtn.disabled = true;
    showElement("timer");
    seconds = 0;
    timerCount.textContent = "0";
    timerInterval = setInterval(() => {
      seconds++;
      timerCount.textContent = seconds;
      if (seconds >= 60) stopRecording();
    }, 1000);

  } catch (err) {
    micStatus.textContent = "Microphone access denied. Please allow mic permissions.";
  }
});

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    mediaRecorder.stop();
    mediaRecorder.stream.getTracks().forEach(t => t.stop());
  }
  clearInterval(timerInterval);
  micBtn.classList.remove("recording");
  stopBtn.disabled = true;
  hideElement("timer");
}

stopBtn.addEventListener("click", stopRecording);

resetBtn.addEventListener("click", () => {
  stopRecording();
  audioBlob = null;
  audioChunks = [];
  analyzeBtn.disabled = true;
  micStatus.textContent = "Tap the mic and speak your symptoms";
  hideElement("audio-preview-card");
  hideElement("results-panel");
  hideElement("status-bar");
  document.getElementById("audio-preview").src = "";
});

// ─── Analyze ───────────────────────────────────────────────

analyzeBtn.addEventListener("click", async () => {
  if (!audioBlob) return;

  const langCode = document.getElementById("language-select").value;
  const formData = new FormData();
  formData.append("audio", audioBlob, "recording.wav");
  formData.append("language_code", langCode);

  analyzeBtn.disabled = true;
  showStatus("Transcribing your voice...");
  hideElement("results-panel");

  try {
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
    showElement("results-panel");

  } catch (err) {
    hideStatus();
    micStatus.textContent = `Error: ${err.message}`;
    analyzeBtn.disabled = false;
  }
});

// ─── Render Results ────────────────────────────────────────

function renderTriageResults(data) {
  const triage = data.triage;
  const detectedLang = data.detected_language || "en-IN";

  // Triage level box
  const levelBox = document.getElementById("triage-level-box");
  const level = triage.triage_level || "LOW";
  levelBox.textContent = level;
  levelBox.className = `triage-level-box level-${level.toLowerCase()}`;

  // Triage title + urgency
  const titleEl = document.getElementById("triage-level-title");
  if (titleEl) titleEl.textContent = level === "HIGH" ? "Urgent" : level === "MEDIUM" ? "Moderate" : "Low Priority";

  const urgencyEl = document.getElementById("urgency-message");
  if (urgencyEl) urgencyEl.textContent = triage.urgency_message || "—";

  // Transcript + detected language
  const transcriptEl = document.getElementById("transcript-text");
  if (transcriptEl) transcriptEl.textContent = data.transcript || "—";

  const langBadge = document.getElementById("detected-lang-badge");
  if (langBadge) langBadge.textContent = LANGUAGE_NAMES[detectedLang] || detectedLang;

  // Summary
  const summaryEl = document.getElementById("summary-text");
  if (summaryEl) summaryEl.textContent = triage.summary || "—";

  // Voice preview text (urgency message shown in green bar)
  const voicePreview = document.getElementById("voice-preview-text");
  if (voicePreview) voicePreview.textContent = triage.urgency_message || "";

  // Conditions
  const condList = document.getElementById("conditions-list");
  if (condList) {
    condList.innerHTML = "";
    (triage.possible_conditions || []).forEach(c => {
      const li = document.createElement("li");
      li.textContent = c;
      condList.appendChild(li);
    });

  }

  // Recommended action
  const actionEl = document.getElementById("recommended-action");
  if (actionEl) actionEl.textContent = triage.recommended_action || "—";

  // Follow-up questions
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
        const formData = new FormData();
        formData.append("text", triage.summary);
        formData.append("language_code", detectedLang);
        formData.append("speaker", "anushka");

        const response = await fetch(`${API_BASE}/voice/speak`, {
          method: "POST", body: formData
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
  // Initialize follow-up chat with this triage context
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
  document.getElementById("chat-history").innerHTML = "";
}

function addBubble(text, role) {
  const history = document.getElementById("chat-history");
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
  status.style.display = "block";
  status.textContent = "Thinking...";
  sendBtn.disabled = true;

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

    // Create assistant bubble first
    const history = document.getElementById("chat-history");
    const aiBubble = document.createElement("div");
    aiBubble.className = "chat-bubble assistant";
    aiBubble.innerHTML = `<div class="bubble-label">Swasthya Setu</div>${data.answer}`;
    history.appendChild(aiBubble);
    history.scrollTop = history.scrollHeight;

    followupHistory.push({ question: displayQuestion, answer: data.answer });

    // TTS — voice output priority
    status.textContent = "Speaking...";
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

      // Embed audio player in bubble
      const audioEl = document.createElement("audio");
      audioEl.src = url;
      audioEl.controls = true;
      audioEl.style.cssText = "width:100%; height:32px; margin-top:6px;";
      aiBubble.appendChild(audioEl);

      // Auto play
      const autoAudio = new Audio(url);
      autoAudio.play();
    } else {
      console.error("TTS failed:", await ttsRes.text());
    }

  } catch (e) {
    addBubble("Sorry, something went wrong. Please try again.", "assistant");
    console.error(e);
  }

  status.style.display = "none";
  sendBtn.disabled = false;
  document.getElementById("followup-text-input").value = "";
}

// ─── Follow-up Voice Input ───────────────────────────────

const followupMicBtn = document.getElementById("followup-mic-btn");

followupMicBtn.addEventListener("click", async () => {
  // Toggle: if recording, stop it
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
      // Auto-send voice question
      sendFollowup("", blob);
    };

    followupRecorder.start();
    followupMicBtn.classList.add("recording");
    document.getElementById("followup-status").style.display = "block";
    document.getElementById("followup-status").textContent = "● Recording... tap mic again to stop";

  } catch (err) {
    document.getElementById("followup-status").textContent = "Microphone access denied.";
  }
});

function stopFollowupRecording() {
  if (followupRecorder && followupRecorder.state !== "inactive") {
    followupRecorder.stop();
  }
  followupMicBtn.classList.remove("recording");
  document.getElementById("followup-status").textContent = "Processing...";
}

// Wire up text input send
document.getElementById("followup-send-btn").addEventListener("click", () => {
  const input = document.getElementById("followup-text-input");
  const text = input.value.trim();
  if (text) sendFollowup(text);
});

document.getElementById("followup-text-input").addEventListener("keydown", (e) => {
  if (e.key === "Enter") {
    const text = e.target.value.trim();
    if (text) sendFollowup(text);
  }
});