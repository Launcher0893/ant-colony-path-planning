from __future__ import annotations

import unittest
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from aco_path_planning.models import AcoParams


class AcoParamsTests(unittest.TestCase):
    def test_validate_rejects_non_positive_ant_count(self) -> None:
        with self.assertRaisesRegex(ValueError, "ant_count"):
            AcoParams(ant_count=0).validate()

    def test_validate_rejects_non_positive_iterations(self) -> None:
        with self.assertRaisesRegex(ValueError, "iterations"):
            AcoParams(iterations=0).validate()

    def test_validate_rejects_negative_alpha(self) -> None:
        with self.assertRaisesRegex(ValueError, "alpha"):
            AcoParams(alpha=-1.0).validate()

    def test_validate_rejects_negative_beta(self) -> None:
        with self.assertRaisesRegex(ValueError, "beta"):
            AcoParams(beta=-0.1).validate()

    def test_validate_rejects_out_of_range_evaporation_rate(self) -> None:
        with self.assertRaisesRegex(ValueError, "evaporation_rate"):
            AcoParams(evaporation_rate=1.0).validate()

    def test_validate_rejects_non_positive_q(self) -> None:
        with self.assertRaisesRegex(ValueError, "pheromone_deposit_q"):
            AcoParams(pheromone_deposit_q=0.0).validate()

    def test_validate_rejects_non_positive_initial_pheromone(self) -> None:
        with self.assertRaisesRegex(ValueError, "initial_pheromone"):
            AcoParams(initial_pheromone=0.0).validate()

    def test_validate_rejects_out_of_range_local_evaporation_rate(self) -> None:
        with self.assertRaisesRegex(ValueError, "local_evaporation_rate"):
            AcoParams(local_evaporation_rate=1.0).validate()

    def test_validate_rejects_negative_elite_weight(self) -> None:
        with self.assertRaisesRegex(ValueError, "elite_weight"):
            AcoParams(elite_weight=-0.1).validate()


if __name__ == "__main__":
    unittest.main()
