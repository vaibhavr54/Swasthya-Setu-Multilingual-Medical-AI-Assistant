from dotenv import load_dotenv
import os

load_dotenv()

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")
GOOGLE_VISION_API_KEY = os.getenv("GOOGLE_VISION_API_KEY")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

SARVAM_BASE_URL = "https://api.sarvam.ai"

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