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


def cells_from_stroke_alpha(
    alpha: np.ndarray,
    cell_px: int,
    rows: int,
    cols: int,
    alpha_threshold: int = 32,
    min_coverage: float = 0.02,
) -> set[tuple[int, int]]:
    """Map a stroke alpha mask (at canvas resolution) to the set of touched cells.

    A cell counts as touched when the fraction of its pixels whose alpha exceeds
    ``alpha_threshold`` is at least ``min_coverage``. The coverage gate ignores
    faint anti-aliased bleed into neighbouring cells so a stroke only paints the
    cells it actually passes through.
    """
    if alpha.ndim != 2:
        raise ValueError("alpha mask must be a 2D array.")
    if cell_px <= 0:
        raise ValueError("cell_px must be positive.")

    touched: set[tuple[int, int]] = set()
    for row in range(rows):
        y0 = row * cell_px
        y1 = y0 + cell_px
        for col in range(cols):
            x0 = col * cell_px
            x1 = x0 + cell_px
            block = alpha[y0:y1, x0:x1]
            if block.size == 0:
                continue
            covered = int(np.count_nonzero(block >= alpha_threshold))
            if covered / block.size >= min_coverage:
                touched.add((row, col))
    return touched


def cells_from_stroke_image(
    image_data,
    cell_px: int,
    rows: int,
    cols: int,
    **kwargs,
) -> set[tuple[int, int]]:
    """Extract touched cells from a drawable-canvas RGBA stroke image.

    ``image_data`` is the (H, W, 4) array returned by ``st_canvas`` holding only
    the drawn strokes (the background grid is not included by the component).
    """
    array = np.asarray(image_data)
    if array.ndim != 3 or array.shape[2] < 4:
        raise ValueError("image_data must be an (H, W, 4) RGBA array.")
    alpha = array[:, :, 3]
    return cells_from_stroke_alpha(alpha, cell_px, rows, cols, **kwargs)


def _pick_single_cell(cells: set[tuple[int, int]]) -> tuple[int, int]:
    """Pick one representative cell (nearest the centroid) for start/goal strokes."""
    cell_list = list(cells)
    mean_row = sum(row for row, _ in cell_list) / len(cell_list)
    mean_col = sum(col for _, col in cell_list) / len(cell_list)
    return min(
        cell_list,
        key=lambda rc: ((rc[0] - mean_row) ** 2 + (rc[1] - mean_col) ** 2, rc),
    )


def apply_brush_to_cells(
    grid: np.ndarray,
    cells: set[tuple[int, int]],
    brush: str,
) -> np.ndarray:
    """Paint a set of cells with the selected brush, keeping start/goal unique.

    Obstacle and erase brushes paint every touched cell. Start and goal are
    single-valued, so a multi-cell stroke collapses to one representative cell.
    Mutates ``grid`` in place and returns it.
    """
    if brush not in BRUSH_VALUES:
        raise ValueError(f"Unknown brush '{brush}'.")
    if not cells:
        return grid

    if brush in (BRUSH_START, BRUSH_GOAL):
        row, col = _pick_single_cell(cells)
        apply_brush(grid, row, col, brush)
    else:
        for row, col in cells:
            if 0 <= row < grid.shape[0] and 0 <= col < grid.shape[1]:
                apply_brush(grid, row, col, brush)
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
    raw_grid = np.asarray(grid)
    if raw_grid.ndim != 2 or raw_grid.size == 0:
        raise ValueError("Map must be a non-empty 2D grid.")
    if not np.issubdtype(raw_grid.dtype, np.integer):
        raise ValueError("Map grid values must be integers.")
    invalid_values = set(np.unique(raw_grid).tolist()) - {EMPTY, OBSTACLE, START, GOAL}
    if invalid_values:
        sample = sorted(invalid_values)[0]
        raise ValueError(f"Unsupported cell value {sample}. Allowed values: 0, 1, 2, 3.")
    raw_grid = raw_grid.astype(np.int8, copy=True)
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


def _resolve_unique_stem(stem: str, existing_names: list[str]) -> str:
    existing_stems = {Path(name).stem.lower() for name in existing_names}
    candidate = stem
    sequence = 1
    while candidate.lower() in existing_stems:
        candidate = f"{stem}_{sequence}"
        sequence += 1
    return candidate


def resolve_map_filename(
    user_name: str,
    existing_names: list[str],
    now: datetime | None = None,
) -> str:
    """Decide the final ``<name>.csv`` filename from optional user input."""
    cleaned = sanitize_map_name(user_name) if user_name else ""
    stem = _resolve_unique_stem(cleaned, existing_names) if cleaned else generate_custom_map_name(existing_names, now=now)
    return f"{stem}.csv"


def _safe_csv_filename(file_name: str) -> str:
    raw_name = file_name.strip()
    if not raw_name:
        raise ValueError("Map file name must not be empty.")

    candidate = Path(raw_name)
    if candidate.is_absolute() or candidate.name != raw_name:
        raise ValueError("Map file name must not include a path.")
    if candidate.suffix and candidate.suffix != ".csv":
        raise ValueError("Map file name must use the .csv extension.")

    stem = candidate.stem if candidate.suffix else candidate.name
    if not stem or sanitize_map_name(stem) != stem:
        raise ValueError("Map file name contains unsafe characters.")
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

    safe_name = _safe_csv_filename(file_name)
    output_path = target_dir / safe_name

    with output_path.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerows(np.asarray(grid, dtype=int).tolist())

    return output_path
