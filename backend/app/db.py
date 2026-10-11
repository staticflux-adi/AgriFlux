"""SQLite connection helper and schema for AgriFlux."""
import sqlite3
from contextlib import contextmanager
from typing import Iterator

from app.config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS mandis (
    id        INTEGER PRIMARY KEY,
    name      TEXT NOT NULL,
    district  TEXT NOT NULL,
    state     TEXT NOT NULL,
    lat       REAL NOT NULL,
    lon       REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS commodities (
    id                 INTEGER PRIMARY KEY,
    name               TEXT NOT NULL UNIQUE,
    shelf_decay_rate   REAL NOT NULL,
    base_loss_pct      REAL NOT NULL,
    max_transit_hours  REAL NOT NULL
);

-- Raw reported prices only. Gaps (holidays, outages) are simply absent rows;
-- the forecasting module fills them and sets is_imputed on its own copy.
CREATE TABLE IF NOT EXISTS prices (
    mandi_id      INTEGER NOT NULL REFERENCES mandis(id),
    commodity_id  INTEGER NOT NULL REFERENCES commodities(id),
    date          TEXT    NOT NULL,   -- ISO YYYY-MM-DD
    modal_price   REAL    NOT NULL,   -- Rs/quintal
    min_price     REAL,
    max_price     REAL,
    arrival_qtl   REAL,
    is_imputed    INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (mandi_id, commodity_id, date)
);
CREATE INDEX IF NOT EXISTS idx_prices_commodity_date ON prices(commodity_id, date);

CREATE TABLE IF NOT EXISTS forecasts (
    mandi_id      INTEGER NOT NULL REFERENCES mandis(id),
    commodity_id  INTEGER NOT NULL REFERENCES commodities(id),
    made_on       TEXT    NOT NULL,
    target_date   TEXT    NOT NULL,
    p25           REAL    NOT NULL,
    p50           REAL    NOT NULL,
    p75           REAL    NOT NULL,
    confidence    REAL,
    PRIMARY KEY (mandi_id, commodity_id, made_on, target_date)
);

CREATE TABLE IF NOT EXISTS weather (
    district     TEXT    NOT NULL,
    date         TEXT    NOT NULL,
    rain_mm      REAL    NOT NULL,
    temp_c       REAL    NOT NULL,
    is_forecast  INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (district, date)
);

-- Cache of road distances so we never hit the routing API twice for a pair.
CREATE TABLE IF NOT EXISTS distances (
    from_id    INTEGER NOT NULL REFERENCES mandis(id),
    to_id      INTEGER NOT NULL REFERENCES mandis(id),
    road_km    REAL    NOT NULL,
    duration_h REAL    NOT NULL,
    source     TEXT    NOT NULL,      -- 'osrm' or 'haversine'
    PRIMARY KEY (from_id, to_id)
);
"""


@contextmanager
def get_connection() -> Iterator[sqlite3.Connection]:
    """Yield a connection that commits on success and rolls back on error."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Create all tables if they do not exist."""
    with get_connection() as conn:
        conn.executescript(SCHEMA)
