#!/usr/bin/env python3
"""Regenerate manuscript figures using the repository-level figure script."""

from __future__ import annotations

import runpy
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
runpy.run_path(str(ROOT / "scripts" / "make_figures.py"), run_name="__main__")
