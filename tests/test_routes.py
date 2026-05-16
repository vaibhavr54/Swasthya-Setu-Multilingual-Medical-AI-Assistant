import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock


# ─── Mock all external API calls ──────────────────────────────────────────

MOCK_TRIAGE = {
    "triage_level": "LOW",
    "urgency_message": "See a doctor within a week",
    "possible_conditions": ["Common cold"],
    "recommended_action": "Rest and drink fluids",
    "follow_up_questions": ["How long have you had symptoms?"],
    "summary": "Patient has mild cold symptoms"
}

MOCK_PRESCRIPTION = {
    "patient_name": "Ramesh",
    "doctor_name": "Dr. Sharma",
    "date": "2024-01-01",
    "medications": [{"name": "Paracetamol", "purpose": "Fever", "dosage": "500mg BD", "duration": "5 days", "side_effects": "None"}],
    "instructions": ["Take after food"],
    "summary": "Simple fever prescription"
}


@pytest.fixture
def client():
    with patch.dict(os.environ, {
        "SARVAM_API_KEY": "test_key",
        "MISTRAL_API_KEY": "test_key",
        "SARVAM_BASE_URL": "https://api.sarvam.ai"
    }):
        from main import app
        return TestClient(app)


class TestHealthEndpoint:

    def test_health_returns_ok(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"
        assert response.json()["app"] == "Swasthya Setu"


class TestVoiceRoutes:

    def test_triage_missing_audio_returns_422(self, client):
        response = client.post("/api/voice/triage", data={"language_code": "hi-IN"})
        assert response.status_code == 422

    def test_speak_missing_text_returns_422(self, client):
        response = client.post("/api/voice/speak", data={"language_code": "hi-IN"})
        assert response.status_code == 422

    def test_triage_with_mock(self, client):
        with patch("routes.voice.speech_to_text") as mock_stt, \
             patch("routes.voice.analyze_symptoms") as mock_llm, \
             patch("routes.voice.translate_text") as mock_translate:

            mock_stt.return_value = {"transcript": "I have fever", "language_code": "en-IN"}
            mock_llm.return_value = MOCK_TRIAGE
            mock_translate.return_value = "translated text"

            audio_bytes = b"RIFF" + b"\x00" * 100
            response = client.post(
                "/api/voice/triage",
                files={"audio": ("test.wav", audio_bytes, "audio/wav")},
                data={"language_code": "en-IN"}
            )
            assert response.status_code == 200
            data = response.json()
            assert "triage" in data
            assert "transcript" in data
            assert data["triage"]["triage_level"] == "LOW"

    def test_speak_with_mock(self, client):
        with patch("routes.voice.text_to_speech") as mock_tts:
            mock_tts.return_value = b"RIFF" + b"\x00" * 200
            response = client.post(
                "/api/voice/speak",
                data={"text": "Hello", "language_code": "hi-IN", "speaker": "auto"}
            )
            assert response.status_code == 200
            assert response.headers["content-type"] == "audio/wav"


class TestDocumentRoutes:

    def test_analyze_missing_file_returns_422(self, client):
        response = client.post("/api/document/analyze", data={"target_language": "hi-IN"})
        assert response.status_code == 422

    def test_analyze_with_mock(self, client):
        with patch("routes.document.extract_text_from_image") as mock_ocr, \
             patch("routes.document.explain_prescription") as mock_llm, \
             patch("routes.document.translate_text") as mock_translate:

            mock_ocr.return_value = "Paracetamol 500mg BD x 5 days"
            mock_llm.return_value = MOCK_PRESCRIPTION
            mock_translate.return_value = "translated"

            image_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * 100  # fake JPEG header
            response = client.post(
                "/api/document/analyze",
                files={"file": ("prescription.jpg", image_bytes, "image/jpeg")},
                data={"target_language": "en-IN"}
            )
            assert response.status_code == 200
            data = response.json()
            assert "explanation" in data
            assert "ocr_text" in data

    def test_followup_missing_context_returns_422(self, client):
        response = client.post(
            "/api/document/followup",
            data={"question": "What is this medicine for?", "language_code": "en-IN"}
        )
        assert response.status_code == 422