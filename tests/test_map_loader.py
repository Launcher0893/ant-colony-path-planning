from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
import sys

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from aco_path_planning.map_loader import load_grid_map


class MapLoaderTests(unittest.TestCase):
    def test_load_grid_map_reads_start_goal_and_obstacles(self) -> None:
        content = "2,0,1\n0,0,0\n1,0,3\n"
        with tempfile.TemporaryDirectory() as temp_dir:
            map_path = Path(temp_dir) / "sample.csv"
            map_path.write_text(content, encoding="utf-8")

            grid_map = load_grid_map(map_path)

        self.assertEqual(grid_map.start, (0, 0))
        self.assertEqual(grid_map.goal, (2, 2))
        self.assertEqual(grid_map.grid.tolist(), [[0, 0, 1], [0, 0, 0], [1, 0, 0]])

    def test_load_grid_map_rejects_multiple_starts(self) -> None:
        content = "2,0,2\n0,0,0\n1,0,3\n"
        with tempfile.TemporaryDirectory() as temp_dir:
            map_path = Path(temp_dir) / "sample.csv"
            map_path.write_text(content, encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "exactly one start"):
                load_grid_map(map_path)

    def test_load_grid_map_rejects_non_rectangular_input(self) -> None:
        content = "2,0,1\n0,3\n"
        with tempfile.TemporaryDirectory() as temp_dir:
            map_path = Path(temp_dir) / "sample.csv"
            map_path.write_text(content, encoding="utf-8")

            with self.assertRaisesRegex(ValueError, "rectangular"):
                load_grid_map(map_path)


if __name__ == "__main__":
    unittest.main()
