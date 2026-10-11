"""HTTP API. Thin layer: validate, call the domain code, map errors to HTTP codes."""
import logging
import sqlite3

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from app.config import FORECAST_HORIZON
from app.db import get_connection
from app.forecasting.backtest import run_backtest
from app.forecasting.model import forecast_prices
from app.forecasting.prepare import clean_series, load_raw_series, today_ts
from app.optimizer.recommend import recommend
from app.schemas import RecommendRequest

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api")

_backtest_cache: dict[int, dict] = {}  # backtests take a few seconds; compute once per crop

STALE_OK_DAYS = 2
STALE_WARN_DAYS = 7


def _commodity(conn: sqlite3.Connection, name: str) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM commodities WHERE lower(name) = lower(?)", (name,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Unknown commodity '{name}'")
    return row


def _clean_for(conn: sqlite3.Connection, mandi_id: int, commodity_id: int) -> pd.DataFrame:
    raw = load_raw_series(conn, mandi_id, commodity_id, today_ts())
    if raw.notna().sum() == 0:
        raise HTTPException(status_code=404, detail="No price data for this mandi and commodity")
    return clean_series(raw)


@router.get("/mandis")
def list_mandis() -> list[dict]:
    with get_connection() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM mandis ORDER BY name").fetchall()]


@router.get("/prices")
def get_prices(commodity: str, mandi_id: int, days: int = Query(90, ge=7, le=365)) -> list[dict]:
    with get_connection() as conn:
        clean = _clean_for(conn, mandi_id, _commodity(conn, commodity)["id"]).iloc[-days:]
    return [
        {"date": ts.strftime("%Y-%m-%d"), "price": round(float(row["price"])), "is_imputed": bool(row["is_imputed"])}
        for ts, row in clean.iterrows()
    ]


@router.get("/forecast")
def get_forecast(
    commodity: str, mandi_id: int, horizon: int = Query(FORECAST_HORIZON, ge=1, le=14)
) -> dict:
    with get_connection() as conn:
        clean = _clean_for(conn, mandi_id, _commodity(conn, commodity)["id"])
    fc = forecast_prices(clean, horizon)
    return {
        "confidence": round(fc.confidence, 2),
        "stale_days": fc.stale_days,
        "forecast": [
            {"date": r.date.strftime("%Y-%m-%d"), "p25": round(r.p25), "p50": round(r.p50), "p75": round(r.p75)}
            for r in fc.frame.itertuples()
        ],
    }


@router.post("/recommend")
def post_recommend(req: RecommendRequest) -> dict:
    with get_connection() as conn:
        try:
            return recommend(conn, req)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/backtest")
def get_backtest(commodity: str) -> dict:
    with get_connection() as conn:
        commodity_row = _commodity(conn, commodity)
        if commodity_row["id"] not in _backtest_cache:
            mandi_ids = [r["id"] for r in conn.execute("SELECT id FROM mandis").fetchall()]
            _backtest_cache[commodity_row["id"]] = run_backtest(
                conn, commodity_row["id"], mandi_ids, today_ts()
            )
        return {"commodity": commodity_row["name"], **_backtest_cache[commodity_row["id"]]}


@router.get("/health/data")
def data_health() -> list[dict]:
    """Per mandi and commodity: how fresh and complete is the reporting?"""
    today = today_ts()
    since = (today - pd.Timedelta(days=29)).strftime("%Y-%m-%d")
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT m.name AS mandi, c.name AS commodity, MAX(p.date) AS last_reported,
                   SUM(CASE WHEN p.date >= ? THEN 1 ELSE 0 END) AS reports_30d
            FROM prices p
            JOIN mandis m ON m.id = p.mandi_id
            JOIN commodities c ON c.id = p.commodity_id
            GROUP BY p.mandi_id, p.commodity_id
            ORDER BY m.name, c.name
            """,
            (since,),
        ).fetchall()
    out = []
    for r in rows:
        stale = (today - pd.Timestamp(r["last_reported"])).days
        status = "ok" if stale <= STALE_OK_DAYS else "stale" if stale <= STALE_WARN_DAYS else "outage"
        out.append({
            "mandi": r["mandi"], "commodity": r["commodity"], "last_reported": r["last_reported"],
            "stale_days": stale, "missing_pct_30d": round(100 * (1 - r["reports_30d"] / 30), 1),
            "status": status,
        })
    return out
