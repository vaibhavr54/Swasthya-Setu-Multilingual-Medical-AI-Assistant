const API_BASE = "http://localhost:8000/api";

const LANGUAGE_NAMES = {
  "hi-IN": "Hindi", "mr-IN": "Marathi", "ta-IN": "Tamil",
  "te-IN": "Telugu", "kn-IN": "Kannada", "gu-IN": "Gujarati",
  "bn-IN": "Bengali", "ml-IN": "Malayalam", "pa-IN": "Punjabi",
  "en-IN": "English", "unknown": "Auto"
};

function showStatus(text) {
  const bar = document.getElementById("status-bar");
  const txt = document.getElementById("status-text");
  if (bar && txt) { txt.textContent = text; bar.classList.remove("hidden"); }
}

function hideStatus() {
  const bar = document.getElementById("status-bar");
  if (bar) bar.classList.add("hidden");
}

function showElement(id) {
  const el = document.getElementById(id);
  if (el) el.classList.remove("hidden");
}

function hideElement(id) {
  const el = document.getElementById(id);
  if (el) el.classList.add("hidden");
}

function setHTML(id, html) {
  const el = document.getElementById(id);
  if (el) el.innerHTML = html;
}

function setText(id, text) {
  const el = document.getElementById(id);
  if (el) el.textContent = text || "—";
}

async function speakText(text, languageCode, audioElementId, playerContainerId) {
  const formData = new FormData();
  formData.append("text", text);
  formData.append("language_code", languageCode);
  formData.append("speaker", "anushka");

  const response = await fetch(`${API_BASE}/voice/speak`, {
    method: "POST", body: formData
  });

  if (!response.ok) throw new Error("TTS failed");

  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const audio = document.getElementById(audioElementId);
  if (audio) {
    audio.src = url;
    audio.play();
    // Show player container if it exists
    const player = document.getElementById(playerContainerId);
    if (player && player !== audio) showElement(playerContainerId);
  }
}