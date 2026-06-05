from __future__ import annotations

import unittest
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from aco_path_planning import AcoParams, load_grid_map, solve_path
from aco_path_planning.custom_map import create_empty_grid
from aco_path_planning.visualization import (
    cell_from_click,
    plot_convergence,
    plot_length_comparison,
    plot_success_count,
    render_editor_canvas,
)


class VisualizationTests(unittest.TestCase):
    def setUp(self) -> None:
        grid_map = load_grid_map(PROJECT_ROOT / "data" / "maps" / "easy.csv")
        result = solve_path(grid_map, AcoParams(ant_count=30, iterations=40, random_seed=42))
        self.result = result

    def test_plot_convergence_returns_figure(self) -> None:
        figure = plot_convergence(self.result.history_best_length)
        self.assertIsNotNone(figure)

    def test_plot_length_comparison_returns_figure(self) -> None:
        figure = plot_length_comparison(
            self.result.history_iteration_best_length,
            self.result.history_iteration_mean_length,
        )
        self.assertIsNotNone(figure)

    def test_plot_success_count_returns_figure(self) -> None:
        figure = plot_success_count(self.result.history_success_count)
        self.assertIsNotNone(figure)


if __name__ == "__main__":
    unittest.main()
