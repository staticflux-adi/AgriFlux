"""Seed the database with synthetic data.

Run from the backend/ folder:  python -m scripts.seed
Safe to re-run: prices and weather are replaced, reference tables are upserted.
"""
from datetime import date

import numpy as np
import pandas as pd

from app.config import (
    COMMODITIES,
    HISTORY_DAYS,
    MANDIS,
    RANDOM_SEED,
    WEATHER_FORECAST_DAYS,
)
from app.db import get_connection, init_db
from app.ingestion.synthetic import generate_prices, generate_weather

UPSERT_MANDI = """
INSERT INTO mandis (id, name, district, state, lat, lon)
VALUES (:id, :name, :district, :state, :lat, :lon)
ON CONFLICT(id) DO UPDATE SET name=excluded.name, district=excluded.district,
    state=excluded.state, lat=excluded.lat, lon=excluded.lon
"""

UPSERT_COMMODITY = """
INSERT INTO commodities (id, name, shelf_decay_rate, base_loss_pct, max_transit_hours)
VALUES (:id, :name, :shelf_decay_rate, :base_loss_pct, :max_transit_hours)
ON CONFLICT(id) DO UPDATE SET name=excluded.name, shelf_decay_rate=excluded.shelf_decay_rate,
    base_loss_pct=excluded.base_loss_pct, max_transit_hours=excluded.max_transit_hours
"""


def main() -> None:
    rng = np.random.default_rng(RANDOM_SEED)
    today = pd.Timestamp(date.today())
    history = pd.date_range(end=today, periods=HISTORY_DAYS, freq="D")
    all_dates = pd.date_range(history[0], periods=HISTORY_DAYS + WEATHER_FORECAST_DAYS, freq="D")

    weather = generate_weather(rng, all_dates, last_observed=today)
    prices = generate_prices(rng, history, weather[weather["is_forecast"] == 0])

    for frame in (weather, prices):
        frame["date"] = frame["date"].dt.strftime("%Y-%m-%d")

    init_db()
    with get_connection() as conn:
        conn.execute("DELETE FROM prices")
        conn.execute("DELETE FROM weather")
        conn.executemany(UPSERT_MANDI, MANDIS)
        conn.executemany(UPSERT_COMMODITY, COMMODITIES)
        weather.to_sql("weather", conn, if_exists="append", index=False)
        prices.to_sql("prices", conn, if_exists="append", index=False)

    possible = len(history) * len(MANDIS) * len(COMMODITIES)
    print(f"Seeded {len(prices)} price rows ({1 - len(prices) / possible:.0%} missing), "
          f"{len(weather)} weather rows.")


if __name__ == "__main__":
    main()
