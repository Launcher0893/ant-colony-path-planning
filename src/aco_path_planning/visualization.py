from __future__ import annotations

import math

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap

from .models import Coordinate, GridMap, PlanningResult


def plot_grid_map(
    grid_map: GridMap,
    result: PlanningResult | None = None,
    title: str = "ACO Path Planning Result",
    figure_size: tuple[float, float] = (7.0, 7.0),
    compact: bool = False,
):
    figure, axis = plt.subplots(figsize=figure_size)

    display_grid = np.zeros_like(grid_map.grid, dtype=float)
    display_grid[grid_map.grid == 1] = 1.0

    color_map = ListedColormap(["#f8f8f8", "#30343f"])
    axis.imshow(display_grid, cmap=color_map, origin="upper")

    axis.set_title(title)
    if compact:
        axis.set_xlabel("")
        axis.set_ylabel("")
    else:
        axis.set_xlabel("Column")
        axis.set_ylabel("Row")
    axis.set_xticks(np.arange(-0.5, grid_map.cols, 1), minor=True)
    axis.set_yticks(np.arange(-0.5, grid_map.rows, 1), minor=True)
    axis.grid(which="minor", color="#d6d6d6", linestyle="-", linewidth=0.8)
    axis.tick_params(which="minor", bottom=False, left=False)

    start_row, start_col = grid_map.start
    goal_row, goal_col = grid_map.goal
    axis.scatter(start_col, start_row, c="#1f77b4", s=120, marker="o", label="Start")
    axis.scatter(goal_col, goal_row, c="#d62728", s=120, marker="*", label="Goal")

    if result and result.path:
        x_coords = [coordinate[1] for coordinate in result.path]
        y_coords = [coordinate[0] for coordinate in result.path]
        axis.plot(x_coords, y_coords, color="#2ca02c", linewidth=2.5, label="Best Path")

    axis.legend(loc="upper right", fontsize="small" if compact else None)
    figure.tight_layout()
    return figure


def plot_convergence(history_best_length: list[float]):
    figure, axis = plt.subplots(figsize=(7, 4))

    y_values = [value if math.isfinite(value) else np.nan for value in history_best_length]
    axis.plot(range(1, len(y_values) + 1), y_values, color="#ff7f0e", linewidth=2)
    axis.set_title("Best Path Length by Iteration")
    axis.set_xlabel("Iteration")
    axis.set_ylabel("Best Path Length")
    axis.grid(alpha=0.3)

    figure.tight_layout()
    return figure


def format_path_coordinates(path: list[Coordinate]) -> str:
    if not path:
        return "[]"
    return " -> ".join(f"({row}, {col})" for row, col in path)
