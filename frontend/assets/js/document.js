let selectedFile = null;

const uploadZone = document.getElementById("upload-zone");
const fileInput = document.getElementById("file-input");
const analyzeBtn = document.getElementById("analyze-btn");

// ─── File Upload ───────────────────────────────────────────

uploadZone.addEventListener("click", () => fileInput.click());

uploadZone.addEventListener("dragover", e => {
  e.preventDefault();
  uploadZone.classList.add("dragover");
});

uploadZone.addEventListener("dragleave", () => uploadZone.classList.remove("dragover"));

uploadZone.addEventListener("drop", e => {
  e.preventDefault();
  uploadZone.classList.remove("dragover");
  const file = e.dataTransfer.files[0];
  if (file) handleFile(file);
});

fileInput.addEventListener("change", () => {
  if (fileInput.files[0]) handleFile(fileInput.files[0]);
});

document.getElementById("clear-file-btn").addEventListener("click", () => {
  selectedFile = null;
  fileInput.value = "";
  hideElement("file-preview");
  hideElement("results-panel");
  hideElement("ocr-card");
  analyzeBtn.disabled = true;
});

function handleFile(file) {
  selectedFile = file;
  setText("file-name", file.name);
  showElement("file-preview");
  analyzeBtn.disabled = false;

  if (file.type.startsWith("image/")) {
    const reader = new FileReader();
    reader.onload = e => {
      document.getElementById("img-preview").src = e.target.result;
      showElement("img-preview-wrap");
    };
    reader.readAsDataURL(file);
  } else {
    hideElement("img-preview-wrap");
  }
}

// ─── OCR Toggle ────────────────────────────────────────────

document.getElementById("toggle-ocr-btn").addEventListener("click", () => {
  const box = document.getElementById("ocr-text-box");
  const btn = document.getElementById("toggle-ocr-btn");
  if (box.classList.contains("hidden")) {
    box.classList.remove("hidden");
    btn.textContent = "Hide";
  } else {
    box.classList.add("hidden");
    btn.textContent = "Show";
  }
});

// ─── Analyze ───────────────────────────────────────────────

analyzeBtn.addEventListener("click", async () => {
  if (!selectedFile) return;

  const langCode = document.getElementById("language-select").value;
  const formData = new FormData();
  formData.append("file", selectedFile, selectedFile.name);
  formData.append("target_language", langCode);

  analyzeBtn.disabled = true;
  showStatus("Extracting text from document...");
  hideElement("results-panel");
  hideElement("ocr-card");

  try {
    showStatus("Understanding prescription...");
    const response = await fetch(`${API_BASE}/document/analyze`, {
      method: "POST", body: formData
    });

    if (!response.ok) {
      const err = await response.json();
      throw new Error(err.detail || "Analysis failed");
    }

    const data = await response.json();
    renderDocumentResults(data);
    hideStatus();
    showElement("results-panel");

  } catch (err) {
    hideStatus();
    alert("Error: " + err.message);
    analyzeBtn.disabled = false;
  }
});

// ─── Render Results ────────────────────────────────────────

function renderDocumentResults(data) {
  const exp = data.explanation;
  const langCode = data.target_language;

  // OCR text
  setText("ocr-text-box", data.ocr_text);
  showElement("ocr-card");

  // Patient info
  setText("patient-name", exp.patient_name || "Not found");
  setText("doctor-name", exp.doctor_name || "Not found");
  setText("doc-date", exp.date || "Not found");

  /// Summary — format for visual clarity
const summaryEl = document.getElementById("summary-text");
if (summaryEl) {
    let formatted = exp.summary
        .replace(/\[PAUSE\]/g, "</p><p>")
        .replace(/।।/g, "</p><p>")
        // Bold medication names
        .replace(/(पहिले|दुसरे|तिसरे|चौथे) — ([^:]+):/g, '<strong>$1 — $2:</strong>')
        // Bold "लक्षात ठेवा" section
        .replace(/(लक्षात ठेवा:)/g, '<strong>$1</strong>')
        // Convert bullet-like dashes to actual list items
        .replace(/- /g, '<li>')
        .replace(/<<li>([^<<]+)(?=<\/p>|<li>|<\/div>|$)/g, '<li>$1</li>');
    
    // Wrap list items in ul
    if (formatted.includes('<li>')) {
        formatted = formatted.replace(/(<li>[^<<]+<<\/li>)+/g, '<ul style="margin:8px 0; padding-left:20px;">$&</ul>');
    }
    
    summaryEl.innerHTML = `<p>${formatted}</p>`;
}
  // Medications
  const medList = document.getElementById("medications-list");
  medList.innerHTML = "";
  (exp.medications || []).forEach(med => {
    const card = document.createElement("div");
    card.className = "med-card";
    card.innerHTML = `
      <div class="med-name">${med.name || "Unknown"}</div>
      <div class="med-grid">
        <div class="med-field">
          <label>Purpose</label>
          <p>${med.purpose || "—"}</p>
        </div>
        <div class="med-field">
          <label>Dosage</label>
          <p>${med.dosage || "—"}</p>
        </div>
        <div class="med-field">
          <label>Duration</label>
          <p>${med.duration || "—"}</p>
        </div>
      </div>
      ${med.side_effects ? `<div class="med-side-effects">⚠️ Side effects: ${med.side_effects}</div>` : ""}
    `;
    medList.appendChild(card);
  });

  // Instructions
  const instrList = document.getElementById("instructions-list");
  instrList.innerHTML = "";
  if (exp.instructions && exp.instructions.length > 0) {
    exp.instructions.forEach(inst => {
      const li = document.createElement("li");
      li.textContent = inst;
      instrList.appendChild(li);
    });
    showElement("instructions-card");
  } else {
    hideElement("instructions-card");
  }

  // Speak button
  const speakBtn = document.getElementById("speak-btn");
  speakBtn.onclick = async () => {
    speakBtn.disabled = true;
    speakBtn.textContent = "Loading...";
    try {
      await speakText(exp.summary, langCode, "tts-audio", "tts-player");
    } catch (e) {
      alert("TTS failed: " + e.message);
    }
    speakBtn.disabled = false;
    speakBtn.innerHTML = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/><path d="M19.07 4.93a10 10 0 0 1 0 14.14"/></svg> Listen`;
  };
  // Initialize follow-up chat
  initDocFollowup(exp, langCode);
}

// ─── Follow-up Chat (Document) ─────────────────────────────

let docFollowupHistory = [];
let prescriptionContext = null;
let docLang = "en-IN";

function initDocFollowup(context, lang) {
  prescriptionContext = context;
  docLang = lang;
  docFollowupHistory = [];
  document.getElementById("chat-history").innerHTML = "";
}

async function sendDocFollowup(question) {
  if (!prescriptionContext || !question.trim()) return;

  const status = document.getElementById("followup-status");
  const sendBtn = document.getElementById("followup-send-btn");
  status.style.display = "block";
  status.textContent = "Thinking...";
  sendBtn.disabled = true;

  const formData = new FormData();
  formData.append("question", question);
  formData.append("language_code", docLang);
  formData.append("prescription_context", JSON.stringify(prescriptionContext));
  formData.append("history", JSON.stringify(docFollowupHistory));

  try {
    const res = await fetch(`${API_BASE}/document/followup`, {
      method: "POST", body: formData
    });
    if (!res.ok) throw new Error("Follow-up failed");
    const data = await res.json();

    const history = document.getElementById("chat-history");

    const userBubble = document.createElement("div");
    userBubble.className = "chat-bubble user";
    userBubble.innerHTML = `<div class="bubble-label">You</div>${question}`;
    history.appendChild(userBubble);

    const aiBubble = document.createElement("div");
    aiBubble.className = "chat-bubble assistant";
    aiBubble.innerHTML = `<div class="bubble-label">Swasthya Setu</div>${data.answer}`;
    history.appendChild(aiBubble);
    history.scrollTop = history.scrollHeight;

    docFollowupHistory.push({ question, answer: data.answer });

    // Auto TTS — voice output priority
    status.textContent = "Speaking...";
    try {
      const ttsForm = new FormData();
      ttsForm.append("text", data.answer);
      ttsForm.append("language_code", docLang);
      ttsForm.append("speaker", "auto");
      const ttsRes = await fetch(`${API_BASE}/voice/speak`, {
        method: "POST", body: ttsForm
      });
      if (ttsRes.ok) {
        const blob = await ttsRes.blob();
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);

        // Add audio player below the answer bubble
        const audioEl = document.createElement("audio");
        audioEl.src = url;
        audioEl.controls = true;
        audioEl.style.cssText = "width:100%; height:32px; margin-top:6px;";
        aiBubble.appendChild(audioEl);

        audio.play();
      }
    } catch (_) {}

  } catch (e) {
    alert("Follow-up failed: " + e.message);
  }

  status.style.display = "none";
  sendBtn.disabled = false;
  document.getElementById("followup-text-input").value = "";
}
// ─── Voice input for document follow-up ───────────────────

let docFollowupRecorder = null;
let docFollowupChunks = [];

const docFollowupMic = document.getElementById("followup-mic-btn");

docFollowupMic.addEventListener("click", async () => {
  if (docFollowupRecorder && docFollowupRecorder.state === "recording") {
    docFollowupRecorder.stop();
    docFollowupRecorder.stream.getTracks().forEach(t => t.stop());
    docFollowupMic.classList.remove("recording");
    return;
  }
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    docFollowupChunks = [];
    docFollowupRecorder = new MediaRecorder(stream);
    docFollowupRecorder.ondataavailable = e => {
      if (e.data.size > 0) docFollowupChunks.push(e.data);
    };
    docFollowupRecorder.onstop = () => {
      const blob = new Blob(docFollowupChunks, { type: "audio/wav" });
      sendDocFollowupAudio(blob);
    };
    docFollowupRecorder.start();
    docFollowupMic.classList.add("recording");
  } catch (e) {
    alert("Mic access denied.");
  }
});

async function sendDocFollowupAudio(audioBlob) {
  if (!prescriptionContext) return;

  const status = document.getElementById("followup-status");
  const sendBtn = document.getElementById("followup-send-btn");
  status.style.display = "block";
  status.textContent = "Transcribing...";
  sendBtn.disabled = true;

  const formData = new FormData();
  formData.append("question_audio", audioBlob, "followup.wav");
  formData.append("question", "");
  formData.append("language_code", docLang);
  formData.append("prescription_context", JSON.stringify(prescriptionContext));
  formData.append("history", JSON.stringify(docFollowupHistory));

  try {
    const res = await fetch(`${API_BASE}/document/followup`, {
      method: "POST", body: formData
    });
    if (!res.ok) throw new Error("Follow-up failed");
    const data = await res.json();

    const history = document.getElementById("chat-history");

    const userBubble = document.createElement("div");
    userBubble.className = "chat-bubble user";
    userBubble.innerHTML = `<div class="bubble-label">🎙️ You</div>${data.question || "Voice question"}`;
    history.appendChild(userBubble);

    const aiBubble = document.createElement("div");
    aiBubble.className = "chat-bubble assistant";
    aiBubble.innerHTML = `<div class="bubble-label">Swasthya Setu</div>${data.answer}`;
    history.appendChild(aiBubble);
    history.scrollTop = history.scrollHeight;

    docFollowupHistory.push({ question: data.question, answer: data.answer });

    // Auto TTS
    status.textContent = "Speaking...";
    const ttsForm = new FormData();
    ttsForm.append("text", data.answer);
    ttsForm.append("language_code", data.language_code || docLang);
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
    alert("Follow-up failed: " + e.message);
  }

  status.style.display = "none";
  sendBtn.disabled = false;
}