from __future__ import annotations

import argparse
import csv
import random
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
import sys

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from aco_path_planning.config import DEFAULT_GENERATED_MAP_DIR
from aco_path_planning.custom_map import sanitize_map_name


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate benchmark grid maps.")
    parser.add_argument("--mode", choices=["maze", "dense", "large_sparse"], required=True)
    parser.add_argument("--rows", type=int, default=15)
    parser.add_argument("--cols", type=int, default=15)
    parser.add_argument("--density", type=float, default=0.28)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--name", required=True, help="Output filename without extension.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    rng = random.Random(args.seed)
    grid = build_grid(args.mode, args.rows, args.cols, args.density, rng)
    output_dir = DEFAULT_GENERATED_MAP_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{safe_output_stem(args.name)}.csv"
    write_csv(output_path, grid)
    print(output_path)
    return 0


def build_grid(
    mode: str,
    rows: int,
    cols: int,
    density: float,
    rng: random.Random,
) -> list[list[int]]:
    if rows < 2 or cols < 2:
        raise ValueError("Generated maps must be at least 2 x 2.")

    grid = [[0 for _ in range(cols)] for _ in range(rows)]
    start = (0, 0)
    goal = (rows - 1, cols - 1)

    if mode == "maze":
        for row in range(rows):
            for col in range(cols):
                if row in (0, rows - 1) or col in (0, cols - 1):
                    continue
                if (row + col) % 2 == 0 and rng.random() < 0.55:
                    grid[row][col] = 1
        carve_path(grid, start, goal)
    elif mode == "dense":
        for row in range(rows):
            for col in range(cols):
                if rng.random() < density:
                    grid[row][col] = 1
        carve_path(grid, start, goal)
    elif mode == "large_sparse":
        sparse_density = min(density, 0.18)
        for row in range(rows):
            for col in range(cols):
                if rng.random() < sparse_density:
                    grid[row][col] = 1
        carve_path(grid, start, goal)

    grid[start[0]][start[1]] = 2
    grid[goal[0]][goal[1]] = 3
    return grid


def carve_path(grid: list[list[int]], start: tuple[int, int], goal: tuple[int, int]) -> None:
    row, col = start
    goal_row, goal_col = goal
    while row < goal_row:
        grid[row][col] = 0
        row += 1
    while col < goal_col:
        grid[row][col] = 0
        col += 1
    grid[goal_row][goal_col] = 0


def write_csv(path: Path, grid: list[list[int]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerows(grid)


def safe_output_stem(name: str) -> str:
    stem = sanitize_map_name(name)
    if not stem:
        raise ValueError("Output map name must contain at least one safe character.")
    return stem


if __name__ == "__main__":
    raise SystemExit(main())
