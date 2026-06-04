from __future__ import annotations

import unittest

import numpy as np

from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from aco_path_planning.grid import get_neighbors, path_length
from aco_path_planning.models import GridMap


class GridTests(unittest.TestCase):
    def test_diagonal_corner_cutting_is_blocked(self) -> None:
        grid_map = GridMap(
            grid=np.array(
                [
                    [0, 1, 0],
                    [1, 0, 0],
                    [0, 0, 0],
                ],
                dtype=np.int8,
            ),
            start=(0, 0),
            goal=(2, 2),
        )

        neighbors = get_neighbors(grid_map, (1, 1))
        neighbor_coords = {coord for coord, _ in neighbors}

        self.assertNotIn((0, 0), neighbor_coords)

    def test_path_length_uses_diagonal_cost(self) -> None:
        path = [(0, 0), (0, 1), (1, 2)]
        self.assertAlmostEqual(path_length(path), 1.0 + 2 ** 0.5)


if __name__ == "__main__":
    unittest.main()
