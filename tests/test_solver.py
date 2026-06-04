from __future__ import annotations

import math
import unittest
from pathlib import Path

import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from aco_path_planning import AcoParams, load_grid_map, solve_path
from aco_path_planning.grid import get_neighbors


class SolverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.project_root = PROJECT_ROOT

    def test_solver_finds_path_on_easy_map(self) -> None:
        grid_map = load_grid_map(self.project_root / "data" / "maps" / "easy.csv")
        params = AcoParams(ant_count=40, iterations=80, random_seed=42)

        result = solve_path(grid_map, params)

        self.assertTrue(result.found)
        self.assertEqual(result.path[0], grid_map.start)
        self.assertEqual(result.path[-1], grid_map.goal)
        self.assertTrue(math.isfinite(result.path_length))

        for current, nxt in zip(result.path, result.path[1:]):
            neighbor_coords = {coordinate for coordinate, _ in get_neighbors(grid_map, current)}
            self.assertIn(nxt, neighbor_coords)

    def test_solver_reports_failure_on_blocked_map(self) -> None:
        grid_map = load_grid_map(self.project_root / "data" / "maps" / "blocked.csv")
        params = AcoParams(ant_count=20, iterations=20, random_seed=42)

        result = solve_path(grid_map, params)

        self.assertFalse(result.found)
        self.assertEqual(result.path, [])
        self.assertTrue(math.isinf(result.path_length))


if __name__ == "__main__":
    unittest.main()
