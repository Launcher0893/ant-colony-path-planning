from __future__ import annotations

import csv
import tempfile
import unittest
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from aco_path_planning import AcoParams, load_grid_map, solve_path
from aco_path_planning.output_writer import save_planning_artifacts
import summarize_results


class SummarizeResultsTests(unittest.TestCase):
    def test_collect_results_and_write_summary(self) -> None:
        grid_map = load_grid_map(PROJECT_ROOT / "data" / "maps" / "easy.csv")
        params = AcoParams(ant_count=30, iterations=50, random_seed=42)
        result = solve_path(grid_map, params)

        with tempfile.TemporaryDirectory() as temp_dir:
            output_root = Path(temp_dir) / "outputs"
            save_planning_artifacts(
                grid_map=grid_map,
                params=params,
                result=result,
                surface="cli",
                output_root=output_root,
            )
            result_dir = next(output_root.iterdir())
            (result_dir / "experiment_label.txt").write_text("baseline", encoding="utf-8")

            rows = summarize_results.collect_results(output_root)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["map_name"], "easy.csv")
            self.assertEqual(rows[0]["surface"], "cli")
            self.assertEqual(rows[0]["experiment_label"], "baseline")
            self.assertIn("total_successful_paths", rows[0])
            self.assertIn("avg_success_count", rows[0])

            summary_path = Path(temp_dir) / "summary.csv"
            summarize_results.write_summary(summary_path, rows)

            self.assertTrue(summary_path.exists())
            with summary_path.open("r", encoding="utf-8", newline="") as handle:
                csv_rows = list(csv.DictReader(handle))

        self.assertEqual(len(csv_rows), 1)
        self.assertEqual(csv_rows[0]["map_name"], "easy.csv")
        self.assertIn("avg_success_count", csv_rows[0])


if __name__ == "__main__":
    unittest.main()
