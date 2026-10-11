"""AgriFlux API entrypoint.

Local:  uvicorn app.main:app --reload   (run from backend/)
Vercel: api/index.py imports this app and calls bootstrap() on cold start.
"""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import get_connection, init_db
from app.routes import router

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def bootstrap() -> None:
    """Create tables and seed demo data if the database is empty. Safe to call repeatedly."""
    init_db()
    with get_connection() as conn:
        has_data = conn.execute("SELECT COUNT(*) FROM prices").fetchone()[0] > 0
    if not has_data:
        from scripts.seed import main as seed  # demo data so the app is never empty

        logger.info("Empty database, seeding synthetic data")
        seed()


@asynccontextmanager
async def lifespan(_: FastAPI):
    bootstrap()
    yield


# Same-origin deployments (Vercel) need no CORS. Set CORS_ORIGINS="https://a.com,https://b.com"
# only if the frontend is hosted on a different domain than the API.
ALLOWED_ORIGINS = [
    o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",") if o.strip()
]

app = FastAPI(title="AgriFlux", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)
app.include_router(router)
