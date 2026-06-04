from __future__ import annotations

import argparse
import json
import tempfile
import unittest
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from aco_path_planning.cli import build_params


class CliTests(unittest.TestCase):
    def test_build_params_uses_json_file_and_cli_overrides(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            param_path = Path(temp_dir) / "params.json"
            param_path.write_text(
                json.dumps(
                    {
                        "ant_count": 12,
                        "iterations": 34,
                        "alpha": 1.5,
                        "beta": 2.5,
                        "evaporation_rate": 0.25,
                        "pheromone_deposit_q": 88.0,
                        "initial_pheromone": 0.8,
                        "local_evaporation_rate": 0.12,
                        "elite_enabled": True,
                        "elite_weight": 1.7,
                        "random_seed": 7,
                    }
                ),
                encoding="utf-8",
            )

            args = argparse.Namespace(
                param_file=str(param_path),
                ant_count=None,
                iterations=55,
                alpha=None,
                beta=None,
                evaporation_rate=None,
                pheromone_deposit_q=99.0,
                initial_pheromone=None,
                local_evaporation_rate=None,
                elite_weight=3.0,
                disable_elite=True,
                random_seed=None,
            )

            params = build_params(args)

        self.assertEqual(params.ant_count, 12)
        self.assertEqual(params.iterations, 55)
        self.assertEqual(params.alpha, 1.5)
        self.assertEqual(params.pheromone_deposit_q, 99.0)
        self.assertEqual(params.local_evaporation_rate, 0.12)
        self.assertEqual(params.elite_weight, 3.0)
        self.assertFalse(params.elite_enabled)
        self.assertEqual(params.random_seed, 7)


if __name__ == "__main__":
    unittest.main()
