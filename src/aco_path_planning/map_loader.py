from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

from .models import GridMap

VALID_CELL_VALUES = {0, 1, 2, 3}


def build_grid_map_from_cells(
    raw_grid: np.ndarray,
    source: Path | None = None,
) -> GridMap:
    """Validate a raw 0/1/2/3 integer grid and build an immutable GridMap.

    Shared by both CSV loading and in-memory custom maps so the start/goal and
    normalization rules stay in one place.
    """
    if raw_grid.ndim != 2 or raw_grid.size == 0:
        raise ValueError("Map must be a non-empty 2D grid.")

    invalid_values = set(np.unique(raw_grid).tolist()) - VALID_CELL_VALUES
    if invalid_values:
        sample = sorted(invalid_values)[0]
        raise ValueError(
            f"Unsupported cell value {sample}. Allowed values: 0, 1, 2, 3."
        )

    start_positions = np.argwhere(raw_grid == 2)
    goal_positions = np.argwhere(raw_grid == 3)

    if len(start_positions) != 1:
        raise ValueError("Map must contain exactly one start cell with value 2.")
    if len(goal_positions) != 1:
        raise ValueError("Map must contain exactly one goal cell with value 3.")

    normalized_grid = np.where(raw_grid == 1, 1, 0).astype(np.int8)
    start = tuple(int(value) for value in start_positions[0])
    goal = tuple(int(value) for value in goal_positions[0])

    return GridMap(grid=normalized_grid, start=start, goal=goal, source=source)


def load_grid_map(path: str | Path) -> GridMap:
    map_path = Path(path)
    if not map_path.exists():
        raise FileNotFoundError(f"Map file not found: {map_path}")

    rows: list[list[int]] = []
    with map_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        for row_index, raw_row in enumerate(reader, start=1):
            if not raw_row or all(cell.strip() == "" for cell in raw_row):
                continue

            parsed_row: list[int] = []
            for col_index, cell in enumerate(raw_row, start=1):
                value_text = cell.strip()
                try:
                    value = int(value_text)
                except ValueError as exc:
                    raise ValueError(
                        f"Invalid cell value '{value_text}' at row {row_index}, "
                        f"column {col_index}."
                    ) from exc
                if value not in VALID_CELL_VALUES:
                    raise ValueError(
                        f"Unsupported cell value {value} at row {row_index}, "
                        f"column {col_index}. Allowed values: 0, 1, 2, 3."
                    )
                parsed_row.append(value)
            rows.append(parsed_row)

    if not rows:
        raise ValueError("Map file is empty.")

    expected_width = len(rows[0])
    if expected_width == 0:
        raise ValueError("Map file contains an empty row.")

    for index, row in enumerate(rows[1:], start=2):
        if len(row) != expected_width:
            raise ValueError(
                f"Map must be rectangular. Row 1 has width {expected_width}, "
                f"but row {index} has width {len(row)}."
            )

    raw_grid = np.array(rows, dtype=np.int8)
    return build_grid_map_from_cells(raw_grid, source=map_path)


def discover_map_files(directory: str | Path) -> list[Path]:
    root = Path(directory)
    if not root.exists():
        return []
    return sorted(path for path in root.glob("*.csv") if path.is_file())
