#!/usr/bin/env python3
"""Start SkillCompass FastAPI locally."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_SRC = ROOT / "services" / "api" / "src"

subprocess.run(
    [
        sys.executable,
        "-m",
        "uvicorn",
        "main:app",
        "--app-dir",
        str(API_SRC),
        "--host",
        "127.0.0.1",
        "--port",
        "8000",
        "--reload",
    ],
    cwd=str(ROOT),
    check=False,
)
