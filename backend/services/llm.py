import requests
import json
from config import SARVAM_API_KEY, SARVAM_BASE_URL

headers = {
    "Authorization": f"Bearer {SARVAM_API_KEY}",
    "Content-Type": "application/json"
}


def chat_completion(messages: list, reasoning: str = "low") -> str:
    url = f"{SARVAM_BASE_URL}/v1/chat/completions"
    payload = {
        "model": "sarvam-m",
        "messages": messages,
        "max_tokens": 1000,
        "reasoning_effort": reasoning
    }
    response = requests.post(url, headers=headers, json=payload)

    if not response.ok:
        raise Exception(f"LLM Error {response.status_code}: {response.text}")

    content = response.json()["choices"][0]["message"]["content"]

    # Strip <think>...</think> block if present
    if "<think>" in content and "</think>" in content:
        content = content.split("</think>")[-1].strip()

    return content


# ─── Symptom Triage ────────────────────────────────────────────────────────

def analyze_symptoms(symptom_text: str) -> dict:
    messages = [
        {
            "role": "system",
            "content": """You are a medical triage assistant. Analyze patient symptoms and respond ONLY in this exact JSON format:
{
  "triage_level": "LOW" or "MEDIUM" or "HIGH",
  "urgency_message": "one sentence on when to see a doctor",
  "possible_conditions": ["condition1", "condition2"],
  "recommended_action": "what the patient should do next",
  "follow_up_questions": ["question1", "question2"],
  "summary": "8 to 10 sentence plain language summary of the situation"
}
Do not diagnose. Do not prescribe. Only triage and guide.
IMPORTANT: Respond only with the JSON object, no extra text."""
        },
        {
            "role": "user",
            "content": f"Patient symptoms: {symptom_text}"
        }
    ]
    import json
    # Clean and parse JSON
    raw = chat_completion(messages, reasoning="medium").strip()
    # Remove markdown code fences if present
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.split("```")[0]
    return json.loads(raw.strip())


# ─── Prescription Explanation ──────────────────────────────────────────────

def explain_prescription(ocr_text: str) -> dict:
    messages = [
        {
            "role": "system",
            "content": """You are a medical document assistant. Given raw OCR text from a prescription or discharge summary, extract and explain it in simple terms. Respond ONLY in this exact JSON format:
{
  "patient_name": "name if found, else null",
  "doctor_name": "name if found, else null",
  "date": "date if found, else null",
  "medications": [
    {
      "name": "medicine name",
      "purpose": "what this medicine is for in simple terms",
      "dosage": "dose and timing",
      "duration": "how many days",
      "side_effects": "common side effects to watch for"
    }
  ],
  "instructions": ["any special instructions"],
  "summary": "8 to 10 sentence plain language overview of this prescription"
}
IMPORTANT: Respond only with the JSON object, no extra text."""
        },
        {
            "role": "user",
            "content": f"Prescription OCR text:\n{ocr_text}"
        }
    ]
    import json
    # Clean and parse JSON
    raw = chat_completion(messages, reasoning="medium").strip()
    # Remove markdown code fences if present
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.split("```")[0]
    return json.loads(raw.strip())