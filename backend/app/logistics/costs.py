"""Freight, spoilage and transit-risk models. All rates live in config.py."""
import math

from app.config import (
    AGE_DECAY_PER_DAY,
    DIESEL_PRICE_PER_L,
    OVERTIME_RISK_PCT_PER_HOUR,
    ROUND_TRIP_FACTOR,
    TRANSIT_RISK_PCT_PER_HOUR,
    TRUCKS,
)

MAX_TRANSIT_LOSS_PCT = 50.0


def freight_cost(truck_type: str, quantity_qtl: float, road_km: float) -> float:
    """Total transport cost in Rs: trips x (fixed + (fuel + running cost) x km x round-trip factor)."""
    truck = TRUCKS[truck_type]
    trips = math.ceil(quantity_qtl / truck["capacity_qtl"])
    fuel_per_km = DIESEL_PRICE_PER_L / truck["mileage_kmpl"]
    per_km = fuel_per_km + truck["other_cost_per_km"]
    return trips * (truck["fixed_cost"] + road_km * per_km * ROUND_TRIP_FACTOR)


def spoilage_factor(commodity, elapsed_days: float, harvest_age_days: int, stress: float) -> float:
    """Fraction of saleable produce left: exponential decay x handling loss.

    stress > 1 accelerates decay (heat, rain). Older harvests decay faster.
    """
    rate = commodity["shelf_decay_rate"] * (1 + AGE_DECAY_PER_DAY * harvest_age_days) * stress
    return math.exp(-rate * elapsed_days) * (1 - commodity["base_loss_pct"] / 100)


def transit_loss_fraction(hours: float, max_safe_hours: float, risk_multiplier: float) -> float:
    """Expected value lost in transit (breakdowns, rough roads, theft, heat in the truck)."""
    base = TRANSIT_RISK_PCT_PER_HOUR * hours * risk_multiplier
    overtime = OVERTIME_RISK_PCT_PER_HOUR * max(hours - max_safe_hours, 0.0)
    return min(base + overtime, MAX_TRANSIT_LOSS_PCT) / 100
