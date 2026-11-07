# Cash Flow Forecast and Treasury Q&A

A statsmodels forecast of monthly net cash flow, and a question handler that answers scenario questions ("what if net cash flow drops 15% for 12 months?") by calling the forecast tool. It never guesses a number.

The point of the project is the split: the forecast produces the numbers, the handler only decides which scenario to run, and anything it cannot map to the tool is refused.

## How it works

1. **Baseline forecast.** Holt-Winters exponential smoothing from statsmodels, with an additive trend and a 12-month seasonal cycle, fitted to 36 months of net cash flow.
2. **Scenario tool: `cash_scenario(months, change_pct, opening_balance)`.** Applies the percentage change to every forecast month's net cash flow, then returns the ending balance, the lowest balance, the month it occurs, and the monthly flows.
3. **Question handler (`app/qa.py`).** Rules turn the question into `months` and `change_pct`:
   - no horizon given: 12 months
   - "drop/fall/decline/cut ... N%" becomes a negative change, "rise/grow/increase ... N%" a positive one
   - expense, cost or payroll scenarios are refused, because the model only covers net cash flow
   - a drop or rise with no percentage is refused, and the user is asked for one
   - both a rise and a drop in one question is refused
   - anything outside cash and balance topics is refused
4. **Answer.** The text is built from the tool's output. The model's numbers are never used.

## Input

- `data/synthetic_cashflow.csv`: 36 months of invented net cash flow with trend and seasonality, made by `scripts/make_synthetic_data.py` (fixed seed).
- The opening balance defaults to 250,000.00. It can be changed in code.

Example:

```
Q: What if net cash flow drops by 15% for the next 6 months?
A: 6-month net cash flow -15%: ending balance 826223.35, lowest balance 320173.68 in 2026-01 (opening 250000.00).
```

(Output of one run on the synthetic data. Not real finances.)

## Run it

```bash
python3.13 -m venv .venv && source .venv/bin/activate   # Python 3.10+
pip install -r requirements.txt
python -m pytest -q          # 17 tests
python scripts/evaluate.py   # 10 synthetic questions
```

## Evaluation

`data/synthetic_questions.json` has 10 questions with expected results. A case passes when:

- For answerable questions: the handler maps the question to the expected `months` and `change_pct`, and produces an answer.
- For unanswerable questions: the handler refuses, and produces no forecast number.

| Cases | Expected |
|---|---|
| CQ-01 to 04, 06, 07: baseline, drops, rises, 3 to 24 months | answered with the right arguments |
| CQ-05: expense increase | refused (net flow only) |
| CQ-08: "sales decline" with no percentage | refused, asks for the percentage |
| CQ-09: off-topic (hiring) | refused |
| CQ-10: 40 months, beyond the 36-month forecast range | refused |

**Result:** 10 of 10 (100%), plus 17 passing unit tests.

The evaluation checks the question-to-tool mapping, not forecast accuracy. The forecast's error on this data has not been measured against held-out months; that is the next thing to add.

## Limits and what is not built yet

- **No LLM agent yet.** The handler uses rules. A tool-calling model could replace the parser later, but it must still call `cash_scenario` for numbers.
- **No Streamlit UI yet.** The project runs from Python and tests only.
- **Forecast accuracy not measured.** No holdout split or error metric yet.
- **Scenarios are simple.** A percentage change on total net flow. Collections, payroll and capex are not modelled separately, so "collections fall 10%" is treated as net flow down 10%.
- **Synthetic data only.** The forecast says nothing about a real business.

## Structure

```
app/
  forecast.py    statsmodels baseline and the cash_scenario tool
  qa.py          question -> tool arguments, refusals, answer text
data/            synthetic cash flow and question set
scripts/         data generator and evaluation
tests/           pytest suite
```
