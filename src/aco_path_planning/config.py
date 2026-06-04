from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MAP_DIR = PROJECT_ROOT / "data" / "maps"
DEFAULT_PARAM_FILE = PROJECT_ROOT / "config" / "aco_defaults.json"
