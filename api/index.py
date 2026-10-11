"""Vercel entrypoint: serves the whole FastAPI app (every /api/* route) as one function."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.main import app, bootstrap  # noqa: E402

# Serverless instances start with an empty /tmp, so seed the demo data once per cold start.
bootstrap()
