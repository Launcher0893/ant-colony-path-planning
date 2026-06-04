from __future__ import annotations

import math

from .models import Coordinate, GridMap

ORTHOGONAL_COST = 1.0
DIAGONAL_COST = math.sqrt(2.0)
NEIGHBOR_OFFSETS = (
    (-1, -1, DIAGONAL_COST),
    (-1, 0, ORTHOGONAL_COST),
    (-1, 1, DIAGONAL_COST),
    (0, -1, ORTHOGONAL_COST),
    (0, 1, ORTHOGONAL_COST),
    (1, -1, DIAGONAL_COST),
    (1, 0, ORTHOGONAL_COST),
    (1, 1, DIAGONAL_COST),
)


def is_in_bounds(grid_map: GridMap, coordinate: Coordinate) -> bool:
    row, col = coordinate
    return 0 <= row < grid_map.rows and 0 <= col < grid_map.cols


def is_walkable(grid_map: GridMap, coordinate: Coordinate) -> bool:
    if not is_in_bounds(grid_map, coordinate):
        return False
    row, col = coordinate
    return bool(grid_map.grid[row, col] == 0)


def get_neighbors(grid_map: GridMap, coordinate: Coordinate) -> list[tuple[Coordinate, float]]:
    row, col = coordinate
    neighbors: list[tuple[Coordinate, float]] = []

    for row_offset, col_offset, move_cost in NEIGHBOR_OFFSETS:
        next_coord = (row + row_offset, col + col_offset)
        if not is_walkable(grid_map, next_coord):
            continue

        if row_offset != 0 and col_offset != 0:
            if not _can_move_diagonally(grid_map, coordinate, next_coord):
                continue

        neighbors.append((next_coord, move_cost))

    return neighbors


def path_length(path: list[Coordinate]) -> float:
    if len(path) < 2:
        return 0.0

    total = 0.0
    for current, nxt in zip(path, path[1:]):
        row_delta = abs(current[0] - nxt[0])
        col_delta = abs(current[1] - nxt[1])
        if row_delta == 1 and col_delta == 1:
            total += DIAGONAL_COST
        else:
            total += ORTHOGONAL_COST
    return total


def distance_to_goal(coordinate: Coordinate, goal: Coordinate) -> float:
    row_delta = abs(coordinate[0] - goal[0])
    col_delta = abs(coordinate[1] - goal[1])
    diagonal_steps = min(row_delta, col_delta)
    straight_steps = max(row_delta, col_delta) - diagonal_steps
    return diagonal_steps * DIAGONAL_COST + straight_steps * ORTHOGONAL_COST


def _can_move_diagonally(
    grid_map: GridMap,
    current: Coordinate,
    nxt: Coordinate,
) -> bool:
    current_row, current_col = current
    next_row, next_col = nxt

    adjacent_one = (current_row, next_col)
    adjacent_two = (next_row, current_col)

    return is_walkable(grid_map, adjacent_one) and is_walkable(grid_map, adjacent_two)
