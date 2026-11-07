"""Answer treasury scenario questions by calling the forecast tool. Never by guessing numbers.

The question is turned into tool arguments with rules (months, percentage change).
If a question cannot be mapped to those arguments, the app says so instead of answering.
An LLM can be added later to parse questions, but it must still call cash_scenario for numbers.
"""
import re
from dataclasses import dataclass

from .forecast import cash_scenario

DEFAULT_MONTHS = 12
CASH_WORDS = re.compile(r"\b(cash|balance|forecast|scenario|runway|treasury|net flow|cash flow)\b", re.I)
MONTHS_RE = re.compile(r"\b(\d{1,2})\s*months?\b", re.I)
DECREASE_RE = re.compile(r"\b(drop|drops|dropping|fall|falls|falling|decline|declines|declining|decrease|decreases|decreasing|reduce|reduces|reducing|cut|cuts|cutting|lower|lowers|lowering)\b(?:\s+\w+){0,2}?\s+by\s+(\d+(?:\.\d+)?)\s*%|\b(drop|drops|dropping|fall|falls|falling|decline|declines|declining|decrease|decreases|decreasing|reduce|reduces|reducing|cut|cuts|cutting|lower|lowers|lowering)\b(?:\s+\w+){0,2}?\s+(\d+(?:\.\d+)?)\s*%", re.I)
INCREASE_RE = re.compile(r"\b(rise|rises|rising|increase|increases|increasing|grow|grows|growing|up|higher)\b(?:\s+\w+){0,2}?\s+by\s+(\d+(?:\.\d+)?)\s*%|\b(rise|rises|rising|increase|increases|increasing|grow|grows|growing|up|higher)\b(?:\s+\w+){0,2}?\s+(\d+(?:\.\d+)?)\s*%", re.I)


DIRECTION_WORDS = re.compile(
    r"\b(drop|drops|dropping|fall|falls|falling|decline|declines|declining|decrease|decreases|decreasing|reduce|reduces|reducing|cut|cuts|cutting|lower|lowers|lowering|"
    r"rise|rises|rising|increase|increases|increasing|grow|grows|growing|higher)\b",
    re.I,
)


EXPENSE_RE = re.compile(r"\b(expense|expenses|cost|costs|payroll|spend|spending|salaries|salary)\b", re.I)


class QuestionError(ValueError):
    """The question is outside what the forecast tool can answer."""


@dataclass(frozen=True)
class ScenarioArgs:
    months: int
    change_pct: float


def parse_question(question: str) -> ScenarioArgs:
    if not CASH_WORDS.search(question):
        raise QuestionError("I can only answer cash, balance and forecast scenario questions.")

    months_match = MONTHS_RE.search(question)
    months = int(months_match.group(1)) if months_match else DEFAULT_MONTHS
    if not 1 <= months <= 36:
        raise QuestionError("the forecast covers 1 to 36 months")

    if EXPENSE_RE.search(question):
        raise QuestionError(
            "the forecast models net cash flow only; expense or cost scenarios need a separate model"
        )

    decrease = DECREASE_RE.search(question)
    increase = INCREASE_RE.search(question)
    if decrease and increase:
        raise QuestionError("the question describes both a rise and a drop; ask one scenario at a time")
    if decrease:
        pct = float(decrease.group(2) or decrease.group(4))
        return ScenarioArgs(months=months, change_pct=-pct)
    if increase:
        pct = float(increase.group(2) or increase.group(4))
        return ScenarioArgs(months=months, change_pct=pct)
    if DIRECTION_WORDS.search(question):
        raise QuestionError("I need the percentage change, for example 'drop by 15%'")
    return ScenarioArgs(months=months, change_pct=0.0)


def answer(question: str) -> dict:
    """Return {'answer': text, 'tool_args': {...}, 'tool_result': {...}}."""
    args = parse_question(question)
    result = cash_scenario(months=args.months, change_pct=args.change_pct)
    scenario = "baseline" if args.change_pct == 0 else f"net cash flow {args.change_pct:+g}%"
    text = (
        f"{args.months}-month {scenario}: ending balance {result['ending_balance']}, "
        f"lowest balance {result['lowest_balance']} in {result['lowest_month']} "
        f"(opening {result['opening_balance']})."
    )
    return {"answer": text, "tool_args": {"months": args.months, "change_pct": args.change_pct}, "tool_result": result}
