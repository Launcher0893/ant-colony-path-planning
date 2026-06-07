from __future__ import annotations

import sys
import unittest
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from aco_path_planning.webapp import _should_use_drag_canvas


class WebappTests(unittest.TestCase):
    def test_drag_canvas_is_used_when_available_and_not_disabled(self) -> None:
        self.assertTrue(_should_use_drag_canvas(True, False))

    def test_drag_canvas_is_skipped_when_disabled(self) -> None:
        self.assertFalse(_should_use_drag_canvas(True, True))

    def test_drag_canvas_is_skipped_when_unavailable(self) -> None:
        self.assertFalse(_should_use_drag_canvas(False, False))


if __name__ == "__main__":
    unittest.main()
