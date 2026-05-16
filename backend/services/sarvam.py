import requests
import base64
from config import SARVAM_API_KEY, SARVAM_BASE_URL

headers = {
    "api-subscription-key": SARVAM_API_KEY,
}


# ─── Speech to Text (Saaras v3) ────────────────────────────────────────────

def speech_to_text(audio_bytes: bytes, language_code: str = "unknown") -> dict:
    url = f"{SARVAM_BASE_URL}/speech-to-text"
    files = {"file": ("audio.wav", audio_bytes, "audio/wav")}
    data = {"model": "saaras:v3", "mode": "transcribe"}
    if language_code and language_code != "unknown":
        data["language_code"] = language_code

    response = requests.post(url, headers=headers, files=files, data=data)
    if not response.ok:
        raise Exception(f"STT Error {response.status_code}: {response.text}")
    text = response.text.strip()
    if not text:
        raise Exception("STT returned empty response")
    import json
    return json.loads(text)


# ─── Text to Speech (Bulbul v2) ────────────────────────────────────────────

def text_to_speech(text: str, language_code: str = "hi-IN", speaker: str = "auto") -> bytes:
    import re

    language_speaker_map = {
        "hi-IN": "Ratan", "mr-IN": "anushka", "ta-IN": "Kavitha",
        "te-IN": "Vijay", "kn-IN": "anushka", "gu-IN": "Ratan",
        "bn-IN": "anushka", "ml-IN": "Kavitha", "pa-IN": "Ratan", "en-IN": "anushka",
    }
    if speaker == "auto":
        speaker = language_speaker_map.get(language_code, "anushka")

    range_connectors = {
        "hi-IN": "से", "mr-IN": "ते", "ta-IN": "முதல்", "te-IN": "నుండి",
        "kn-IN": "ರಿಂದ", "gu-IN": "થી", "bn-IN": "থেকে",
        "ml-IN": "മുതൽ", "pa-IN": "ਤੋਂ", "en-IN": "to",
    }
    connector = range_connectors.get(language_code, "to")
    text = re.sub(r'(\d+)\s*-\s*(\d+)', rf'\1 {connector} \2', text)
    text = re.sub(r'।([^\s])', '। \\1', text)

    url = f"{SARVAM_BASE_URL}/text-to-speech"

    def split_text(t, limit=490):
        if len(t) <= limit:
            return [t]
        chunks = []
        while len(t) > limit:
            split_at = t.rfind("।", 0, limit)
            if split_at == -1:
                split_at = t.rfind(".", 0, limit)
            if split_at == -1:
                split_at = t.rfind(" ", 0, limit)
            if split_at == -1:
                split_at = limit
            chunks.append(t[:split_at + 1].strip())
            t = t[split_at + 1:].strip()
        if t:
            chunks.append(t)
        return chunks

    def get_wav_params(wav_bytes):
        import struct
        channels = struct.unpack_from('<H', wav_bytes, 22)[0]
        sample_rate = struct.unpack_from('<I', wav_bytes, 24)[0]
        bit_depth = struct.unpack_from('<H', wav_bytes, 34)[0]
        return channels, sample_rate, bit_depth

    def extract_pcm(wav_bytes):
        idx = wav_bytes.find(b'data')
        if idx == -1:
            return wav_bytes[44:]
        return wav_bytes[idx + 8:]

    def build_wav(pcm_data, channels, sample_rate, bit_depth):
        import struct
        byte_rate = sample_rate * channels * bit_depth // 8
        block_align = channels * bit_depth // 8
        data_size = len(pcm_data)
        header = struct.pack('<4sI4s4sIHHIIHH4sI',
            b'RIFF', 36 + data_size, b'WAVE',
            b'fmt ', 16, 1, channels,
            sample_rate, byte_rate, block_align, bit_depth,
            b'data', data_size
        )
        return header + pcm_data

    chunks = split_text(text)
    all_pcm = b""
    wav_params = None

    for chunk in chunks:
        if not chunk:
            continue
        payload = {
            "inputs": [chunk],
            "target_language_code": language_code,
            "speaker": speaker,
            "model": "bulbul:v2",
            "enable_preprocessing": True,
            "pace": 0.9,
        }
        response = requests.post(
            url, headers={**headers, "Content-Type": "application/json"}, json=payload
        )
        if not response.ok:
            raise Exception(f"TTS Error {response.status_code}: {response.text}")
        wav_bytes = base64.b64decode(response.json()["audios"][0])
        if wav_params is None:
            wav_params = get_wav_params(wav_bytes)
        all_pcm += extract_pcm(wav_bytes)

    if wav_params is None:
        raise Exception("TTS returned no audio")
    channels, sample_rate, bit_depth = wav_params
    return build_wav(all_pcm, channels, sample_rate, bit_depth)


# ─── Translation (Mayura) ──────────────────────────────────────────────────

def translate_text(text: str, source_language: str = "en-IN", target_language: str = "hi-IN") -> str:
    url = f"{SARVAM_BASE_URL}/translate"
    payload = {
        "input": text,
        "source_language_code": source_language,
        "target_language_code": target_language,
        "model": "mayura:v1",
        "enable_preprocessing": True,
    }
    response = requests.post(url, headers={**headers, "Content-Type": "application/json"}, json=payload)
    if not response.ok:
        raise Exception(f"Translation Error {response.status_code}: {response.text}")
    return response.json()["translated_text"]


def extract_text_from_image(image_bytes: bytes, filename: str = "document.jpg") -> str:
    import base64 as b64
    from config import MISTRAL_API_KEY

    # Determine mime type
    mime_type = "image/jpeg"
    if filename.lower().endswith(".png"):
        mime_type = "image/png"
    elif filename.lower().endswith(".pdf"):
        mime_type = "application/pdf"

    image_b64 = b64.b64encode(image_bytes).decode("utf-8")

    try:
        if mime_type == "application/pdf":
            # PDF — upload as file first
            import requests as req
            upload_response = req.post(
                "https://api.mistral.ai/v1/files",
                headers={"Authorization": f"Bearer {MISTRAL_API_KEY}"},
                files={"file": (filename, image_bytes, "application/pdf")},
                data={"purpose": "ocr"}
            )
            if not upload_response.ok:
                raise Exception(f"Upload failed: {upload_response.text}")

            file_id = upload_response.json()["id"]

            # Get signed URL
            url_response = req.get(
                f"https://api.mistral.ai/v1/files/{file_id}/url",
                headers={"Authorization": f"Bearer {MISTRAL_API_KEY}"}
            )
            signed_url = url_response.json()["url"]

            # OCR via URL
            ocr_response = req.post(
                "https://api.mistral.ai/v1/ocr",
                headers={
                    "Authorization": f"Bearer {MISTRAL_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "mistral-ocr-latest",
                    "document": {"type": "document_url", "document_url": signed_url}
                }
            )
        else:
            # Image — send as base64
            import requests as req
            ocr_response = req.post(
                "https://api.mistral.ai/v1/ocr",
                headers={
                    "Authorization": f"Bearer {MISTRAL_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "mistral-ocr-latest",
                    "document": {
                        "type": "image_url",
                        "image_url": f"data:{mime_type};base64,{image_b64}"
                    }
                }
            )

        print("Mistral OCR status:", ocr_response.status_code)

        if not ocr_response.ok:
            print("Mistral OCR error:", ocr_response.text[:200])
            raise Exception(f"Mistral OCR failed: {ocr_response.status_code}")

        pages = ocr_response.json().get("pages", [])
        text = "\n\n".join(page.get("markdown", "") for page in pages).strip()

        if not text:
            raise Exception("No text extracted")

        print("Mistral OCR success, chars:", len(text))
        return text

    except Exception as e:
        print(f"Mistral OCR failed: {e} — falling back to Tesseract")
        return _tesseract_fallback(image_bytes)
    

def _tesseract_fallback(image_bytes: bytes) -> str:
    import pytesseract
    from PIL import Image
    import io
    from config import TESSERACT_CMD

    pytesseract.pytesseract.tesseract_cmd = TESSERACT_CMD

    image = Image.open(io.BytesIO(image_bytes))
    text = pytesseract.image_to_string(image, lang="eng+hin", config="--psm 6")
    if not text.strip():
        text = pytesseract.image_to_string(image, lang="eng", config="--psm 6")
    if not text.strip():
        raise Exception("Could not extract text. Please upload a clearer image.")
    return text.strip()

# ─── Language Detection ────────────────────────────────────────────────────

def detect_language(text: str) -> str:
    url = f"{SARVAM_BASE_URL}/text-language-identification"
    payload = {"input": text}
    response = requests.post(url, headers={**headers, "Content-Type": "application/json"}, json=payload)
    if not response.ok:
        return "en-IN"
    return response.json().get("language_code", "en-IN")