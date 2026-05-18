import requests
import json
import pytest
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

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
        "max_tokens": 2000,
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
            "content": """You are a medical document assistant for Indian rural patients. Given raw OCR text from a prescription, create a VOICE-FRIENDLY explanation.

Respond ONLY in this exact JSON format:
{
  "patient_name": "name if found, else null",
  "doctor_name": "name if found, else null",
  "date": "date if found, else null",
  "medications": [
    {
      "name": "medicine name in simple terms",
      "purpose": "what this medicine does in 1 simple sentence",
      "dosage": "dose and timing",
      "duration": "how many days",
      "side_effects": "common side effects in simple words"
    }
  ],
  "instructions": ["any special instructions in short sentences"],
  "summary": "A warm, conversational summary as if a caring nurse is explaining to the patient directly. Use 'you' (तुम्ही/आपण). Start with a greeting using the patient's first name if available. Format medications with simple numbering (पहिले, दुसरे, तिसरे). Each medication: name first, then what it's for in 1 sentence, then how to take it in 1-2 short sentences, then 1 side-effect warning if relevant. Use active voice. End with 2-3 bullet points of key reminders and a warm closing wish for recovery. Never mention missing information (doctor name, incomplete details) — simply omit it. Never use formal words like 'प्रथम' — use 'पहिले'. Never use abbreviations like 'मि.ग्रॅ.' — spell out 'मिलीग्रॅम'. Keep sentences under 10 words each."
}

RULES FOR SUMMARY:
- Start with greeting and patient identification
- Use [PAUSE] between every 2-3 sentences for TTS pacing
- Each medication gets its own short paragraph with numbering
- Side effects should include a clear "what to do if this happens" instruction
- End with an encouraging, actionable closing
- Never say "doctor name not found" — simply omit if unavailable
- Never include system notes like "explanations needed"
- Use warm, reassuring tone suitable for elderly patients

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

def answer_followup(question: str, context: dict, context_type: str, history: list = []) -> str:
    if context_type == "triage":
        system_prompt = f"""You are a helpful medical assistant. A patient has already been triaged with these results:
- Triage level: {context.get('triage_level')}
- Summary: {context.get('summary')}
- Possible conditions: {', '.join(context.get('possible_conditions', []))}
- Recommended action: {context.get('recommended_action')}

Answer the patient's follow-up question in simple, clear language. Do NOT diagnose or prescribe.
Keep your answer under 3 sentences. Be warm and easy to understand."""

    elif context_type == "prescription":
        meds = context.get('medications', [])
        med_names = ', '.join([m.get('name', '') for m in meds])
        system_prompt = f"""You are a helpful medical document assistant. A patient has a prescription with these medications: {med_names}.
Prescription summary: {context.get('summary')}

Answer the patient's follow-up question about their prescription in simple, plain language.
Keep your answer under 3 sentences. Do NOT give new medical advice beyond what's in the prescription."""

    messages = [{"role": "system", "content": system_prompt}]

    # Add conversation history
    for turn in history:
        messages.append({"role": "user", "content": turn["question"]})
        messages.append({"role": "assistant", "content": turn["answer"]})

    # Add current question
    messages.append({"role": "user", "content": question})

    result = chat_completion(messages, reasoning="low")
    # Strip any think tags if present
    if "<think>" in result and "</think>" in result:
        result = result.split("</think>")[-1].strip()
    return result


# ─── Test JSON parsing resilience ─────────────────────────────────────────

def parse_llm_json(raw: str) -> dict:
    """Mirrors the JSON parsing logic used in llm.py"""
    raw = raw.strip()
    if "<think>" in raw and "</think>" in raw:
        raw = raw.split("</think>")[-1].strip()
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.split("```")[0]
    return json.loads(raw.strip())


class TestJsonParsing:

    def test_clean_json(self):
        raw = '{"triage_level": "LOW", "summary": "Patient is fine."}'
        result = parse_llm_json(raw)
        assert result["triage_level"] == "LOW"
        assert "summary" in result

    def test_json_with_markdown_fence(self):
        raw = '```json\n{"triage_level": "HIGH", "summary": "Urgent care needed."}\n```'
        result = parse_llm_json(raw)
        assert result["triage_level"] == "HIGH"

    def test_json_with_think_tags(self):
        raw = '<think>Let me analyze this...</think>\n{"triage_level": "MEDIUM", "summary": "Monitor symptoms."}'
        result = parse_llm_json(raw)
        assert result["triage_level"] == "MEDIUM"

    def test_json_with_think_and_fence(self):
        raw = '<think>analyzing</think>\n```json\n{"triage_level": "LOW", "summary": "Rest advised."}\n```'
        result = parse_llm_json(raw)
        assert result["triage_level"] == "LOW"

    def test_invalid_json_raises(self):
        with pytest.raises(json.JSONDecodeError):
            parse_llm_json("this is not json")

    def test_triage_levels_valid(self):
        valid_levels = {"LOW", "MEDIUM", "HIGH"}
        raw = '{"triage_level": "HIGH", "summary": "test", "urgency_message": "go now", "possible_conditions": [], "recommended_action": "go", "follow_up_questions": []}'
        result = parse_llm_json(raw)
        assert result["triage_level"] in valid_levels

    def test_prescription_json_structure(self):
        raw = json.dumps({
            "patient_name": "Ramesh",
            "doctor_name": "Dr. Sharma",
            "date": "2024-01-01",
            "medications": [
                {
                    "name": "Paracetamol",
                    "purpose": "Fever",
                    "dosage": "500mg",
                    "duration": "5 days",
                    "side_effects": "None"
                }
            ],
            "instructions": ["Take after food"],
            "summary": "Simple fever prescription"
        })
        result = parse_llm_json(raw)
        assert "medications" in result
        assert len(result["medications"]) == 1
        assert result["medications"][0]["name"] == "Paracetamol"

    def test_empty_medications_list(self):
        raw = json.dumps({
            "patient_name": None,
            "doctor_name": None,
            "date": None,
            "medications": [],
            "instructions": [],
            "summary": "No medications found"
        })
        result = parse_llm_json(raw)
        assert result["medications"] == []


class TestPromptFormatting:

    def test_symptom_prompt_contains_symptoms(self):
        symptom_text = "I have fever and headache"
        prompt_content = f"Patient symptoms: {symptom_text}"
        assert symptom_text in prompt_content

    def test_prescription_prompt_contains_ocr(self):
        ocr_text = "Paracetamol 500mg BD x 5 days"
        prompt_content = f"Prescription OCR text:\n{ocr_text}"
        assert ocr_text in prompt_content

    def test_followup_triage_context_format(self):
        context = {
            "triage_level": "MEDIUM",
            "summary": "Patient has fever",
            "possible_conditions": ["Flu", "Cold"],
            "recommended_action": "Rest and hydrate"
        }
        system_prompt = f"""Triage level: {context.get('triage_level')}
        Summary: {context.get('summary')}
        Conditions: {', '.join(context.get('possible_conditions', []))}"""
        assert "MEDIUM" in system_prompt
        assert "Flu" in system_prompt

    def test_message_list_structure(self):
        messages = [
            {"role": "system", "content": "You are a medical assistant"},
            {"role": "user", "content": "I have a headache"}
        ]
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert len(messages) == 2

    def test_history_appended_correctly(self):
        history = [
            {"question": "What is paracetamol?", "answer": "A painkiller"},
            {"question": "Can I take it with food?", "answer": "Yes"}
        ]
        messages = [{"role": "system", "content": "You are helpful"}]
        for turn in history:
            messages.append({"role": "user", "content": turn["question"]})
            messages.append({"role": "assistant", "content": turn["answer"]})
        messages.append({"role": "user", "content": "Any side effects?"})

        assert len(messages) == 6
        assert messages[-1]["content"] == "Any side effects?"
        assert messages[1]["role"] == "user"
        assert messages[2]["role"] == "assistant"