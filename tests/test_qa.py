import pytest

from app.qa import QuestionError, answer, parse_question


@pytest.mark.parametrize(
    "question, months, pct",
    [
        ("What if net cash flow drops by 15% for the next 12 months?", 12, -15.0),
        ("Forecast with cash flow rising 5% for 9 months", 9, 5.0),
        ("cash balance for 6 months", 6, 0.0),
        ("scenario: cash flow falls 7.5% next 4 months", 4, -7.5),
    ],
)
def test_parses_months_and_change(question, months, pct):
    args = parse_question(question)
    assert args.months == months
    assert args.change_pct == pct


def test_default_horizon_is_12_months():
    assert parse_question("What is the cash balance?").months == 12


def test_expense_question_is_refused():
    with pytest.raises(QuestionError, match="net cash flow only"):
        parse_question("Cash forecast if expenses increase by 20% for 6 months?")


def test_direction_without_percentage_asks_for_it():
    with pytest.raises(QuestionError, match="percentage change"):
        parse_question("What is the cash balance if sales decline?")


def test_both_rise_and_drop_is_refused():
    with pytest.raises(QuestionError, match="both a rise and a drop"):
        parse_question("cash flow drops 5% but also rises 10% over 6 months")


def test_off_topic_question_is_refused():
    with pytest.raises(QuestionError):
        parse_question("Should we hire another engineer?")


def test_answer_numbers_come_from_the_tool_result():
    out = answer("What if net cash flow drops by 15% for the next 6 months?")
    assert out["tool_args"] == {"months": 6, "change_pct": -15.0}
    assert out["tool_result"]["ending_balance"] in out["answer"]
    assert out["tool_result"]["lowest_balance"] in out["answer"]
