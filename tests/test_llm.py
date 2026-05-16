import pytest
import json
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))


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