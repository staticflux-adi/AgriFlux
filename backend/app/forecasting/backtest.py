"""Rolling-origin backtest: the model vs a 'tomorrow equals today' baseline.

Each origin only sees data up to that day (cleaning included), so there is no leakage.
Actuals are real reported prices only, never imputed ones.
"""
import sqlite3

import numpy as np
import pandas as pd

from app.forecasting.model import forecast_prices
from app.forecasting.prepare import clean_series, load_raw_series

HORIZONS = (3, 7)
ORIGIN_STEP_DAYS = 10
N_ORIGINS = 9
MIN_TRAIN_DAYS = 60
MIN_OBSERVATIONS = 30
MAX_LOG_MOVE = 0.7  # larger one-step jumps are treated as data-entry errors and skipped


def run_backtest(
    conn: sqlite3.Connection, commodity_id: int, mandi_ids: list[int], end: pd.Timestamp
) -> dict:
    stats = {h: {"model": [], "naive": [], "hit": []} for h in HORIZONS}

    for mandi_id in mandi_ids:
        raw = load_raw_series(conn, mandi_id, commodity_id, end)
        if raw.notna().sum() < 90:
            continue
        for k in range(N_ORIGINS):
            origin = len(raw) - 1 - max(HORIZONS) - k * ORIGIN_STEP_DAYS
            if origin < MIN_TRAIN_DAYS:
                break
            train = raw.iloc[: origin + 1]
            if train.notna().sum() < MIN_OBSERVATIONS:
                continue
            clean = clean_series(train)
            frame = forecast_prices(clean, max(HORIZONS)).frame
            last = float(clean["price"].iloc[-1])

            for h in HORIZONS:
                actual = raw.iloc[origin + h]
                if np.isnan(actual) or abs(np.log(actual / last)) > MAX_LOG_MOVE:
                    continue
                pred = float(frame["p50"].iloc[h])
                stats[h]["model"].append(abs(pred - actual) / actual)
                stats[h]["naive"].append(abs(last - actual) / actual)
                if actual != last:
                    stats[h]["hit"].append(float(np.sign(pred - last) == np.sign(actual - last)))

    result = {}
    for h, s in stats.items():
        if not s["model"]:
            result[str(h)] = None
            continue
        model_mape = float(np.mean(s["model"]) * 100)
        naive_mape = float(np.mean(s["naive"]) * 100)
        result[str(h)] = {
            "samples": len(s["model"]),
            "model_mape_pct": round(model_mape, 2),
            "naive_mape_pct": round(naive_mape, 2),
            "improvement_pct": round((naive_mape - model_mape) / naive_mape * 100, 1),
            "directional_accuracy_pct": round(float(np.mean(s["hit"]) * 100), 1) if s["hit"] else None,
        }
    return {"horizons": result}
