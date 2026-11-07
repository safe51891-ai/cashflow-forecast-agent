"""Cash flow forecast with a statsmodels baseline, exposed as one tool: cash_scenario.

The baseline is Holt-Winters exponential smoothing (additive trend and seasonality, 12-month season).
A scenario applies a percentage change to the forecast net cash flow in every month.
The tool returns the numbers. Nothing else in the app is allowed to invent them.
"""
from decimal import Decimal
from pathlib import Path

import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DATA = ROOT / "data" / "synthetic_cashflow.csv"
DEFAULT_OPENING_BALANCE = Decimal("250000.00")
SEASONAL_PERIODS = 12


class ForecastError(ValueError):
    """The request cannot be answered with the forecast."""


def load_history(path: Path = DEFAULT_DATA) -> pd.Series:
    frame = pd.read_csv(path)
    series = pd.Series(frame["net_cash_flow"].to_numpy(), index=pd.PeriodIndex(frame["month"], freq="M"))
    return series


def baseline_forecast(history: pd.Series, months: int) -> pd.Series:
    """Point forecast of monthly net cash flow for the next `months` months."""
    if months < 1 or months > 36:
        raise ForecastError("months must be between 1 and 36")
    model = ExponentialSmoothing(
        history.to_numpy(dtype=float),
        trend="add",
        seasonal="add",
        seasonal_periods=SEASONAL_PERIODS,
    ).fit()
    values = model.forecast(months)
    index = pd.period_range(history.index[-1] + 1, periods=months, freq="M")
    return pd.Series(values, index=index)


def cash_scenario(
    months: int,
    change_pct: float = 0.0,
    opening_balance: Decimal = DEFAULT_OPENING_BALANCE,
    history: pd.Series | None = None,
) -> dict:
    """Tool: ending balance and lowest balance over the next `months` months under a scenario.

    change_pct applies to every forecast month's net cash flow, e.g. -15 means net flow is 15% lower.
    """
    if change_pct <= -100:
        raise ForecastError("change_pct must be greater than -100")
    history = load_history() if history is None else history
    base = baseline_forecast(history, months)
    scenario = base * (1 + change_pct / 100)

    balances = [opening_balance + Decimal(str(round(float(v), 2))) for v in scenario.cumsum().values]
    lowest_idx = min(range(len(balances)), key=lambda i: balances[i])
    return {
        "months": months,
        "change_pct": change_pct,
        "opening_balance": str(opening_balance),
        "ending_balance": f"{balances[-1]:.2f}",
        "lowest_balance": f"{balances[lowest_idx]:.2f}",
        "lowest_month": str(scenario.index[lowest_idx]),
        "monthly_net_flow": {str(p): f"{v:.2f}" for p, v in scenario.items()},
    }
