const API_BASE = window.location.origin + "/api";

const LANGUAGE_NAMES = {
  "hi-IN": "Hindi", "mr-IN": "Marathi", "ta-IN": "Tamil",
  "te-IN": "Telugu", "kn-IN": "Kannada", "gu-IN": "Gujarati",
  "bn-IN": "Bengali", "ml-IN": "Malayalam", "pa-IN": "Punjabi",
  "en-IN": "English", "unknown": "Auto"
};

function showStatus(text) {
  const bar = document.getElementById("status-bar");
  const txt = document.getElementById("status-text");
  if (bar && txt) { txt.textContent = text; bar.classList.remove("hidden");}
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
    const player = document.getElementById(playerContainerId);
    if (player && player !== audio) showElement(playerContainerId);
  }
}

// ─── FAQ Search ────────────────────────────────────────────

// ─── FAQ Search ────────────────────────────────────────────

function setFaqQuery(text) {
  const input = document.getElementById("faq-input");
  if (input) {
    input.value = text;
    input.focus();
    searchFAQ();
  }
}

function formatAnswerForDisplay(text) {
  if (!text) return "";
  return text
    .replace(/\*\*(.*?)\*\*/g, '$1')
    .replace(/\*(.*?)\*/g, '$1')
    .replace(/(\d+)\.\s+/g, '\n$1. ')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

async function searchFAQ() {
  const query = document.getElementById("faq-input")?.value?.trim();
  if (!query) return;

  const langCode = document.getElementById("faq-lang-select")?.value || "en-IN";
  const statusEl = document.getElementById("faq-status");
  const resultEl = document.getElementById("faq-result");
  const searchBtn = document.getElementById("faq-search-btn");

  if (!statusEl || !resultEl || !searchBtn) {
    console.error("FAQ elements missing");
    return;
  }

  statusEl.style.cssText = "display:flex !important; font-size:13px; color:var(--accent); align-items:center; gap:8px; margin-bottom:10px;";
  resultEl.style.display = "none";
  searchBtn.disabled = true;

  try {
    const formData = new FormData();
    formData.append("query", query);
    formData.append("language_code", langCode);
    formData.append("n_results", "3");

    const response = await fetch(`${API_BASE}/faq/search`, {
      method: "POST", body: formData
    });

    if (!response.ok) {
      const errText = await response.text();
      throw new Error(`HTTP ${response.status}: ${errText}`);
    }

    const data = await response.json();

    // Format and display answer
    const answerEl = document.getElementById("faq-answer");
    if (answerEl) {
      answerEl.textContent = formatAnswerForDisplay(data.answer);
    }

    // Color-coded source badges
    const sourcesEl = document.getElementById("faq-sources");
    if (sourcesEl) {
      sourcesEl.innerHTML = "";
      if (data.matched_faqs && data.matched_faqs.length > 0) {
        data.matched_faqs.forEach(faq => {
          const badge = document.createElement("span");
          let bgColor = "var(--bg)";
          let borderColor = "var(--border)";
          let textColor = "var(--text-muted)";
          
          if (faq.similarity >= 0.7) {
            bgColor = "var(--primary-pale)";
            borderColor = "rgba(15, 110, 86, 0.2)";
            textColor = "var(--primary)";
          } else if (faq.similarity >= 0.5) {
            bgColor = "var(--accent-pale)";
            borderColor = "rgba(24, 95, 165, 0.2)";
            textColor = "var(--accent)";
          }
          
          badge.style.cssText = `
            font-size: 12px; 
            padding: 4px 12px; 
            border-radius: 99px; 
            background: ${bgColor}; 
            color: ${textColor}; 
            border: 1px solid ${borderColor};
            font-weight: 500;
          `;
          badge.textContent = faq.category;
          sourcesEl.appendChild(badge);
        });
      }
    }

    resultEl.style.cssText = "display:flex !important; flex-direction:column; gap:16px; margin-top:8px;";

    // Speak button
    const speakBtn = document.getElementById("faq-speak-btn");
    if (speakBtn) {
      speakBtn.onclick = async () => {
        speakBtn.disabled = true;
        speakBtn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" style="animation:pulse 1s infinite"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/></svg> Loading...`;
        
        try {
          const ttsForm = new FormData();
          ttsForm.append("text", data.answer);
          ttsForm.append("language_code", langCode);
          ttsForm.append("speaker", "auto");
          const ttsRes = await fetch(`${API_BASE}/voice/speak`, { method: "POST", body: ttsForm });
          
          if (ttsRes.ok) {
            const blob = await ttsRes.blob();
            const url = URL.createObjectURL(blob);
            const audioEl = document.getElementById("faq-audio");
            if (audioEl) {
              audioEl.src = url;
              audioEl.style.cssText = "width:100%; height:40px; display:block !important; border-radius:var(--radius-sm);";
              audioEl.play();
            }
          }
        } catch (e) { 
          console.error("TTS failed:", e);
        }
        
        speakBtn.disabled = false;
        speakBtn.innerHTML = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/></svg> Listen to answer`;
      };
    }

  } catch (e) {
    console.error("FAQ search error:", e);
    alert("FAQ search failed: " + e.message);
  }

  statusEl.style.display = "none";
  if (searchBtn) searchBtn.disabled = false;
}

// ─── FAQ Voice Input ───────────────────────────────────────

let faqRecorder = null;
let faqAudioChunks = [];

const faqMicBtn = document.getElementById("faq-mic-btn");

faqMicBtn?.addEventListener("click", async () => {
  if (faqRecorder && faqRecorder.state === "recording") {
    stopFaqRecording();
    return;
  }

  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    faqAudioChunks = [];
    faqRecorder = new MediaRecorder(stream);

    faqRecorder.ondataavailable = e => {
      if (e.data.size > 0) faqAudioChunks.push(e.data);
    };

    faqRecorder.onstop = () => {
      const blob = new Blob(faqAudioChunks, { type: "audio/wav" });
      stream.getTracks().forEach(t => t.stop());
      sendFaqVoiceQuery(blob);
    };

    faqRecorder.start();
    faqMicBtn.classList.add("recording");
    document.getElementById("faq-input").placeholder = "● Recording... tap mic to stop";
    
    // Visual feedback
    const statusEl = document.getElementById("faq-status");
    statusEl.style.cssText = "display:flex !important; font-size:13px; color:var(--danger); align-items:center; gap:8px; margin-bottom:10px;";
    statusEl.innerHTML = `<div style="width:14px; height:14px; border-radius:50%; border:2px solid rgba(192,57,43,0.3); border-top-color:var(--danger); animation:spin 0.7s linear infinite;"></div> Recording... tap mic again to stop`;

  } catch (err) {
    alert("Microphone access denied. Please allow mic permissions.");
  }
});

function stopFaqRecording() {
  if (faqRecorder && faqRecorder.state !== "inactive") {
    faqRecorder.stop();
  }
  faqMicBtn.classList.remove("recording");
  document.getElementById("faq-input").placeholder = "Speak or type your question...";
}

async function sendFaqVoiceQuery(audioBlob) {
  const langCode = document.getElementById("faq-lang-select")?.value || "unknown";
  const statusEl = document.getElementById("faq-status");
  const resultEl = document.getElementById("faq-result");

  statusEl.style.cssText = "display:flex !important; font-size:13px; color:var(--accent); align-items:center; gap:8px; margin-bottom:10px;";
  statusEl.innerHTML = `<div style="width:14px; height:14px; border-radius:50%; border:2px solid rgba(24,95,165,0.3); border-top-color:var(--accent); animation:spin 0.7s linear infinite;"></div> Transcribing...`;

  try {
    const formData = new FormData();
    formData.append("audio", audioBlob, "faq_query.wav");
    formData.append("language_code", langCode);

    // Use the voice transcribe endpoint
    const sttRes = await fetch(`${API_BASE}/voice/transcribe`, {
      method: "POST",
      body: formData
    });

    if (!sttRes.ok) throw new Error("Voice transcription failed");
    const sttData = await sttRes.json();

    // Fill input with transcribed text
    const input = document.getElementById("faq-input");
    input.value = sttData.transcript || "";
    
    // Auto-trigger search
    if (input.value.trim()) {
      searchFAQ();
    }

  } catch (e) {
    statusEl.innerHTML = `<span style="color:var(--danger);">❌ Voice input failed: ${e.message}</span>`;
    setTimeout(() => { statusEl.style.display = "none"; }, 3000);
  }
}

// Wire up FAQ search on page load
document.addEventListener("DOMContentLoaded", () => {
  const searchBtn = document.getElementById("faq-search-btn");
  if (searchBtn) searchBtn.addEventListener("click", searchFAQ);
  
  const input = document.getElementById("faq-input");
  if (input) input.addEventListener("keydown", e => { 
    if (e.key === "Enter") searchFAQ(); 
  });
});