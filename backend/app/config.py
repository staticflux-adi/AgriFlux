"""Central configuration and modelling assumptions for AgriFlux.

Tune values here, not in logic. Commodity parameters are assumptions
for the MVP (approximate, not measured) and are labelled as such in the demo.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
# Vercel's filesystem is read-only except /tmp; demo data is re-seeded on each cold start.
_DEFAULT_DB = Path("/tmp/agriflux.db") if os.getenv("VERCEL") else BASE_DIR / "data" / "agriflux.db"
DB_PATH = Path(os.getenv("AGRIFLUX_DB", _DEFAULT_DB))

# --- Synthetic data settings ---
RANDOM_SEED = 42
HISTORY_DAYS = 365
WEATHER_FORECAST_DAYS = 7

# Fixed-date market holidays as (month, day): Republic Day, Independence Day,
# Gandhi Jayanti, Christmas.
MARKET_HOLIDAYS_MD = {(1, 26), (8, 15), (10, 2), (12, 25)}

# report_prob   : chance a mandi reports on a normal open day (irregular cadence)
# closed_weekday: 0=Mon ... 6=Sun, None = trades every day
# price_offset  : persistent log-price premium/discount vs the regional level
MANDIS = [
    {"id": 1, "name": "Pune APMC", "district": "Pune", "state": "Maharashtra",
     "lat": 18.5196, "lon": 73.8553, "report_prob": 0.95, "closed_weekday": 6, "price_offset": 0.03},
    {"id": 2, "name": "Lasalgaon APMC", "district": "Nashik", "state": "Maharashtra",
     "lat": 20.1424, "lon": 74.2380, "report_prob": 0.97, "closed_weekday": None, "price_offset": -0.08},
    {"id": 3, "name": "Ahmednagar APMC", "district": "Ahmednagar", "state": "Maharashtra",
     "lat": 19.0952, "lon": 74.7496, "report_prob": 0.85, "closed_weekday": 6, "price_offset": -0.04},
    {"id": 4, "name": "Solapur APMC", "district": "Solapur", "state": "Maharashtra",
     "lat": 17.6599, "lon": 75.9064, "report_prob": 0.75, "closed_weekday": 6, "price_offset": -0.05},
    {"id": 5, "name": "Satara APMC", "district": "Satara", "state": "Maharashtra",
     "lat": 17.6805, "lon": 74.0183, "report_prob": 0.65, "closed_weekday": 6, "price_offset": 0.00},
    {"id": 6, "name": "Vashi APMC", "district": "Mumbai", "state": "Maharashtra",
     "lat": 19.0745, "lon": 72.9978, "report_prob": 0.95, "closed_weekday": 6, "price_offset": 0.10},
]

# base_price        : typical modal price, Rs/quintal
# daily_vol         : std-dev of daily log-price shock
# seasonal_amp      : amplitude of yearly seasonal swing (log scale)
# seasonal_peak_doy : day of year when the seasonal price peaks
# rain_sensitivity  : price spike per heavy-rain day (supply disruption)
# base_arrival      : typical daily arrivals per mandi, quintals
# shelf_decay_rate  : exponential spoilage rate per day (used by logistics module)
# base_loss_pct     : handling loss % from loading/unloading
# max_transit_hours : beyond this, transit risk grows sharply
COMMODITIES = [
    {"id": 1, "name": "Onion", "base_price": 1800, "daily_vol": 0.025, "seasonal_amp": 0.15,
     "seasonal_peak_doy": 300, "rain_sensitivity": 0.15, "base_arrival": 1200,
     "shelf_decay_rate": 0.005, "base_loss_pct": 1.0, "max_transit_hours": 36},
    {"id": 2, "name": "Tomato", "base_price": 1500, "daily_vol": 0.060, "seasonal_amp": 0.25,
     "seasonal_peak_doy": 200, "rain_sensitivity": 0.40, "base_arrival": 600,
     "shelf_decay_rate": 0.040, "base_loss_pct": 3.0, "max_transit_hours": 14},
    {"id": 3, "name": "Potato", "base_price": 2000, "daily_vol": 0.020, "seasonal_amp": 0.12,
     "seasonal_peak_doy": 240, "rain_sensitivity": 0.08, "base_arrival": 900,
     "shelf_decay_rate": 0.008, "base_loss_pct": 1.0, "max_transit_hours": 48},
]

# --- Forecast and optimizer settings ---
FORECAST_HORIZON = 7
RISK_AVERSION = 0.5          # 0 = value at median price, 1 = value at P25 (pessimistic)
SAME_DAY_MAX_HOURS = 10.0    # transit up to this still allows a same-day sale
MIN_OBSERVATIONS = 30        # skip mandis with less history than this

# --- Logistics assumptions (approximate Indian rates, tune freely) ---
DIESEL_PRICE_PER_L = 92.0
ROAD_FACTOR = 1.3                # haversine -> road distance when routing API is down
FALLBACK_SPEED_KMPH = 35.0       # loaded truck average incl. stops
OSRM_DURATION_MULTIPLIER = 1.35  # OSRM assumes car speeds; trucks are slower
ROUND_TRIP_FACTOR = 1.6          # return leg is partly recovered with backhaul
MANDI_FEE_PCT = 2.0              # commission, weighing, hamali
STORAGE_COST_PER_QTL_DAY = 2.0
TRANSIT_RISK_PCT_PER_HOUR = 0.15 # expected loss from breakdowns, rough roads, theft
OVERTIME_RISK_PCT_PER_HOUR = 1.5 # extra loss per hour beyond the crop's safe transit time
TEMP_COMFORT_C = 25.0
TEMP_STRESS_PER_C = 0.04         # spoilage multiplier per degree above comfort
RAIN_STORAGE_STRESS = 0.5        # spoilage multiplier at heavy rain
AGE_DECAY_PER_DAY = 0.03         # older harvest spoils faster

TRUCKS = {
    "mini":   {"capacity_qtl": 10,  "mileage_kmpl": 18.0, "other_cost_per_km": 6.0,  "fixed_cost": 150.0},
    "pickup": {"capacity_qtl": 25,  "mileage_kmpl": 12.0, "other_cost_per_km": 10.0, "fixed_cost": 250.0},
    "truck":  {"capacity_qtl": 100, "mileage_kmpl": 5.0,  "other_cost_per_km": 18.0, "fixed_cost": 600.0},
}
