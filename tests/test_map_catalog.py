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
from aco_path_planning.map_catalog import (
    CUSTOM_CATEGORY,
    get_map_metadata,
    get_sorted_map_files,
)


EXPECTED_MAPS = {
    "easy.csv": {"size": (6, 6), "start": (5, 0), "goal": (0, 5), "found": True},
    "easy_alt.csv": {"size": (6, 6), "start": (5, 5), "goal": (0, 0), "found": True},
    "medium.csv": {"size": (10, 10), "start": (8, 1), "goal": (1, 8), "found": True},
    "medium_alt.csv": {"size": (10, 10), "start": (0, 1), "goal": (9, 8), "found": True},
    "blocked.csv": {"size": (5, 5), "start": (4, 0), "goal": (0, 4), "found": False},
    "blocked_alt.csv": {"size": (5, 5), "start": (0, 0), "goal": (4, 4), "found": False},
    "hard_corridor.csv": {"size": (11, 12), "start": (9, 1), "goal": (1, 10), "found": True},
    "hard_corridor_alt.csv": {"size": (11, 12), "start": (1, 1), "goal": (9, 10), "found": True},
    "maze_small.csv": {"size": (10, 10), "start": (9, 1), "goal": (1, 8), "found": True},
    "maze_small_alt.csv": {"size": (10, 10), "start": (4, 0), "goal": (0, 8), "found": True},
    "dense_obstacles.csv": {"size": (11, 12), "start": (5, 0), "goal": (0, 11), "found": True},
    "dense_obstacles_alt.csv": {"size": (11, 12), "start": (10, 1), "goal": (2, 9), "found": True},
    "large_sparse.csv": {"size": (15, 15), "start": (13, 1), "goal": (1, 13), "found": True},
    "large_sparse_alt.csv": {"size": (15, 15), "start": (13, 7), "goal": (0, 7), "found": True},
    "large_dense.csv": {"size": (15, 15), "start": (12, 1), "goal": (1, 13), "found": True},
    "large_dense_alt.csv": {"size": (15, 15), "start": (13, 12), "goal": (1, 2), "found": True},
    "no_solution_large.csv": {"size": (10, 10), "start": (9, 0), "goal": (4, 8), "found": False},
    "no_solution_large_alt.csv": {"size": (10, 10), "start": (0, 9), "goal": (8, 2), "found": False},
}


class MapCatalogTests(unittest.TestCase):
    def test_map_catalog_matches_expected_layout(self) -> None:
        for file_name, spec in EXPECTED_MAPS.items():
            with self.subTest(file_name=file_name):
                grid_map = load_grid_map(PROJECT_ROOT / "data" / "maps" / file_name)
                self.assertEqual((grid_map.rows, grid_map.cols), spec["size"])
                self.assertEqual(grid_map.start, spec["start"])
                self.assertEqual(grid_map.goal, spec["goal"])
                metadata = get_map_metadata(file_name)
                self.assertEqual(metadata.start, spec["start"])
                self.assertEqual(metadata.goal, spec["goal"])

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

    def test_analysis_maps_have_non_flat_history_best_length(self) -> None:
        params = AcoParams(
            ant_count=12,
            iterations=100,
            alpha=1.0,
            beta=2.0,
            evaporation_rate=0.3,
            local_evaporation_rate=0.05,
            elite_enabled=False,
            elite_weight=0.0,
            random_seed=42,
        )
        analysis_maps = [
            "easy_alt.csv",
            "medium_alt.csv",
            "large_sparse.csv",
            "large_dense_alt.csv",
        ]

        for file_name in analysis_maps:
            with self.subTest(file_name=file_name):
                grid_map = load_grid_map(PROJECT_ROOT / "data" / "maps" / file_name)
                result = solve_path(grid_map, params)
                finite = [value for value in result.history_best_length if math.isfinite(value)]
                unique_values = []
                for value in finite:
                    if not unique_values or unique_values[-1] != value:
                        unique_values.append(value)

                self.assertTrue(result.found)
                self.assertGreaterEqual(len(unique_values), 2)
                self.assertIsNotNone(result.best_iteration)
                self.assertGreater(result.best_iteration, 1)


class CustomMapFallbackTests(unittest.TestCase):
    def test_unknown_map_gets_custom_fallback_metadata(self) -> None:
        metadata = get_map_metadata("custom_20260605_123000_1.csv")
        self.assertEqual(metadata.category, CUSTOM_CATEGORY)
        self.assertIn("custom", metadata.display_name)

    def test_known_map_still_returns_curated_metadata(self) -> None:
        metadata = get_map_metadata("easy.csv")
        self.assertEqual(metadata.category, "easy")

    def test_sorted_files_place_custom_maps_last(self) -> None:
        ordered = get_sorted_map_files(["custom_demo.csv", "easy.csv", "medium.csv"])
        self.assertEqual(ordered[-1], "custom_demo.csv")


if __name__ == "__main__":
    unittest.main()
