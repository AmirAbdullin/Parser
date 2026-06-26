#!/usr/bin/env python3
"""Start SkillCompass Streamlit dashboard locally."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DASH = ROOT / "services" / "dashboard"

subprocess.run(
    [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "app.py",
        "--server.port",
        "8501",
    ],
    cwd=str(DASH),
    check=False,
)
