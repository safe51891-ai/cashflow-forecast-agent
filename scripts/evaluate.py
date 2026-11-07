"""Check how questions are turned into forecast-tool calls, and that unanswerable ones are refused.

Usage: python scripts/evaluate.py
A case passes when:
  - expect is a dict: the question parses to the same months and change_pct, and the answer is produced.
  - expect is "refuse": the question is refused and no forecast number is produced.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.qa import QuestionError, answer  # noqa: E402


def run(question: str, expect) -> tuple[bool, str]:
    try:
        result = answer(question)
    except QuestionError as exc:
        return expect == "refuse", f"refused: {exc}"
    if expect == "refuse":
        return False, f"answered but should refuse: {result['answer']}"
    got = result["tool_args"]
    ok = got["months"] == expect["months"] and abs(got["change_pct"] - expect["change_pct"]) < 1e-9
    return ok, result["answer"]


def main() -> int:
    cases = json.loads((ROOT / "data" / "synthetic_questions.json").read_text())
    correct = 0
    print(f"{'id':6} {'expected':34} result  detail")
    for case in cases:
        expect = case["expect"]
        label = "refuse" if expect == "refuse" else f"{expect['months']}m, {expect['change_pct']:+g}%"
        ok, detail = run(case["question"], expect)
        correct += ok
        print(f"{case['id']:6} {label:34} {'PASS' if ok else 'FAIL':6} {detail[:120]}")
    print(f"\nAccuracy: {correct}/{len(cases)} = {correct / len(cases):.0%}")
    return 0 if correct == len(cases) else 1


if __name__ == "__main__":
    raise SystemExit(main())
