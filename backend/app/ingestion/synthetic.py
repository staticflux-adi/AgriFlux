"""Synthetic weather and mandi price generator.

Each price series is built from interpretable parts so the forecaster has
real structure to find, plus deliberate mess to test resilience:

  log price = base + seasonality + regional drift (slow AR1)
            + mandi premium + local noise (fast AR1)
            + glut shocks (sudden local price drops that fade)
            + rain shock (lagged price spike after heavy rain)

Mess injected: weekly closures, market holidays, random reporting gaps,
multi-day outages, and rare 10x / 0.1x data-entry outliers.
"""
import numpy as np
import pandas as pd

from app.config import (
    COMMODITIES,
    MANDIS,
    MARKET_HOLIDAYS_MD,
)

GLUT_EVENTS_PER_YEAR = 6
OUTAGES_PER_YEAR = 4
OUTLIER_PROB = 0.004


def _ar1(rng: np.random.Generator, n: int, phi: float, sigma: float) -> np.ndarray:
    """Mean-reverting noise: x[t] = phi * x[t-1] + shock."""
    shocks = rng.normal(0.0, sigma, n)
    out = np.zeros(n)
    for i in range(1, n):
        out[i] = phi * out[i - 1] + shocks[i]
    return out


def _glut_series(rng: np.random.Generator, n: int) -> np.ndarray:
    """Negative log-price shocks (local supply gluts) that decay over 3-7 days."""
    glut = np.zeros(n)
    for _ in range(rng.poisson(GLUT_EVENTS_PER_YEAR * n / 365)):
        start = int(rng.integers(0, n))
        duration = int(rng.integers(3, 8))
        depth = rng.uniform(0.12, 0.30)
        for k in range(duration):
            if start + k < n:
                glut[start + k] -= depth * (1 - k / duration)
    return glut


def _reporting_mask(rng: np.random.Generator, dates: pd.DatetimeIndex, mandi: dict) -> np.ndarray:
    """True on days the mandi actually reported a price."""
    n = len(dates)
    mask = rng.random(n) < mandi["report_prob"]

    if mandi["closed_weekday"] is not None:
        mask &= dates.weekday.to_numpy() != mandi["closed_weekday"]

    is_holiday = np.array([(d.month, d.day) in MARKET_HOLIDAYS_MD for d in dates])
    mask &= ~is_holiday

    for _ in range(rng.poisson(OUTAGES_PER_YEAR * n / 365)):
        start = int(rng.integers(0, n))
        mask[start:start + int(rng.integers(3, 7))] = False
    return mask


def generate_weather(
    rng: np.random.Generator, dates: pd.DatetimeIndex, last_observed: pd.Timestamp
) -> pd.DataFrame:
    """Daily rain and temperature per district; dates after last_observed are forecasts."""
    doy = dates.dayofyear.to_numpy()
    monsoon = np.exp(-(((doy - 200) / 45.0) ** 2))  # peaks mid-July

    frames = []
    for district in sorted({m["district"] for m in MANDIS}):
        rainy = rng.random(len(dates)) < (0.03 + 0.6 * monsoon)
        rain = np.where(rainy, rng.gamma(1.5, 8 + 25 * monsoon), 0.0)
        temp = (27 + 5 * np.sin(2 * np.pi * (doy - 100) / 365)
                - 4 * monsoon + rng.normal(0, 1.5, len(dates)))
        frames.append(pd.DataFrame({
            "district": district,
            "date": dates,
            "rain_mm": rain.round(1),
            "temp_c": temp.round(1),
            "is_forecast": (dates > last_observed).astype(int),
        }))
    return pd.concat(frames, ignore_index=True)


def generate_prices(
    rng: np.random.Generator, dates: pd.DatetimeIndex, weather: pd.DataFrame
) -> pd.DataFrame:
    """Reported prices for every (mandi, commodity); unreported days are absent rows."""
    n = len(dates)
    doy = dates.dayofyear.to_numpy()
    rain = weather.pivot(index="date", columns="district", values="rain_mm").reindex(dates)

    frames = []
    for c in COMMODITIES:
        seasonal = c["seasonal_amp"] * np.cos(2 * np.pi * (doy - c["seasonal_peak_doy"]) / 365)
        regional = _ar1(rng, n, 0.97, c["daily_vol"] * 0.6)

        for m in MANDIS:
            local = _ar1(rng, n, 0.80, c["daily_vol"] * 0.5)
            glut = _glut_series(rng, n)

            # Heavy rain disrupts supply: lagged one day, then fades.
            rain_intensity = np.clip(rain[m["district"]].to_numpy() / 50.0, 0, 1)
            rain_effect = (
                pd.Series(rain_intensity).shift(1).fillna(0).ewm(halflife=2).mean().to_numpy()
                * c["rain_sensitivity"]
            )

            log_price = (np.log(c["base_price"]) + seasonal + regional
                         + m["price_offset"] + local + glut + rain_effect)
            modal = np.exp(log_price)

            # Rare data-entry errors the cleaning step must catch.
            outlier = rng.random(n) < OUTLIER_PROB
            scale = np.ones(n)
            scale[outlier] = rng.choice([0.1, 10.0], size=int(outlier.sum()))
            modal = modal * scale

            # Gluts mean excess supply, so arrivals rise when price falls.
            arrival = c["base_arrival"] * np.exp(-1.5 * (glut + local) + rng.normal(0, 0.15, n))

            frame = pd.DataFrame({
                "mandi_id": m["id"],
                "commodity_id": c["id"],
                "date": dates,
                "modal_price": modal.round(0),
                "min_price": (modal * rng.uniform(0.85, 0.95, n)).round(0),
                "max_price": (modal * rng.uniform(1.05, 1.15, n)).round(0),
                "arrival_qtl": arrival.round(0),
                "is_imputed": 0,
            })
            frames.append(frame[_reporting_mask(rng, dates, m)])

    return pd.concat(frames, ignore_index=True)
