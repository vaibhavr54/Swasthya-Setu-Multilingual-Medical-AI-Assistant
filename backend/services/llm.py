import requests
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

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
  "summary": "8 to 10 sentence plain language summary of the situation written for a patient with no medical education"
}
Do not diagnose. Do not prescribe. Only triage and guide.
IMPORTANT: Respond only with the JSON object, no extra text."""
        },
        {
            "role": "user",
            "content": f"Patient symptoms: {symptom_text}"
        }
    ]

    raw = chat_completion(messages, reasoning="medium").strip()
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
            "content": """You are a medical document parser. Extract information from prescription text and return ONLY a JSON object.
CRITICAL RULES:
1. ALL text values in the JSON must be in ENGLISH only
2. Never use Marathi, Hindi or any other language in your response
3. Respond with ONLY the JSON object, no other text

Return this exact JSON structure:
{
  "patient_name": null,
  "doctor_name": null,
  "date": null,
  "medications": [{"name": "english name", "purpose": "english purpose", "dosage": "english dosage", "duration": "english duration", "side_effects": "english side effects"}],
  "instructions": ["english instruction"],
  "summary": "5 to 8 simple sentences explaining: what medicines are given and why each one is needed, when and how to take each medicine, how many days to continue, any important warnings or side effects to watch for, and what the patient should do if they feel unwell — written in very simple English as if explaining to someone with no medical education"
}"""
        },
        {
            "role": "user",
            "content": "Prescription: Paracetamol 500mg twice daily for 5 days, Cetirizine 10mg once daily at night for 3 days. Patient: Ramesh. Doctor: Dr. Sharma. Instructions: Take after food."
        },
        {
            "role": "assistant",
            "content": '{"patient_name": "Ramesh", "doctor_name": "Dr. Sharma", "date": null, "medications": [{"name": "Paracetamol 500mg", "purpose": "To reduce fever and relieve body pain", "dosage": "500mg twice daily — once in morning, once at night", "duration": "5 days", "side_effects": "Generally safe, but avoid taking more than prescribed. Do not take on empty stomach."}, {"name": "Cetirizine 10mg", "purpose": "To reduce allergy symptoms like runny nose, sneezing and itching", "dosage": "10mg once daily at night before sleeping", "duration": "3 days", "side_effects": "May cause drowsiness. Avoid driving after taking this medicine."}], "instructions": ["Take all medicines after food"], "summary": "Doctor Sharma has given Ramesh two medicines. The first medicine Paracetamol is for fever and body pain — take 1 tablet in the morning and 1 tablet at night for 5 days. The second medicine Cetirizine is for allergy symptoms like sneezing and runny nose — take 1 tablet at night before sleeping for 3 days. Always take both medicines after eating food, never on an empty stomach. Cetirizine may make you feel sleepy so do not drive or operate machines after taking it. Complete the full course of medicines even if you feel better before finishing. Drink plenty of water and rest properly during this time. If your symptoms get worse or you feel any unusual side effects, stop the medicines and visit your doctor immediately."}'
        },
        {
            "role": "user",
            "content": f"Prescription text to parse (respond in ENGLISH JSON only):\n{ocr_text}"
        }
    ]

    raw = chat_completion(messages, reasoning="medium").strip()
    if "<think>" in raw and "</think>" in raw:
        raw = raw.split("</think>")[-1].strip()
    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
        raw = raw.split("```")[0]
    return json.loads(raw.strip())


# ─── Follow-up Answer ──────────────────────────────────────────────────────

def answer_followup(question: str, context: dict, context_type: str, history: list = []) -> str:
    if context_type == "triage":
        system_prompt = f"""You are a helpful medical assistant. A patient has already been triaged with these results:
- Triage level: {context.get('triage_level')}
- Summary: {context.get('summary')}
- Possible conditions: {', '.join(context.get('possible_conditions', []))}
- Recommended action: {context.get('recommended_action')}

Answer the patient's follow-up question in simple, clear English. Do NOT diagnose or prescribe.
Give a helpful answer in 5 to 8 sentences. Be warm, clear and easy to understand for someone with no medical education."""

    elif context_type == "prescription":
        meds = context.get('medications', [])
        med_names = ', '.join([m.get('name', '') for m in meds])
        system_prompt = f"""You are a helpful medical document assistant. A patient has a prescription with these medications: {med_names}.
Prescription summary: {context.get('summary')}

Answer the patient's follow-up question about their prescription in simple, plain English.
Give a helpful answer in 5 to 8 sentences. Do NOT give new medical advice beyond what is in the prescription.
Write as if explaining to someone with no medical education."""

    messages = [{"role": "system", "content": system_prompt}]

    for turn in history:
        messages.append({"role": "user", "content": turn["question"]})
        messages.append({"role": "assistant", "content": turn["answer"]})

    messages.append({"role": "user", "content": question})

    result = chat_completion(messages, reasoning="low")
    if "<think>" in result and "</think>" in result:
        result = result.split("</think>")[-1].strip()
    return result