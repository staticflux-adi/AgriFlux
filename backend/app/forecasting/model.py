"""Short-term price forecast: damped-trend Holt smoothing on log prices.

Why this model: market series are noisy and non-stationary, so a damped trend
avoids runaway extrapolation, works with little data, and fits in milliseconds.
Uncertainty grows with sqrt(horizon) and widens when data is stale or imputed.
"""
import logging
import warnings
from dataclasses import dataclass

import numpy as np
import pandas as pd
from statsmodels.tsa.holtwinters import ExponentialSmoothing

logger = logging.getLogger(__name__)

TRAIN_WINDOW_DAYS = 120
Z_QUARTILE = 0.6745   # z-score for the 25th/75th percentile
MIN_SIGMA = 0.01
STALE_SIGMA_PER_DAY = 0.1
MAX_STALE_DAYS_FOR_SIGMA = 10


@dataclass
class PriceForecast:
    frame: pd.DataFrame   # rows = day offsets 0..horizon; columns date, p25, p50, p75
    confidence: float     # 0.1 - 1.0, lower when data is stale or imputed
    stale_days: int       # days since the last real (non-imputed) report
    imputed_share: float  # share of the last 14 days that were filled in


def forecast_prices(
    clean: pd.DataFrame,
    horizon: int,
    shock: np.ndarray | None = None,
    sigma_mult: float = 1.0,
) -> PriceForecast:
    """Forecast offsets 0..horizon (0 = today's best estimate).

    shock: additive log-price shift per offset (e.g. rain-driven supply disruption).
    sigma_mult: widens the interval, e.g. during anomalous weather.
    """
    y = np.log(clean["price"].iloc[-TRAIN_WINDOW_DAYS:]).asfreq("D")
    last = float(y.iloc[-1])

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            fit = ExponentialSmoothing(
                y, trend="add", damped_trend=True, initialization_method="estimated"
            ).fit()
        path = np.concatenate([[last], fit.forecast(horizon).to_numpy()])
        resid_std = float(np.std(fit.resid, ddof=1))
    except Exception:  # model failures must never break the API; fall back to naive
        logger.exception("Holt fit failed, using naive forecast")
        path = np.full(horizon + 1, last)
        resid_std = float(np.std(np.diff(y.to_numpy())))

    observed = clean.index[~clean["is_imputed"].to_numpy()]
    stale_days = int((clean.index[-1] - observed[-1]).days) if len(observed) else 999
    imputed_share = float(clean["is_imputed"].iloc[-14:].mean())

    if shock is not None:
        path = path + shock

    steps = np.arange(horizon + 1)
    stale_factor = 1 + STALE_SIGMA_PER_DAY * min(stale_days, MAX_STALE_DAYS_FOR_SIGMA)
    sigma = max(resid_std, MIN_SIGMA) * np.sqrt(np.maximum(steps, 0.5)) * sigma_mult * stale_factor

    dates = [clean.index[-1] + pd.Timedelta(days=int(i)) for i in steps]
    frame = pd.DataFrame({
        "date": dates,
        "p25": np.exp(path - Z_QUARTILE * sigma),
        "p50": np.exp(path),
        "p75": np.exp(path + Z_QUARTILE * sigma),
    })
    confidence = float(np.clip(1 - 0.6 * imputed_share - 0.02 * stale_days, 0.1, 1.0))
    return PriceForecast(frame, confidence, stale_days, imputed_share)
