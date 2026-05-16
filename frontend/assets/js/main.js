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
    const player = document.getElementById(playerContainerId);
    if (player && player !== audio) showElement(playerContainerId);
  }
}

// ─── FAQ Search ────────────────────────────────────────────

function setFaqQuery(text) {
  const input = document.getElementById("faq-input");
  if (input) {
    input.value = text;
    input.focus();
    searchFAQ();
  }
}

async function searchFAQ() {
  const query = document.getElementById("faq-input")?.value?.trim();
  if (!query) return;

  const langCode = document.getElementById("faq-lang-select")?.value || "en-IN";
  const statusEl = document.getElementById("faq-status");
  const resultEl = document.getElementById("faq-result");
  const searchBtn = document.getElementById("faq-search-btn");

  if (!statusEl || !resultEl || !searchBtn) {
    console.error("FAQ elements missing:", { statusEl, resultEl, searchBtn });
    return;
  }

  // Force show status using cssText to override any inline display:none
  statusEl.style.cssText = "display:flex !important; font-size:13px; color:var(--accent); align-items:center; gap:8px; margin-bottom:10px;";
  resultEl.style.cssText = "display:none !important; flex-direction:column; gap:10px;";
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
    console.log("FAQ response:", data); // Debug log

    // Show answer
    const answerEl = document.getElementById("faq-answer");
    if (answerEl) answerEl.textContent = data.answer || "No answer received";

    // Show source badges
    const sourcesEl = document.getElementById("faq-sources");
    if (sourcesEl) {
      sourcesEl.innerHTML = "";
      if (data.matched_faqs && data.matched_faqs.length > 0) {
        data.matched_faqs.forEach(faq => {
          const badge = document.createElement("span");
          badge.style.cssText = "font-size:11px; padding:3px 10px; border-radius:99px; background:var(--accent-pale); color:var(--accent); border:1px solid rgba(24,95,165,0.15);";
          badge.textContent = `${faq.category} · ${Math.round((faq.similarity || 0) * 100)}% match`;
          sourcesEl.appendChild(badge);
        });
      }
    }

    // FORCE SHOW RESULT with !important
    resultEl.style.cssText = "display:flex !important; flex-direction:column; gap:10px;";

    // Speak button
    const speakBtn = document.getElementById("faq-speak-btn");
    if (speakBtn) {
      speakBtn.onclick = async () => {
        speakBtn.disabled = true;
        speakBtn.textContent = "Loading...";
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
              audioEl.style.cssText = "width:100%; height:32px; display:block !important;";
              audioEl.play();
            }
          }
        } catch (e) { 
          console.error("TTS failed:", e);
          alert("TTS failed"); 
        }
        speakBtn.disabled = false;
        speakBtn.innerHTML = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="11 5 6 9 2 9 2 15 6 15 11 19 11 5"/><path d="M15.54 8.46a5 5 0 0 1 0 7.07"/></svg> Listen`;
      };
    }

  } catch (e) {
    console.error("FAQ search error:", e);
    alert("FAQ search failed: " + e.message);
  }

  // Hide status
  statusEl.style.cssText = "display:none !important; font-size:13px; color:var(--accent); align-items:center; gap:8px; margin-bottom:10px;";
  if (searchBtn) searchBtn.disabled = false;
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