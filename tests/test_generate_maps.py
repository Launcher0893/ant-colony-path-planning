from __future__ import annotations

import csv
import random
import tempfile
import unittest
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import generate_maps


class GenerateMapsTests(unittest.TestCase):
    def test_build_grid_creates_single_start_and_goal_for_each_mode(self) -> None:
        for mode in ("maze", "dense", "large_sparse"):
            with self.subTest(mode=mode):
                grid = generate_maps.build_grid(
                    mode=mode,
                    rows=12,
                    cols=12,
                    density=0.25,
                    rng=random.Random(42),
                )

                self.assertEqual(len(grid), 12)
                self.assertTrue(all(len(row) == 12 for row in grid))
                flattened = [cell for row in grid for cell in row]
                self.assertEqual(flattened.count(2), 1)
                self.assertEqual(flattened.count(3), 1)

    def test_write_csv_persists_generated_grid(self) -> None:
        grid = generate_maps.build_grid(
            mode="dense",
            rows=8,
            cols=8,
            density=0.2,
            rng=random.Random(7),
        )

        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "generated.csv"
            generate_maps.write_csv(output_path, grid)

            self.assertTrue(output_path.exists())
            with output_path.open("r", encoding="utf-8", newline="") as handle:
                rows = list(csv.reader(handle))

        self.assertEqual(len(rows), 8)
        self.assertTrue(all(len(row) == 8 for row in rows))

    def test_build_grid_rejects_too_small_dimensions(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least 2 x 2"):
            generate_maps.build_grid(
                mode="dense",
                rows=1,
                cols=1,
                density=0.2,
                rng=random.Random(7),
            )

    def test_safe_output_stem_strips_path_components(self) -> None:
        self.assertEqual(generate_maps.safe_output_stem("../bad name"), "bad_name")


if __name__ == "__main__":
    unittest.main()
