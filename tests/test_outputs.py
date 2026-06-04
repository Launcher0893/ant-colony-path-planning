from __future__ import annotations

import json
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
            self.assertTrue((saved_dir / "path.txt").exists())
            self.assertTrue((saved_dir / "result.json").exists())

            payload = json.loads((saved_dir / "result.json").read_text(encoding="utf-8"))
            self.assertEqual(payload["surface"], "cli")
            self.assertTrue(payload["found"])
            self.assertEqual(payload["map_name"], "easy.csv")
            self.assertIn("total_successful_paths", payload)
            self.assertIn("history_success_count", payload)
            self.assertEqual(payload["params"]["elite_enabled"], self.params.elite_enabled)


if __name__ == "__main__":
    unittest.main()
