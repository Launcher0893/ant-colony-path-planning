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


EXPECTED_MAPS = {
    "easy.csv": {"size": (6, 6), "start": (5, 0), "goal": (0, 5), "found": True},
    "medium.csv": {"size": (10, 10), "start": (8, 1), "goal": (1, 8), "found": True},
    "blocked.csv": {"size": (5, 5), "start": (4, 0), "goal": (0, 4), "found": False},
    "hard_corridor.csv": {"size": (11, 12), "start": (9, 1), "goal": (1, 10), "found": True},
    "maze_small.csv": {"size": (10, 10), "start": (9, 1), "goal": (1, 8), "found": True},
    "dense_obstacles.csv": {"size": (11, 12), "start": (5, 0), "goal": (0, 11), "found": True},
    "large_sparse.csv": {"size": (15, 15), "start": (13, 1), "goal": (1, 13), "found": True},
    "large_dense.csv": {"size": (15, 15), "start": (12, 1), "goal": (1, 13), "found": True},
    "no_solution_large.csv": {"size": (10, 10), "start": (9, 0), "goal": (4, 8), "found": False},
}


class MapCatalogTests(unittest.TestCase):
    def test_map_catalog_matches_expected_layout(self) -> None:
        for file_name, spec in EXPECTED_MAPS.items():
            with self.subTest(file_name=file_name):
                grid_map = load_grid_map(PROJECT_ROOT / "data" / "maps" / file_name)
                self.assertEqual((grid_map.rows, grid_map.cols), spec["size"])
                self.assertEqual(grid_map.start, spec["start"])
                self.assertEqual(grid_map.goal, spec["goal"])

    def test_map_catalog_solvability_matches_expectation(self) -> None:
        params = AcoParams(ant_count=50, iterations=100, random_seed=42)
        for file_name, spec in EXPECTED_MAPS.items():
            with self.subTest(file_name=file_name):
                grid_map = load_grid_map(PROJECT_ROOT / "data" / "maps" / file_name)
                result = solve_path(grid_map, params)
                self.assertEqual(result.found, spec["found"])
                if spec["found"]:
                    self.assertTrue(math.isfinite(result.path_length))
                else:
                    self.assertTrue(math.isinf(result.path_length))


if __name__ == "__main__":
    unittest.main()
