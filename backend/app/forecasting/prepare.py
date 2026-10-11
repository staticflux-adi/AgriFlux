"""Load raw mandi prices and turn them into a clean, gap-free daily series."""
import sqlite3
from datetime import date

import numpy as np
import pandas as pd

OUTLIER_WINDOW_DAYS = 15
OUTLIER_MAD_MULTIPLIER = 6.0
# Real gluts move prices ~10-30%; data-entry errors are 10x. Only flag huge deviations.
OUTLIER_MIN_LOG_DEVIATION = 0.5
MIN_MAD = 0.01
MAX_INTERP_GAP_DAYS = 3


def today_ts() -> pd.Timestamp:
    return pd.Timestamp(date.today())


def load_raw_series(
    conn: sqlite3.Connection, mandi_id: int, commodity_id: int, end: pd.Timestamp
) -> pd.Series:
    """Daily series of reported modal prices; unreported days are NaN (never zero)."""
    rows = conn.execute(
        "SELECT date, modal_price FROM prices WHERE mandi_id = ? AND commodity_id = ? ORDER BY date",
        (mandi_id, commodity_id),
    ).fetchall()
    if not rows:
        return pd.Series(dtype=float)
    series = pd.Series(
        [r["modal_price"] for r in rows],
        index=pd.to_datetime([r["date"] for r in rows]),
        dtype=float,
    )
    return series.reindex(pd.date_range(series.index.min(), max(end, series.index.max()), freq="D"))


def clean_series(raw: pd.Series) -> pd.DataFrame:
    """Remove data-entry outliers, fill gaps, and flag every filled point.

    Short gaps (<= 3 days) are interpolated. Longer gaps are carried forward;
    the forecaster widens its interval for them via the imputed share.
    """
    log_price = np.log(raw)
    median = log_price.rolling(OUTLIER_WINDOW_DAYS, center=True, min_periods=5).median()
    resid = log_price - median
    scale = max(float(resid.abs().median()), MIN_MAD) * 1.4826
    threshold = max(OUTLIER_MAD_MULTIPLIER * scale, OUTLIER_MIN_LOG_DEVIATION)
    is_outlier = resid.abs() > threshold

    observed = raw.notna() & ~is_outlier
    filled = (
        log_price.where(~is_outlier)
        .interpolate(method="time", limit=MAX_INTERP_GAP_DAYS)
        .ffill()
        .bfill()
    )
    return pd.DataFrame({"price": np.exp(filled), "is_imputed": ~observed})
