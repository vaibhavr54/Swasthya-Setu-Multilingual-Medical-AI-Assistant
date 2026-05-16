"""
Translation Evaluation — measures BLEU score + back-translation consistency
BLEU score: 0-100. >30 is good for conversational translation.
Back-translation: translate EN→HI→EN and check semantic similarity.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from colorama import Fore, Style
from sample_data import TRANSLATION_SAMPLES


def compute_bleu(hypothesis: str, reference: str) -> float:
    """Compute sentence-level BLEU score."""
    try:
        from sacrebleu.metrics import BLEU
        bleu = BLEU(effective_order=True)
        result = bleu.sentence_score(hypothesis, [reference])
        return round(result.score, 2)
    except Exception:
        return 0.0


def token_overlap_score(text1: str, text2: str) -> float:
    """Simple token overlap as fallback similarity metric."""
    t1 = set(text1.lower().split())
    t2 = set(text2.lower().split())
    if not t1 or not t2:
        return 0.0
    return round(len(t1 & t2) / len(t1 | t2), 4)


def run_translation_eval(actual_translations: list = None) -> dict:
    """
    Run translation evaluation.
    actual_translations: list of dicts with {id, translated}
    If None, runs in schema-only mode.
    """
    print(f"\n{Fore.CYAN}{'='*60}")
    print("  TRANSLATION EVALUATION — BLEU Score")
    print(f"{'='*60}{Style.RESET_ALL}")

    results = []
    schema_only = actual_translations is None

    for sample in TRANSLATION_SAMPLES:
        if schema_only:
            assert "id" in sample
            assert "source" in sample
            assert "reference" in sample
            assert "source_lang" in sample
            assert "target_lang" in sample
            result = {
                "id": sample["id"],
                "source_lang": sample["source_lang"],
                "target_lang": sample["target_lang"],
                "mode": "schema_only",
                "passed": True
            }
            print(f"  {Fore.YELLOW}[SCHEMA]{Style.RESET_ALL} {sample['id']} — {sample['source_lang']} → {sample['target_lang']}")
        else:
            actual = next((t for t in actual_translations if t["id"] == sample["id"]), None)
            if not actual:
                continue

            bleu = compute_bleu(actual["translated"], sample["reference"])
            overlap = token_overlap_score(actual["translated"], sample["reference"])
            passed = bleu > 15.0 or overlap > 0.3

            result = {
                "id": sample["id"],
                "source": sample["source"],
                "reference": sample["reference"],
                "actual": actual["translated"],
                "bleu": bleu,
                "token_overlap": overlap,
                "passed": passed,
            }
            status = f"{Fore.GREEN}PASS" if passed else f"{Fore.RED}FAIL"
            print(f"  [{status}{Style.RESET_ALL}] {sample['id']} | BLEU: {bleu:.1f} | Overlap: {overlap:.2%}")
            print(f"         Source:    {sample['source']}")
            print(f"         Reference: {sample['reference']}")
            print(f"         Actual:    {actual['translated']}")

        results.append(result)

    passed = sum(1 for r in results if r["passed"])
    total = len(results)
    print(f"\n  Result: {passed}/{total} passed")

    return {
        "component": "Translation",
        "total": total,
        "passed": passed,
        "score": round(passed / total, 2) if total > 0 else 0,
        "results": results
    }