"""
Swasthya Setu — Evaluation Runner
Runs all eval components and generates a report.

Usage:
  Schema-only (no API calls, fast, used in CI):
    python eval/eval_runner.py --mode schema

  Full eval (makes real API calls, measures actual quality):
    python eval/eval_runner.py --mode full
"""

import sys
import os
import json
import argparse
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from colorama import Fore, Style, init
init(autoreset=True)

from eval_stt import run_stt_eval
from eval_translation import run_translation_eval
from eval_triage import run_triage_eval


def print_banner():
    print(f"""
{Fore.GREEN}╔══════════════════════════════════════════════════════════╗
║         SWASTHYA SETU — AI EVALUATION FRAMEWORK          ║
║         Measuring STT · Translation · Triage Quality     ║
╚══════════════════════════════════════════════════════════╝{Style.RESET_ALL}
""")


def run_full_eval():
    """Run full evaluation with real Sarvam API calls."""
    print(f"{Fore.YELLOW}Running FULL evaluation — making real API calls...{Style.RESET_ALL}")

    from services.sarvam import translate_text
    from services.llm import analyze_symptoms
    from sample_data import TRANSLATION_SAMPLES, TRIAGE_SAMPLES

    # Translation eval
    actual_translations = []
    print(f"\n{Fore.CYAN}Calling Sarvam translation API...{Style.RESET_ALL}")
    for sample in TRANSLATION_SAMPLES:
        try:
            translated = translate_text(
                sample["source"],
                sample["source_lang"],
                sample["target_lang"]
            )
            actual_translations.append({"id": sample["id"], "translated": translated})
            print(f"  ✓ {sample['id']}: {translated[:50]}...")
        except Exception as e:
            print(f"  ✗ {sample['id']}: {e}")
            actual_translations.append({"id": sample["id"], "translated": ""})

    # Triage eval
    actual_triage = []
    print(f"\n{Fore.CYAN}Calling sarvam-m triage LLM...{Style.RESET_ALL}")
    for sample in TRIAGE_SAMPLES:
        try:
            result = analyze_symptoms(sample["symptoms"])
            actual_triage.append({"id": sample["id"], "triage_result": result})
            print(f"  ✓ {sample['id']}: {result.get('triage_level')} — {result.get('summary', '')[:50]}...")
        except Exception as e:
            print(f"  ✗ {sample['id']}: {e}")

    return actual_translations, actual_triage


def save_report(all_results: list, mode: str):
    """Save evaluation report as JSON."""
    os.makedirs("eval/reports", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = f"eval/reports/eval_{mode}_{timestamp}.json"

    report = {
        "timestamp": timestamp,
        "mode": mode,
        "components": all_results,
        "overall_score": round(
            sum(r["score"] for r in all_results) / len(all_results), 2
        ) if all_results else 0
    }

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n  Report saved: {report_path}")
    return report


def print_summary(all_results: list, mode: str):
    print(f"\n{Fore.CYAN}{'='*60}")
    print("  EVALUATION SUMMARY")
    print(f"{'='*60}{Style.RESET_ALL}")
    print(f"  Mode: {mode.upper()}")
    print(f"  Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    total_passed = 0
    total_tests = 0

    for r in all_results:
        icon = "✅" if r["passed"] == r["total"] else "⚠️ "
        print(f"  {icon} {r['component']:15} {r['passed']}/{r['total']} passed  (score: {r['score']:.0%})")
        total_passed += r["passed"]
        total_tests += r["total"]

    overall = round(total_passed / total_tests, 2) if total_tests > 0 else 0
    color = Fore.GREEN if overall >= 0.8 else Fore.YELLOW if overall >= 0.6 else Fore.RED
    print(f"\n  {color}Overall: {total_passed}/{total_tests} ({overall:.0%}){Style.RESET_ALL}")

    if overall >= 0.8:
        print(f"  {Fore.GREEN}🎉 Evaluation PASSED{Style.RESET_ALL}")
    else:
        print(f"  {Fore.RED}❌ Evaluation needs improvement{Style.RESET_ALL}")

    return overall >= 0.8


def main():
    parser = argparse.ArgumentParser(description="Swasthya Setu Eval Framework")
    parser.add_argument("--mode", choices=["schema", "full"], default="schema",
                        help="schema = no API calls (CI mode), full = real API calls")
    parser.add_argument("--save", action="store_true", help="Save report to JSON")
    args = parser.parse_args()

    print_banner()

    if args.mode == "schema":
        print(f"{Fore.YELLOW}Running SCHEMA-ONLY eval (no API calls) — CI mode{Style.RESET_ALL}")
        stt_results = run_stt_eval(actual_transcripts=None)
        trans_results = run_translation_eval(actual_translations=None)
        triage_results = run_triage_eval(actual_results=None)
    else:
        actual_translations, actual_triage = run_full_eval()
        stt_results = run_stt_eval(actual_transcripts=None)  # STT needs audio files
        trans_results = run_translation_eval(actual_translations=actual_translations)
        triage_results = run_triage_eval(actual_results=actual_triage)

    all_results = [stt_results, trans_results, triage_results]

    if args.save:
        save_report(all_results, args.mode)

    passed = print_summary(all_results, args.mode)
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()