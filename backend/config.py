from dotenv import load_dotenv
import os
import platform

load_dotenv()

# ─── API Keys ──────────────────────────────────────────────────────────────
SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
GOOGLE_VISION_API_KEY = os.getenv("GOOGLE_VISION_API_KEY")

# ─── Base URLs ─────────────────────────────────────────────────────────────
SARVAM_BASE_URL = os.getenv("SARVAM_BASE_URL", "https://api.sarvam.ai")

# ─── Tesseract path — auto-detect per platform ─────────────────────────────
def get_tesseract_path() -> str:
    # Allow override via env variable
    env_path = os.getenv("TESSERACT_CMD")
    if env_path:
        return env_path

    system = platform.system()
    if system == "Windows":
        candidates = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            r"C:\Users\{}\AppData\Local\Tesseract-OCR\tesseract.exe".format(os.getenv("USERNAME", "")),
        ]
        for path in candidates:
            if os.path.exists(path):
                return path
        return candidates[0]  # fallback default

    elif system == "Darwin":  # macOS
        return "/usr/local/bin/tesseract"  # homebrew default

    else:  # Linux / Docker
        return "/usr/bin/tesseract"  # apt default

TESSERACT_CMD = get_tesseract_path()

# ─── Supported Languages ───────────────────────────────────────────────────
SUPPORTED_LANGUAGES = {
    "hi-IN": "Hindi",
    "mr-IN": "Marathi",
    "ta-IN": "Tamil",
    "te-IN": "Telugu",
    "kn-IN": "Kannada",
    "gu-IN": "Gujarati",
    "bn-IN": "Bengali",
    "ml-IN": "Malayalam",
    "pa-IN": "Punjabi",
    "en-IN": "English"
}

# ─── Validate required keys on startup ─────────────────────────────────────
def validate_config():
    missing = []
    if not SARVAM_API_KEY:
        missing.append("SARVAM_API_KEY")
    if not MISTRAL_API_KEY:
        missing.append("MISTRAL_API_KEY")
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")