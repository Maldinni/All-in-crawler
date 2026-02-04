from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / "keys.env")

X_BEARER_TOKEN = Path(os.getenv("X_BEARER_TOKEN"))

if not X_BEARER_TOKEN:
    raise RuntimeError("Bearer token not defined at .env")