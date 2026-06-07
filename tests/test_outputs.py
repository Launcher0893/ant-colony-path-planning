from __future__ import annotations

import json
import math
import tempfile
import unittest
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from aco_path_planning import AcoParams, load_grid_map, solve_path
from aco_path_planning.output_writer import save_planning_artifacts


class OutputWriterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.grid_map = load_grid_map(PROJECT_ROOT / "data" / "maps" / "easy.csv")
        self.params = AcoParams(ant_count=40, iterations=80, random_seed=42)
        self.result = solve_path(self.grid_map, self.params)

    def test_save_planning_artifacts_writes_expected_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            saved_dir = save_planning_artifacts(
                grid_map=self.grid_map,
                params=self.params,
                result=self.result,
                surface="cli",
                output_root=temp_dir,
            )

            self.assertTrue((saved_dir / "path_plot.png").exists())
            self.assertTrue((saved_dir / "convergence_plot.png").exists())
            self.assertTrue((saved_dir / "iteration_length_plot.png").exists())
            self.assertTrue((saved_dir / "success_count_plot.png").exists())
            self.assertTrue((saved_dir / "path.txt").exists())
            self.assertTrue((saved_dir / "result.json").exists())

            payload = json.loads((saved_dir / "result.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["surface"], "cli")
            self.assertTrue(payload["found"])
            self.assertEqual(payload["map_name"], "easy.csv")
            self.assertIn("total_successful_paths", payload)
            self.assertIn("history_success_count", payload)
            self.assertIn("history_iteration_best_length", payload)
            self.assertIn("history_iteration_mean_length", payload)
            self.assertEqual(payload["params"]["elite_enabled"], self.params.elite_enabled)

    def test_save_planning_artifacts_writes_standard_json_for_failure(self) -> None:
        grid_map = load_grid_map(PROJECT_ROOT / "data" / "maps" / "blocked.csv")
        params = AcoParams(ant_count=10, iterations=10, random_seed=42)
        result = solve_path(grid_map, params)
        self.assertFalse(result.found)
        self.assertTrue(math.isinf(result.path_length))

        with tempfile.TemporaryDirectory() as temp_dir:
            saved_dir = save_planning_artifacts(
                grid_map=grid_map,
                params=params,
                result=result,
                surface="cli",
                output_root=temp_dir,
            )
            raw_json = (saved_dir / "result.json").read_text(encoding="utf-8")
            self.assertNotIn("Infinity", raw_json)
            self.assertNotIn("NaN", raw_json)

            payload = json.loads(
                raw_json,
                parse_constant=lambda constant: self.fail(f"non-standard JSON: {constant}"),
            )

        self.assertIsNone(payload["path_length"])
        self.assertTrue(all(value is None for value in payload["history_best_length"]))

    def test_save_planning_artifacts_uses_unique_run_directories(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            first_dir = save_planning_artifacts(
                grid_map=self.grid_map,
                params=self.params,
                result=self.result,
                surface="cli",
                output_root=temp_dir,
            )
            second_dir = save_planning_artifacts(
                grid_map=self.grid_map,
                params=self.params,
                result=self.result,
                surface="cli",
                output_root=temp_dir,
            )

        self.assertNotEqual(first_dir, second_dir)


if __name__ == "__main__":
    unittest.main()
