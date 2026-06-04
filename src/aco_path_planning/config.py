from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MAP_DIR = PROJECT_ROOT / "data" / "maps"
DEFAULT_GENERATED_MAP_DIR = DEFAULT_MAP_DIR / "generated"
DEFAULT_PARAM_FILE = PROJECT_ROOT / "config" / "aco_defaults.json"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "data" / "outputs"
DEFAULT_CLI_OUTPUT_DIR = DEFAULT_OUTPUT_ROOT / "cli"
DEFAULT_STREAMLIT_OUTPUT_DIR = DEFAULT_OUTPUT_ROOT / "streamlit"
