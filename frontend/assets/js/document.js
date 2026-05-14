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

  // Summary
  setText("summary-text", exp.summary);

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
}