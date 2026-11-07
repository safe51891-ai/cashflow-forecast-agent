from decimal import Decimal

import pandas as pd
import pytest

from app.forecast import ForecastError, baseline_forecast, cash_scenario, load_history


def flat_history(value=10_000.0, months=36):
    index = pd.period_range("2023-01", periods=months, freq="M")
    return pd.Series([value] * months, index=index)


def test_history_loads_36_months():
    history = load_history()
    assert len(history) == 36
    assert str(history.index[0]) == "2023-01"


def test_baseline_forecast_has_requested_length_and_next_months():
    forecast = baseline_forecast(flat_history(), 6)
    assert len(forecast) == 6
    assert str(forecast.index[0]) == "2026-01"


def test_zero_change_scenario_matches_baseline_cumulative_flow():
    history = flat_history(10_000.0)
    result = cash_scenario(months=3, change_pct=0, opening_balance=Decimal("1000.00"), history=history)
    base = baseline_forecast(history, 3)
    expected_end = Decimal("1000.00") + Decimal(str(round(float(base.sum()), 2)))
    assert abs(Decimal(result["ending_balance"]) - expected_end) < Decimal("0.05")


def test_drop_scenario_gives_lower_ending_balance_than_baseline():
    history = flat_history(10_000.0)
    base = cash_scenario(months=6, change_pct=0, history=history)
    down = cash_scenario(months=6, change_pct=-20, history=history)
    assert Decimal(down["ending_balance"]) < Decimal(base["ending_balance"])


def test_lowest_balance_is_never_above_ending_balance_when_flows_are_positive():
    result = cash_scenario(months=6, change_pct=0, history=flat_history(5_000.0))
    assert Decimal(result["lowest_balance"]) <= Decimal(result["ending_balance"])


def test_months_out_of_range_is_rejected():
    with pytest.raises(ForecastError):
        baseline_forecast(flat_history(), 0)
    with pytest.raises(ForecastError):
        baseline_forecast(flat_history(), 37)


def test_change_of_minus_100_or_less_is_rejected():
    with pytest.raises(ForecastError):
        cash_scenario(months=3, change_pct=-100, history=flat_history())
