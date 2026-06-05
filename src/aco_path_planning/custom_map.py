from __future__ import annotations

import csv
import re
from datetime import datetime
from pathlib import Path

import numpy as np

from .map_loader import build_grid_map_from_cells
from .models import GridMap

EMPTY = 0
OBSTACLE = 1
START = 2
GOAL = 3

BRUSH_OBSTACLE = "obstacle"
BRUSH_START = "start"
BRUSH_GOAL = "goal"
BRUSH_ERASE = "erase"

BRUSH_VALUES = {
    BRUSH_OBSTACLE: OBSTACLE,
    BRUSH_START: START,
    BRUSH_GOAL: GOAL,
    BRUSH_ERASE: EMPTY,
}

CUSTOM_MAP_PREFIX = "custom_"
_NAME_SANITIZE_PATTERN = re.compile(r"[^0-9A-Za-z_\-]+")


def create_empty_grid(rows: int, cols: int) -> np.ndarray:
    """Create an empty editable grid with a default start (top-left) and goal (bottom-right)."""
    if rows < 2 or cols < 2:
        raise ValueError("Grid must be at least 2 x 2 to hold a start and a goal.")

    grid = np.zeros((rows, cols), dtype=np.int8)
    grid[0, 0] = START
    grid[rows - 1, cols - 1] = GOAL
    return grid


def apply_brush(grid: np.ndarray, row: int, col: int, brush: str) -> np.ndarray:
    """Paint a single cell with the selected brush, keeping start/goal unique.

    Mutates ``grid`` in place and returns it for convenience.
    """
    if brush not in BRUSH_VALUES:
        raise ValueError(f"Unknown brush '{brush}'.")
    if not (0 <= row < grid.shape[0] and 0 <= col < grid.shape[1]):
        raise ValueError(f"Cell ({row}, {col}) is outside the grid.")

    target_value = BRUSH_VALUES[brush]

    # Start and goal must stay unique: clear any previous cell of the same kind.
    if target_value in (START, GOAL):
        grid[grid == target_value] = EMPTY

    grid[row, col] = target_value
    return grid


def count_markers(grid: np.ndarray) -> tuple[int, int]:
    """Return (start_count, goal_count) currently painted on the grid."""
    start_count = int(np.count_nonzero(grid == START))
    goal_count = int(np.count_nonzero(grid == GOAL))
    return start_count, goal_count


def is_ready_to_save(grid: np.ndarray) -> bool:
    """A map is saveable once it has exactly one start and one goal."""
    start_count, goal_count = count_markers(grid)
    return start_count == 1 and goal_count == 1


def build_grid_map_from_array(grid: np.ndarray, source: Path | None = None) -> GridMap:
    """Build a validated GridMap from an in-memory editor grid."""
    raw_grid = np.asarray(grid, dtype=np.int8)
    return build_grid_map_from_cells(raw_grid, source=source)


def sanitize_map_name(name: str) -> str:
    """Reduce a user-supplied name to a safe CSV stem (no path, no extension)."""
    stem = Path(name.strip()).stem
    stem = _NAME_SANITIZE_PATTERN.sub("_", stem).strip("_")
    return stem


def generate_custom_map_name(
    existing_names: list[str],
    now: datetime | None = None,
) -> str:
    """Build a timestamped, sequence-numbered stem that does not collide with existing maps."""
    current_time = now or datetime.now()
    timestamp = current_time.strftime("%Y%m%d_%H%M%S")
    existing_stems = {Path(name).stem for name in existing_names}

    sequence = sum(1 for name in existing_names if Path(name).stem.startswith(CUSTOM_MAP_PREFIX)) + 1
    candidate = f"{CUSTOM_MAP_PREFIX}{timestamp}_{sequence}"
    while candidate in existing_stems:
        sequence += 1
        candidate = f"{CUSTOM_MAP_PREFIX}{timestamp}_{sequence}"
    return candidate


def resolve_map_filename(
    user_name: str,
    existing_names: list[str],
    now: datetime | None = None,
) -> str:
    """Decide the final ``<name>.csv`` filename from optional user input."""
    cleaned = sanitize_map_name(user_name) if user_name else ""
    stem = cleaned or generate_custom_map_name(existing_names, now=now)
    return f"{stem}.csv"


def save_custom_map(
    grid: np.ndarray,
    file_name: str,
    directory: str | Path,
) -> Path:
    """Validate then persist the grid as a CSV map under ``directory``.

    Raises ValueError if the grid does not have exactly one start and one goal.
    """
    # Validate before writing so we never persist an unusable map.
    build_grid_map_from_array(grid)

    target_dir = Path(directory)
    target_dir.mkdir(parents=True, exist_ok=True)

    safe_name = file_name if file_name.endswith(".csv") else f"{file_name}.csv"
    output_path = target_dir / safe_name

    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerows(np.asarray(grid, dtype=int).tolist())

    return output_path
