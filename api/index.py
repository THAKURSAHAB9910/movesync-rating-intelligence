"""Vercel Serverless Entrypoint for MoveInSync Rating Intelligence FastAPI App."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app import app
