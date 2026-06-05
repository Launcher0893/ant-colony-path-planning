from __future__ import annotations

import tempfile
import unittest
from datetime import datetime
from pathlib import Path
import sys

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from aco_path_planning.custom_map import (
    BRUSH_ERASE,
    BRUSH_GOAL,
    BRUSH_OBSTACLE,
    BRUSH_START,
    EMPTY,
    GOAL,
    OBSTACLE,
    START,
    apply_brush,
    build_grid_map_from_array,
    count_markers,
    create_empty_grid,
    generate_custom_map_name,
    is_ready_to_save,
    resolve_map_filename,
    sanitize_map_name,
    save_custom_map,
)
from aco_path_planning.map_loader import load_grid_map


class CreateEmptyGridTests(unittest.TestCase):
    def test_creates_grid_with_default_start_and_goal(self) -> None:
        grid = create_empty_grid(5, 6)

        self.assertEqual(grid.shape, (5, 6))
        self.assertEqual(int(grid[0, 0]), START)
        self.assertEqual(int(grid[4, 5]), GOAL)
        self.assertEqual(count_markers(grid), (1, 1))

    def test_rejects_too_small_grid(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least 2 x 2"):
            create_empty_grid(1, 4)


class ApplyBrushTests(unittest.TestCase):
    def test_obstacle_brush_paints_cell(self) -> None:
        grid = create_empty_grid(4, 4)
        apply_brush(grid, 1, 1, BRUSH_OBSTACLE)
        self.assertEqual(int(grid[1, 1]), OBSTACLE)

    def test_start_brush_is_unique(self) -> None:
        grid = create_empty_grid(4, 4)
        # Default start is at (0, 0); painting a new start should clear the old one.
        apply_brush(grid, 2, 2, BRUSH_START)
        self.assertEqual(int(grid[2, 2]), START)
        self.assertEqual(int(grid[0, 0]), EMPTY)
        self.assertEqual(count_markers(grid)[0], 1)

    def test_goal_brush_is_unique(self) -> None:
        grid = create_empty_grid(4, 4)
        apply_brush(grid, 1, 2, BRUSH_GOAL)
        self.assertEqual(int(grid[1, 2]), GOAL)
        self.assertEqual(count_markers(grid)[1], 1)

    def test_erase_brush_clears_cell(self) -> None:
        grid = create_empty_grid(4, 4)
        apply_brush(grid, 1, 1, BRUSH_OBSTACLE)
        apply_brush(grid, 1, 1, BRUSH_ERASE)
        self.assertEqual(int(grid[1, 1]), EMPTY)

    def test_rejects_unknown_brush(self) -> None:
        grid = create_empty_grid(4, 4)
        with self.assertRaisesRegex(ValueError, "Unknown brush"):
            apply_brush(grid, 0, 1, "rainbow")

    def test_rejects_out_of_bounds_cell(self) -> None:
        grid = create_empty_grid(4, 4)
        with self.assertRaisesRegex(ValueError, "outside the grid"):
            apply_brush(grid, 9, 9, BRUSH_OBSTACLE)


class ReadinessTests(unittest.TestCase):
    def test_fresh_grid_is_ready(self) -> None:
        self.assertTrue(is_ready_to_save(create_empty_grid(4, 4)))

    def test_grid_without_start_is_not_ready(self) -> None:
        grid = create_empty_grid(4, 4)
        apply_brush(grid, 0, 0, BRUSH_ERASE)
        self.assertFalse(is_ready_to_save(grid))


class NamingTests(unittest.TestCase):
    def test_sanitize_strips_unsafe_characters(self) -> None:
        self.assertEqual(sanitize_map_name(" my map!.csv "), "my_map")

    def test_sanitize_handles_path_like_input(self) -> None:
        self.assertEqual(sanitize_map_name("../../etc/passwd"), "passwd")

    def test_generate_name_uses_timestamp_and_sequence(self) -> None:
        now = datetime(2026, 6, 5, 12, 30, 0)
        name = generate_custom_map_name([], now=now)
        self.assertEqual(name, "custom_20260605_123000_1")

    def test_generate_name_increments_sequence(self) -> None:
        now = datetime(2026, 6, 5, 12, 30, 0)
        existing = ["custom_20260605_123000_1.csv", "easy.csv"]
        name = generate_custom_map_name(existing, now=now)
        self.assertEqual(name, "custom_20260605_123000_2")

    def test_resolve_uses_user_name_when_given(self) -> None:
        self.assertEqual(resolve_map_filename("My Arena", [], now=datetime(2026, 6, 5)), "My_Arena.csv")

    def test_resolve_falls_back_to_generated_name(self) -> None:
        now = datetime(2026, 6, 5, 12, 30, 0)
        self.assertEqual(resolve_map_filename("", [], now=now), "custom_20260605_123000_1.csv")


class BuildAndSaveTests(unittest.TestCase):
    def test_build_grid_map_from_array_matches_loader(self) -> None:
        grid = create_empty_grid(4, 4)
        apply_brush(grid, 1, 1, BRUSH_OBSTACLE)
        grid_map = build_grid_map_from_array(grid)

        self.assertEqual(grid_map.start, (0, 0))
        self.assertEqual(grid_map.goal, (3, 3))
        self.assertEqual(int(grid_map.grid[1, 1]), 1)

    def test_build_grid_map_rejects_missing_goal(self) -> None:
        grid = create_empty_grid(4, 4)
        apply_brush(grid, 3, 3, BRUSH_ERASE)  # remove the goal
        with self.assertRaisesRegex(ValueError, "exactly one goal"):
            build_grid_map_from_array(grid)

    def test_save_custom_map_round_trips_through_loader(self) -> None:
        grid = create_empty_grid(5, 5)
        apply_brush(grid, 2, 2, BRUSH_OBSTACLE)
        apply_brush(grid, 1, 3, BRUSH_OBSTACLE)

        with tempfile.TemporaryDirectory() as temp_dir:
            saved_path = save_custom_map(grid, "round_trip", temp_dir)
            self.assertTrue(saved_path.exists())
            self.assertEqual(saved_path.name, "round_trip.csv")

            reloaded = load_grid_map(saved_path)

        self.assertEqual(reloaded.start, (0, 0))
        self.assertEqual(reloaded.goal, (4, 4))
        self.assertEqual(int(reloaded.grid[2, 2]), 1)
        self.assertEqual(int(reloaded.grid[1, 3]), 1)

    def test_save_custom_map_refuses_invalid_grid(self) -> None:
        grid = create_empty_grid(4, 4)
        apply_brush(grid, 0, 0, BRUSH_ERASE)  # remove start
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(ValueError, "exactly one start"):
                save_custom_map(grid, "bad", temp_dir)

    def test_save_custom_map_adds_csv_extension(self) -> None:
        grid = create_empty_grid(3, 3)
        with tempfile.TemporaryDirectory() as temp_dir:
            saved_path = save_custom_map(grid, "no_ext", temp_dir)
            self.assertEqual(saved_path.suffix, ".csv")


if __name__ == "__main__":
    unittest.main()
