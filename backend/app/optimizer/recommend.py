"""Dispatch optimizer: score every (mandi, sell day) and pick the best net profit.

net = quantity x risk-adjusted price x freshness x (1 - transit loss) x (1 - fees)
      - freight and fuel - storage

The risk-adjusted price sits between the forecast median and P25, so a volatile
forecast must beat a stable one by enough margin to win.
"""
import logging
import sqlite3

import numpy as np
import pandas as pd

from app.config import (
    COMMODITIES,
    FORECAST_HORIZON,
    MANDI_FEE_PCT,
    MIN_OBSERVATIONS,
    RAIN_STORAGE_STRESS,
    RISK_AVERSION,
    SAME_DAY_MAX_HOURS,
    STORAGE_COST_PER_QTL_DAY,
    TEMP_COMFORT_C,
    TEMP_STRESS_PER_C,
)
from app.forecasting.model import forecast_prices
from app.forecasting.prepare import clean_series, load_raw_series, today_ts
from app.logistics.costs import freight_cost, spoilage_factor, transit_loss_fraction
from app.logistics.distance import get_route, haversine_km
from app.schemas import RecommendRequest

logger = logging.getLogger(__name__)

HEAVY_RAIN_MM = 50.0
SIMULATED_RAIN_MM = 80.0
SIMULATED_RAIN_DAYS = (1, 2, 3)
DEFAULT_TEMP_C = 28.0
DEFAULT_RAIN_SENSITIVITY = 0.1
LOW_CONFIDENCE = 0.7
RAIN_SIGMA_BOOST = 0.5
TOP_OPTIONS = 12

RAIN_SENSITIVITY = {c["id"]: c["rain_sensitivity"] for c in COMMODITIES}


def _load_weather(conn: sqlite3.Connection, today: pd.Timestamp, horizon: int):
    """Rain (mm) and temperature per district for day offsets 0..horizon."""
    end = today + pd.Timedelta(days=horizon)
    rows = conn.execute(
        "SELECT district, date, rain_mm, temp_c FROM weather WHERE date BETWEEN ? AND ?",
        (today.strftime("%Y-%m-%d"), end.strftime("%Y-%m-%d")),
    ).fetchall()
    rain: dict[str, np.ndarray] = {}
    temp: dict[str, np.ndarray] = {}
    for r in rows:
        offset = (pd.Timestamp(r["date"]) - today).days
        rain.setdefault(r["district"], np.zeros(horizon + 1))[offset] = r["rain_mm"]
        temp.setdefault(r["district"], np.full(horizon + 1, DEFAULT_TEMP_C))[offset] = r["temp_c"]
    return rain, temp


def _fmt_date(ts: pd.Timestamp) -> str:
    return ts.strftime("%a %d %b")


def _public(option: dict) -> dict:
    """Round numbers for the API response."""
    money = ("price_p25", "price_p50", "price_used", "gross", "spoilage_loss",
             "risk_loss", "fees", "freight", "storage", "net", "net_per_qtl")
    out = dict(option)
    for key in money:
        out[key] = round(float(out[key]))
    for key in ("road_km", "transit_hours", "spoilage_pct", "risk_pct"):
        out[key] = round(float(out[key]), 1)
    out["confidence"] = round(float(out["confidence"]), 2)
    return out


def recommend(
    conn: sqlite3.Connection, req: RecommendRequest, today: pd.Timestamp | None = None
) -> dict:
    today = today or today_ts()
    horizon = FORECAST_HORIZON

    commodity = conn.execute(
        "SELECT * FROM commodities WHERE lower(name) = lower(?)", (req.commodity,)
    ).fetchone()
    if commodity is None:
        raise ValueError(f"Unknown commodity '{req.commodity}'")
    mandis = [dict(r) for r in conn.execute("SELECT * FROM mandis").fetchall()]

    rain, temp = _load_weather(conn, today, horizon)
    origin_mandi = min(mandis, key=lambda m: haversine_km(req.lat, req.lon, m["lat"], m["lon"]))
    origin_district = origin_mandi["district"]
    origin_rain = rain.get(origin_district, np.zeros(horizon + 1)).copy()
    origin_temp = temp.get(origin_district, np.full(horizon + 1, DEFAULT_TEMP_C))
    if req.simulate_rain:
        for day in SIMULATED_RAIN_DAYS:
            origin_rain[day] = SIMULATED_RAIN_MM
        rain[origin_district] = origin_rain

    rain_sensitivity = RAIN_SENSITIVITY.get(commodity["id"], DEFAULT_RAIN_SENSITIVITY)
    options: list[dict] = []
    forecasts: dict[str, list[dict]] = {}
    mandi_meta: dict[int, dict] = {}
    max_p50 = 0.0

    for m in mandis:
        raw = load_raw_series(conn, m["id"], commodity["id"], today)
        if raw.notna().sum() < MIN_OBSERVATIONS:
            logger.warning("Skipping %s: too little price history", m["name"])
            continue
        clean = clean_series(raw)

        dest_rain = rain.get(m["district"], np.zeros(horizon + 1))
        shock = np.zeros(horizon + 1)  # heavy rain yesterday lifts today's price (supply disruption)
        shock[1:] = rain_sensitivity * np.clip(dest_rain[:-1] / HEAVY_RAIN_MM, 0, 1)
        sigma_mult = 1 + RAIN_SIGMA_BOOST * float(np.clip(dest_rain[:4].max() / HEAVY_RAIN_MM, 0, 1))
        fc = forecast_prices(clean, horizon, shock, sigma_mult)
        max_p50 = max(max_p50, float(fc.frame["p50"].max()))
        forecasts[m["name"]] = [
            {"date": r.date.strftime("%Y-%m-%d"), "p25": round(r.p25), "p50": round(r.p50), "p75": round(r.p75)}
            for r in fc.frame.itertuples()
        ]

        road_km, hours, route_source = get_route(req.lat, req.lon, m["lat"], m["lon"])
        freight = freight_cost(req.truck_type, req.quantity_qtl, road_km)
        earliest = 0 if hours <= SAME_DAY_MAX_HOURS else min(
            horizon, 1 + int((hours - SAME_DAY_MAX_HOURS) // 24)
        )
        mandi_meta[m["id"]] = {
            "id": m["id"], "name": m["name"], "district": m["district"], "lat": m["lat"], "lon": m["lon"],
            "road_km": road_km, "transit_hours": hours, "stale_days": fc.stale_days,
            "confidence": fc.confidence, "route_source": route_source,
        }

        for s in range(earliest, horizon + 1):
            # Produce waits at the farm until sale; heat and rain on those days speed spoilage.
            stress = float(np.mean([
                (1 + TEMP_STRESS_PER_C * max(origin_temp[i] - TEMP_COMFORT_C, 0.0))
                * (1 + RAIN_STORAGE_STRESS * np.clip(origin_rain[i] / HEAVY_RAIN_MM, 0, 1))
                for i in range(max(s, 1))
            ]))
            fresh = spoilage_factor(commodity, max(s, hours / 24), req.harvest_age_days, stress)
            rain_on_route = max(origin_rain[s], dest_rain[s])
            risk_frac = transit_loss_fraction(
                hours, commodity["max_transit_hours"], 1 + float(np.clip(rain_on_route / HEAVY_RAIN_MM, 0, 1))
            )

            row = fc.frame.iloc[s]
            price_used = row["p50"] - RISK_AVERSION * (row["p50"] - row["p25"])
            gross = req.quantity_qtl * price_used
            spoilage_loss = gross * (1 - fresh)
            risk_loss = gross * fresh * risk_frac
            sold = gross - spoilage_loss - risk_loss
            fees = sold * MANDI_FEE_PCT / 100
            storage = req.quantity_qtl * STORAGE_COST_PER_QTL_DAY * s
            net = sold - fees - freight - storage

            options.append({
                "mandi": m["name"], "mandi_id": m["id"], "sell_day": s,
                "sell_date": row["date"].strftime("%Y-%m-%d"), "sell_label": _fmt_date(row["date"]),
                "price_p25": row["p25"], "price_p50": row["p50"], "price_used": price_used,
                "road_km": road_km, "transit_hours": hours, "route_source": route_source,
                "gross": gross, "spoilage_loss": spoilage_loss, "risk_loss": risk_loss,
                "fees": fees, "freight": freight, "storage": storage,
                "net": net, "net_per_qtl": net / req.quantity_qtl,
                "spoilage_pct": (1 - fresh) * 100, "risk_pct": risk_frac * 100,
                "confidence": fc.confidence,
            })

    if not options:
        raise ValueError("No mandi has enough price data for this commodity")

    best = max(options, key=lambda o: o["net"])
    nearest_id = min(mandi_meta, key=lambda i: mandi_meta[i]["road_km"])
    baseline = min((o for o in options if o["mandi_id"] == nearest_id), key=lambda o: o["sell_day"])
    uplift = best["net"] - baseline["net"]
    theoretical = req.quantity_qtl * max_p50  # best forecast price anywhere, no costs, no losses
    realization = min(max(best["net"], 0) / theoretical * 100, 100)

    is_baseline = best["mandi_id"] == baseline["mandi_id"] and best["sell_day"] == baseline["sell_day"]
    if is_baseline:
        headline = f"Sell now at {best['mandi']}"
    elif best["mandi_id"] == baseline["mandi_id"]:
        headline = f"Hold and sell at {best['mandi']} on {best['sell_label']}"
    else:
        headline = f"Take it to {best['mandi']} and sell on {best['sell_label']}"

    reasoning = [
        f"Expected net ₹{best['net']:,.0f} versus ₹{baseline['net']:,.0f} selling at {baseline['mandi']} "
        f"on {baseline['sell_label']} (uplift ₹{uplift:,.0f}).",
        f"Risk-adjusted price ₹{best['price_used']:,.0f}/qtl at {best['mandi']} versus "
        f"₹{baseline['price_used']:,.0f}/qtl at {baseline['mandi']}.",
        f"Freight and fuel ₹{best['freight']:,.0f} over {best['road_km']:.0f} km "
        f"(about {best['transit_hours']:.1f} h); spoilage and transit loss "
        f"₹{best['spoilage_loss'] + best['risk_loss']:,.0f}.",
    ]
    if best["sell_day"] > 0:
        reasoning.append(
            f"Waiting {best['sell_day']} day(s) pays off: the forecast gain outweighs "
            f"₹{best['storage']:,.0f} storage and {best['spoilage_pct']:.1f}% spoilage."
        )
    if req.simulate_rain:
        reasoning.append(
            f"Heavy-rain scenario active around {origin_district}: spoilage and transit risk are raised."
        )
    if best["confidence"] < LOW_CONFIDENCE:
        reasoning.append(
            f"Price data for {best['mandi']} is stale or partly imputed, so confidence is reduced."
        )

    summary = []
    for mandi_id, meta in mandi_meta.items():
        top = max((o for o in options if o["mandi_id"] == mandi_id), key=lambda o: o["net"])
        summary.append({
            **{k: meta[k] for k in ("id", "name", "district", "lat", "lon", "stale_days")},
            "road_km": round(meta["road_km"], 1), "transit_hours": round(meta["transit_hours"], 1),
            "confidence": round(meta["confidence"], 2),
            "best_net": round(top["net"]), "best_day": top["sell_day"],
        })

    return {
        "commodity": commodity["name"],
        "quantity_qtl": req.quantity_qtl,
        "meta": {
            "origin_mandi": origin_mandi["name"], "origin_district": origin_district,
            "rain_simulated": req.simulate_rain, "route_source": best["route_source"],
        },
        "recommendation": {
            "headline": headline, "mandi": best["mandi"], "sell_date": best["sell_date"],
            "sell_label": best["sell_label"], "sell_day": best["sell_day"],
            "net": round(best["net"]), "uplift": round(uplift),
            "realization_score": round(realization, 1), "confidence": round(best["confidence"], 2),
            "same_as_baseline": is_baseline,
        },
        "best": _public(best),
        "baseline": _public(baseline),
        "options": [_public(o) for o in sorted(options, key=lambda o: o["net"], reverse=True)[:TOP_OPTIONS]],
        "mandi_summary": summary,
        "forecasts": forecasts,
        "reasoning": reasoning,
    }
