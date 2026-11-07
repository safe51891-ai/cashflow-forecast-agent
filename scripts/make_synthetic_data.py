"""Create data/synthetic_cashflow.csv: 36 months of invented net cash flow with seasonality and trend.

Deterministic (fixed seed), so results are reproducible.
Usage: python scripts/make_synthetic_data.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
rng = np.random.default_rng(42)

months = pd.period_range("2023-01", periods=36, freq="M")
t = np.arange(36)
season = 40_000 * np.sin(2 * np.pi * (t % 12) / 12)  # busier and quieter months
trend = 1_500 * t  # gradual improvement
noise = rng.normal(0, 8_000, size=36)
net = 30_000 + trend + season + noise

frame = pd.DataFrame({"month": months.strftime("%Y-%m"), "net_cash_flow": np.round(net, 2)})
frame.to_csv(ROOT / "data" / "synthetic_cashflow.csv", index=False)
print(frame.head(3).to_string(index=False))
print(f"... {len(frame)} rows written")
