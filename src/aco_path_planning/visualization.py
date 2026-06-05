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


def plot_length_comparison(
    history_iteration_best_length: list[float],
    history_iteration_mean_length: list[float],
):
    figure, axis = plt.subplots(figsize=(7, 4))

    best_values = [value if math.isfinite(value) else np.nan for value in history_iteration_best_length]
    mean_values = [value if math.isfinite(value) else np.nan for value in history_iteration_mean_length]
    x_axis = range(1, len(best_values) + 1)
    axis.plot(x_axis, best_values, color="#1f77b4", linewidth=2, label="Iteration Best Length")
    axis.plot(x_axis, mean_values, color="#2ca02c", linewidth=2, label="Iteration Mean Length")
    axis.set_title("Iteration Path Lengths")
    axis.set_xlabel("Iteration")
    axis.set_ylabel("Path Length")
    axis.grid(alpha=0.3)
    axis.legend(loc="upper right")

    figure.tight_layout()
    return figure


def plot_success_count(history_success_count: list[int]):
    figure, axis = plt.subplots(figsize=(7, 4))

    axis.plot(
        range(1, len(history_success_count) + 1),
        history_success_count,
        color="#d62728",
        linewidth=2,
    )
    axis.set_title("Successful Paths by Iteration")
    axis.set_xlabel("Iteration")
    axis.set_ylabel("Successful Path Count")
    axis.grid(alpha=0.3)

    figure.tight_layout()
    return figure


def format_path_coordinates(path: list[Coordinate]) -> str:
    if not path:
        return "[]"
    return " -> ".join(f"({row}, {col})" for row, col in path)


# Cell colors for the interactive editor canvas, keyed by raw grid value.
_EDITOR_CELL_COLORS = {
    0: (248, 248, 248),  # empty
    1: (48, 52, 63),     # obstacle
    2: (31, 119, 180),   # start
    3: (214, 39, 40),    # goal
}
_EDITOR_GRID_LINE_COLOR = (200, 200, 200)


def render_editor_canvas(grid: np.ndarray, cell_px: int = 32):
    """Render the editable grid as a PIL image with one square per cell.

    Returns a PIL.Image. Click coordinates from the image map back to a cell via
    ``cell_from_click``: row = y // cell_px, col = x // cell_px. Drawn at native
    resolution so the click-to-cell mapping stays exact (no display scaling).
    """
    from PIL import Image, ImageDraw

    rows, cols = int(grid.shape[0]), int(grid.shape[1])
    width = cols * cell_px
    height = rows * cell_px
    image = Image.new("RGB", (width, height), color=(255, 255, 255))
    draw = ImageDraw.Draw(image)

    for row in range(rows):
        for col in range(cols):
            value = int(grid[row, col])
            color = _EDITOR_CELL_COLORS.get(value, _EDITOR_CELL_COLORS[0])
            x0 = col * cell_px
            y0 = row * cell_px
            draw.rectangle([x0, y0, x0 + cell_px - 1, y0 + cell_px - 1], fill=color)

    for row in range(rows + 1):
        y = min(row * cell_px, height - 1)
        draw.line([(0, y), (width, y)], fill=_EDITOR_GRID_LINE_COLOR, width=1)
    for col in range(cols + 1):
        x = min(col * cell_px, width - 1)
        draw.line([(x, 0), (x, height)], fill=_EDITOR_GRID_LINE_COLOR, width=1)

    return image


def cell_from_click(x: float, y: float, cell_px: int, rows: int, cols: int) -> Coordinate | None:
    """Convert a click position on the editor canvas to a (row, col) cell.

    Returns None when the click falls outside the grid bounds.
    """
    col = int(x // cell_px)
    row = int(y // cell_px)
    if 0 <= row < rows and 0 <= col < cols:
        return (row, col)
    return None
