from __future__ import annotations

"""纯网格运动规则。

本模块不包含蚁群算法，只定义栅格地图上“哪些格子能走、一步代价是多少、路径长度
如何计算”。求解器、测试和报告中的路径合法性都应以这里为准。
"""

import math

from .models import Coordinate, GridMap

# 正交移动（上下左右）代价。
ORTHOGONAL_COST = 1.0
# 对角移动代价，对应几何距离 sqrt(2)。
DIAGONAL_COST = math.sqrt(2.0)
# 8 邻域偏移，每项为 (row_offset, col_offset, move_cost)。
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
    """判断坐标是否落在地图范围内。"""
    row, col = coordinate
    return 0 <= row < grid_map.rows and 0 <= col < grid_map.cols


def is_walkable(grid_map: GridMap, coordinate: Coordinate) -> bool:
    """判断坐标是否可通行。

    越界坐标直接视为不可通行；合法范围内只有 `grid == 0` 的格子可走。
    """
    if not is_in_bounds(grid_map, coordinate):
        return False
    row, col = coordinate
    return bool(grid_map.grid[row, col] == 0)


def get_neighbors(grid_map: GridMap, coordinate: Coordinate) -> list[tuple[Coordinate, float]]:
    """返回当前位置所有合法邻居及移动代价。

    对角移动会额外检查防穿角规则，避免路径从两个障碍物的角点中穿过。
    """
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
    """计算路径长度。

    只允许相邻的正交步或对角步；如果路径中出现跳格或原地不动，说明上游生成了
    非法路径，应立即报错而不是给出误导性的长度。
    """
    if len(path) < 2:
        return 0.0

    total = 0.0
    for current, nxt in zip(path, path[1:]):
        row_delta = abs(current[0] - nxt[0])
        col_delta = abs(current[1] - nxt[1])
        if row_delta == 1 and col_delta == 1:
            total += DIAGONAL_COST
        elif (row_delta == 1 and col_delta == 0) or (row_delta == 0 and col_delta == 1):
            total += ORTHOGONAL_COST
        else:
            raise ValueError(f"Invalid path step from {current} to {nxt}.")
    return total


def distance_to_goal(coordinate: Coordinate, goal: Coordinate) -> float:
    """计算到终点的 octile 距离。

    在 8 邻域中，最理想的走法会优先走对角线，再走直线，因此这里比曼哈顿距离
    更贴近真实路径代价。求解器用它构造启发函数 eta。
    """
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
    """检查对角移动是否满足防穿角规则。

    从 current 斜走到 nxt 时，两个相邻的正交格必须都可通行。例如从 (1, 1)
    走到 (0, 0)，需要 (1, 0) 和 (0, 1) 都不是障碍。
    """
    current_row, current_col = current
    next_row, next_col = nxt

    adjacent_one = (current_row, next_col)
    adjacent_two = (next_row, current_col)

    return is_walkable(grid_map, adjacent_one) and is_walkable(grid_map, adjacent_two)
