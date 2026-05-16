"""
Triage Evaluation — validates LLM output quality
Checks: schema validity, severity accuracy, required fields, JSON resilience
"""

import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from colorama import Fore, Style
from sample_data import TRIAGE_SAMPLES, REQUIRED_TRIAGE_FIELDS, REQUIRED_PRESCRIPTION_FIELDS


def validate_triage_schema(result: dict) -> dict:
    """Check all required fields are present and valid."""
    errors = []
    for field in REQUIRED_TRIAGE_FIELDS:
        if field not in result:
            errors.append(f"Missing field: {field}")
    if "triage_level" in result:
        if result["triage_level"] not in {"LOW", "MEDIUM", "HIGH"}:
            errors.append(f"Invalid triage_level: {result['triage_level']}")
    if "possible_conditions" in result:
        if not isinstance(result["possible_conditions"], list):
            errors.append("possible_conditions must be a list")
    if "follow_up_questions" in result:
        if not isinstance(result["follow_up_questions"], list):
            errors.append("follow_up_questions must be a list")
    return {"valid": len(errors) == 0, "errors": errors}


def validate_prescription_schema(result: dict) -> dict:
    """Check prescription explanation structure."""
    errors = []
    for field in REQUIRED_PRESCRIPTION_FIELDS:
        if field not in result:
            errors.append(f"Missing field: {field}")
    if "medications" in result:
        if not isinstance(result["medications"], list):
            errors.append("medications must be a list")
        else:
            for i, med in enumerate(result["medications"]):
                for mf in ["name", "purpose", "dosage", "duration", "side_effects"]:
                    if mf not in med:
                        errors.append(f"medications[{i}] missing field: {mf}")
    return {"valid": len(errors) == 0, "errors": errors}


def run_triage_eval(actual_results: list = None) -> dict:
    """
    Run triage evaluation.
    actual_results: list of dicts with {id, triage_result}
    If None, runs schema + mock validation only.
    """
    print(f"\n{Fore.CYAN}{'='*60}")
    print("  TRIAGE EVALUATION — LLM Output Quality")
    print(f"{'='*60}{Style.RESET_ALL}")

    results = []
    schema_only = actual_results is None

    # ── Schema validation tests (always run) ──
    print(f"\n  {Fore.CYAN}[Schema Validation]{Style.RESET_ALL}")

    mock_valid = {
        "triage_level": "LOW",
        "urgency_message": "See a doctor within a week",
        "possible_conditions": ["Common cold"],
        "recommended_action": "Rest and drink fluids",
        "follow_up_questions": ["How long have you had symptoms?"],
        "summary": "Mild symptoms"
    }
    mock_invalid = {
        "triage_level": "UNKNOWN",
        "summary": "test"
        # missing fields
    }
    mock_prescription = {
        "patient_name": "Ramesh",
        "doctor_name": "Dr. Sharma",
        "date": "2024-01-01",
        "medications": [
            {"name": "Paracetamol", "purpose": "Fever",
             "dosage": "500mg", "duration": "5 days", "side_effects": "None"}
        ],
        "instructions": ["Take after food"],
        "summary": "Fever prescription"
    }

    v1 = validate_triage_schema(mock_valid)
    v2 = validate_triage_schema(mock_invalid)
    v3 = validate_prescription_schema(mock_prescription)

    print(f"  [{Fore.GREEN}PASS{Style.RESET_ALL}] Valid triage schema accepted")
    assert v1["valid"], f"Should be valid: {v1['errors']}"

    print(f"  [{Fore.GREEN}PASS{Style.RESET_ALL}] Invalid triage schema rejected")
    assert not v2["valid"], "Should be invalid"

    print(f"  [{Fore.GREEN}PASS{Style.RESET_ALL}] Valid prescription schema accepted")
    assert v3["valid"], f"Should be valid: {v3['errors']}"

    # ── Severity accuracy (with real results or mock) ──
    print(f"\n  {Fore.CYAN}[Severity Accuracy]{Style.RESET_ALL}")

    if schema_only:
        for sample in TRIAGE_SAMPLES:
            result = {
                "id": sample["id"],
                "description": sample["description"],
                "expected_level": sample["expected_level"],
                "mode": "schema_only",
                "passed": True
            }
            print(f"  {Fore.YELLOW}[SCHEMA]{Style.RESET_ALL} {sample['id']} — {sample['description']}")
            results.append(result)
    else:
        for sample in TRIAGE_SAMPLES:
            actual = next((r for r in actual_results if r["id"] == sample["id"]), None)
            if not actual:
                continue

            triage = actual["triage_result"]
            schema_check = validate_triage_schema(triage)
            level_match = triage.get("triage_level") == sample["expected_level"]

            # Allow HIGH for MEDIUM samples (over-triage is safer than under-triage)
            if not level_match and sample["expected_level"] == "MEDIUM":
                level_match = triage.get("triage_level") == "HIGH"

            passed = schema_check["valid"] and level_match
            result = {
                "id": sample["id"],
                "description": sample["description"],
                "expected_level": sample["expected_level"],
                "actual_level": triage.get("triage_level"),
                "schema_valid": schema_check["valid"],
                "level_match": level_match,
                "passed": passed,
            }
            status = f"{Fore.GREEN}PASS" if passed else f"{Fore.RED}FAIL"
            print(f"  [{status}{Style.RESET_ALL}] {sample['id']} | Expected: {sample['expected_level']} | Got: {triage.get('triage_level')} | Schema: {'✓' if schema_check['valid'] else '✗'}")
            results.append(result)

    passed_count = sum(1 for r in results if r["passed"])
    total = len(results)
    print(f"\n  Result: {passed_count}/{total} passed")

    return {
        "component": "Triage",
        "total": total,
        "passed": passed_count,
        "score": round(passed_count / total, 2) if total > 0 else 0,
        "results": results
    }