"""Road distance and drive time: OSRM when available, haversine estimate otherwise."""
import logging
import math
import time
from functools import lru_cache

import requests

from app.config import FALLBACK_SPEED_KMPH, OSRM_DURATION_MULTIPLIER, ROAD_FACTOR

logger = logging.getLogger(__name__)

OSRM_URL = "https://router.project-osrm.org/route/v1/driving/{lon1},{lat1};{lon2},{lat2}"
OSRM_TIMEOUT_S = 3
OSRM_COOLDOWN_S = 300  # after a failure, skip OSRM for a while so requests stay fast
EARTH_RADIUS_KM = 6371.0

_osrm_retry_at = 0.0


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi, dlmb = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


@lru_cache(maxsize=512)
def _cached_route(lat1: float, lon1: float, lat2: float, lon2: float) -> tuple[float, float, str]:
    global _osrm_retry_at
    if time.monotonic() >= _osrm_retry_at:
        try:
            resp = requests.get(
                OSRM_URL.format(lat1=lat1, lon1=lon1, lat2=lat2, lon2=lon2),
                params={"overview": "false"},
                timeout=OSRM_TIMEOUT_S,
            )
            resp.raise_for_status()
            route = resp.json()["routes"][0]
            return route["distance"] / 1000, route["duration"] / 3600 * OSRM_DURATION_MULTIPLIER, "osrm"
        except (requests.RequestException, KeyError, IndexError, ValueError) as exc:
            logger.warning("OSRM unavailable (%s); using haversine estimate", exc)
            _osrm_retry_at = time.monotonic() + OSRM_COOLDOWN_S

    km = haversine_km(lat1, lon1, lat2, lon2) * ROAD_FACTOR
    return km, km / FALLBACK_SPEED_KMPH, "haversine"


def get_route(lat1: float, lon1: float, lat2: float, lon2: float) -> tuple[float, float, str]:
    """Return (road_km, truck_hours, source). Coordinates are rounded so results cache well."""
    return _cached_route(round(lat1, 3), round(lon1, 3), round(lat2, 3), round(lon2, 3))
