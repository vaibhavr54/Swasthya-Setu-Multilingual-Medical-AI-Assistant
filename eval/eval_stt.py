"""
STT Evaluation — measures Word Error Rate (WER) of Sarvam Saaras STT
WER = (Substitutions + Deletions + Insertions) / Total Reference Words
Lower is better. < 0.15 is good, < 0.05 is excellent.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from jiwer import wer, cer
from colorama import Fore, Style
from sample_data import STT_SAMPLES


def normalize_text(text: str) -> str:
    return text.lower().strip()


def evaluate_stt_text(hypothesis: str, reference: str) -> dict:
    """Evaluate a single STT result against reference transcript."""
    h = normalize_text(hypothesis)
    r = normalize_text(reference)
    word_error_rate = wer(r, h)
    char_error_rate = cer(r, h)
    return {
        "wer": round(word_error_rate, 4),
        "cer": round(char_error_rate, 4),
        "passed": word_error_rate < 0.30,  # 30% WER threshold
    }


def run_stt_eval(actual_transcripts: list = None) -> dict:
    """
    Run STT evaluation.
    actual_transcripts: list of dicts with {id, transcript}
    If None, runs in schema-only mode (no real API calls).
    """
    print(f"\n{Fore.CYAN}{'='*60}")
    print("  STT EVALUATION — Word Error Rate (WER)")
    print(f"{'='*60}{Style.RESET_ALL}")

    results = []
    schema_only = actual_transcripts is None

    for sample in STT_SAMPLES:
        if schema_only:
            # Schema validation only — check sample structure
            assert "id" in sample
            assert "language" in sample
            assert "expected_transcript" in sample
            result = {
                "id": sample["id"],
                "language": sample["language"],
                "description": sample["description"],
                "mode": "schema_only",
                "passed": True
            }
            print(f"  {Fore.YELLOW}[SCHEMA]{Style.RESET_ALL} {sample['id']} — {sample['description']}")
        else:
            actual = next((t for t in actual_transcripts if t["id"] == sample["id"]), None)
            if not actual:
                continue
            metrics = evaluate_stt_text(actual["transcript"], sample["expected_transcript"])
            result = {
                "id": sample["id"],
                "language": sample["language"],
                "description": sample["description"],
                "expected": sample["expected_transcript"],
                "actual": actual["transcript"],
                "wer": metrics["wer"],
                "cer": metrics["cer"],
                "passed": metrics["passed"],
            }
            status = f"{Fore.GREEN}PASS" if metrics["passed"] else f"{Fore.RED}FAIL"
            print(f"  [{status}{Style.RESET_ALL}] {sample['id']} | WER: {metrics['wer']:.2%} | CER: {metrics['cer']:.2%}")
            print(f"         Expected: {sample['expected_transcript'][:60]}...")
            print(f"         Actual:   {actual['transcript'][:60]}...")

        results.append(result)

    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    print(f"\n  Result: {passed}/{total} passed")

    return {
        "component": "STT",
        "total": total,
        "passed": passed,
        "score": round(passed / total, 2) if total > 0 else 0,
        "results": results
    }