from __future__ import annotations

"""蚁群路径规划求解器。

本模块是项目核心算法实现。它接收已经校验并归一化的 `GridMap` 和 `AcoParams`，
返回包含最终路径、运行耗时和多条收敛历史的 `PlanningResult`。
"""

import math
import time

import numpy as np

from .grid import distance_to_goal, get_neighbors, path_length
from .models import AcoParams, Coordinate, GridMap, PlanningResult


def solve_path(grid_map: GridMap, params: AcoParams) -> PlanningResult:
    """在给定栅格地图上执行蚁群路径规划。

    参数：
    - `grid_map`：已经由加载器或自定义地图模块构造好的地图对象。
    - `params`：蚁群算法参数，进入主循环前会统一校验。

    返回：
    - `PlanningResult`：包含是否找到路径、最优路径、路径长度、收敛曲线和耗时。
    """
    params.validate()
    started_at = time.perf_counter()

    # 所有随机选择都由同一个生成器驱动。固定 random_seed 后，实验更容易复现。
    rng = np.random.default_rng(params.random_seed)

    # 信息素矩阵与地图同形；障碍格保持 0，可通行格初始化为 tau0。
    pheromone = np.zeros((grid_map.rows, grid_map.cols), dtype=float)
    pheromone[grid_map.walkable_mask] = params.initial_pheromone

    # 全局最优状态，随着迭代逐步更新。
    best_path: list[Coordinate] = []
    best_length = math.inf
    best_iteration: int | None = None

    # 收敛分析所需历史曲线，每轮都会追加一个值。
    history_best_length: list[float] = []
    history_iteration_best_length: list[float] = []
    history_iteration_mean_length: list[float] = []
    history_success_count: list[int] = []
    total_successful_paths = 0

    for iteration in range(1, params.iterations + 1):
        # 本轮所有成功到达终点的路径，元素为 (路径坐标列表, 路径长度)。
        successful_paths: list[tuple[list[Coordinate], float]] = []

        for _ in range(params.ant_count):
            candidate_path, reached_goal = _build_ant_path(grid_map, pheromone, params, rng)
            # 局部更新对成功和失败路径都执行，用于降低后续蚂蚁过度跟随同一路径的概率。
            _apply_local_pheromone_update(
                pheromone=pheromone,
                path=candidate_path,
                initial_pheromone=params.initial_pheromone,
                local_evaporation_rate=params.local_evaporation_rate,
            )

            if not reached_goal:
                continue

            candidate_length = path_length(candidate_path)
            successful_paths.append((candidate_path, candidate_length))
            total_successful_paths += 1

            # 只要发现更短路径，立即刷新全局最优，并记录出现的迭代轮次。
            if candidate_length < best_length:
                best_path = candidate_path
                best_length = candidate_length
                best_iteration = iteration

        # 全局挥发：旧信息逐轮衰减，避免早期路径永远占优势。
        pheromone[grid_map.walkable_mask] *= 1.0 - params.evaporation_rate

        # 普通沉积：路径越短，Q / L 越大，因此短路径获得更多信息素。
        for candidate_path, candidate_length in successful_paths:
            deposit = params.pheromone_deposit_q / max(candidate_length, 1e-9)
            for row, col in candidate_path:
                pheromone[row, col] += deposit

        # 精英强化：对当前全局最优路径额外沉积，提升收敛速度。
        if params.elite_enabled and best_path:
            elite_deposit = (
                params.elite_weight * params.pheromone_deposit_q / max(best_length, 1e-9)
            )
            for row, col in best_path:
                pheromone[row, col] += elite_deposit

        if successful_paths:
            iteration_lengths = [candidate_length for _, candidate_length in successful_paths]
            history_iteration_best_length.append(min(iteration_lengths))
            history_iteration_mean_length.append(sum(iteration_lengths) / len(iteration_lengths))
        else:
            # 本轮没有任何蚂蚁成功时，本轮最优/均值记为 inf，绘图时会转成 NaN 断开曲线。
            history_iteration_best_length.append(math.inf)
            history_iteration_mean_length.append(math.inf)

        history_best_length.append(best_length)
        history_success_count.append(len(successful_paths))

    runtime_seconds = time.perf_counter() - started_at

    if best_path:
        # 成功时返回最优路径和所有历史指标。
        return PlanningResult(
            found=True,
            path=best_path,
            path_length=best_length,
            best_iteration=best_iteration,
            history_best_length=history_best_length,
            history_iteration_best_length=history_iteration_best_length,
            history_iteration_mean_length=history_iteration_mean_length,
            history_success_count=history_success_count,
            total_successful_paths=total_successful_paths,
            runtime_seconds=runtime_seconds,
            message="Path found successfully.",
        )

    # 无解或参数下未搜索到路径时，路径为空、长度为 inf，但历史曲线仍保留。
    return PlanningResult(
        found=False,
        path=[],
        path_length=math.inf,
        best_iteration=None,
        history_best_length=history_best_length,
        history_iteration_best_length=history_iteration_best_length,
        history_iteration_mean_length=history_iteration_mean_length,
        history_success_count=history_success_count,
        total_successful_paths=total_successful_paths,
        runtime_seconds=runtime_seconds,
        message="No feasible path found under the current map and parameters.",
    )


def _build_ant_path(
    grid_map: GridMap,
    pheromone: np.ndarray,
    params: AcoParams,
    rng: np.random.Generator,
) -> tuple[list[Coordinate], bool]:
    """构建单只蚂蚁的一条候选路径。

    返回 `(path, reached_goal)`。即使失败，也会返回已经走过的部分路径，供局部信息素
    更新使用。
    """
    current = grid_map.start
    goal = grid_map.goal
    visited = {current}
    path = [current]
    # 最多访问 rows * cols 个格子，避免在复杂地图中出现无限循环。
    max_steps = grid_map.rows * grid_map.cols

    for _ in range(max_steps):
        if current == goal:
            return path, True

        feasible_neighbors = [
            (coordinate, move_cost)
            for coordinate, move_cost in get_neighbors(grid_map, current)
            # 不重复访问已经走过的格子，减少原地兜圈。
            if coordinate not in visited
        ]

        if not feasible_neighbors:
            return path, False

        weights = _calculate_weights(
            feasible_neighbors=feasible_neighbors,
            goal=goal,
            pheromone=pheromone,
            alpha=params.alpha,
            beta=params.beta,
        )
        next_index = int(rng.choice(len(feasible_neighbors), p=weights))
        next_coordinate = feasible_neighbors[next_index][0]

        # 更新路径状态。
        path.append(next_coordinate)
        visited.add(next_coordinate)
        current = next_coordinate

    return path, current == goal


def _apply_local_pheromone_update(
    *,
    pheromone: np.ndarray,
    path: list[Coordinate],
    initial_pheromone: float,
    local_evaporation_rate: float,
) -> None:
    """对单只蚂蚁走过的路径执行局部信息素更新。

    公式：tau <- (1 - local_rho) * tau + local_rho * tau0。
    local_rho 为 0 时等价于关闭局部更新。
    """
    if local_evaporation_rate <= 0:
        return

    for row, col in path:
        pheromone[row, col] = (
            (1.0 - local_evaporation_rate) * pheromone[row, col]
            + local_evaporation_rate * initial_pheromone
        )


def _calculate_weights(
    feasible_neighbors: list[tuple[Coordinate, float]],
    goal: Coordinate,
    pheromone: np.ndarray,
    alpha: float,
    beta: float,
) -> np.ndarray:
    """计算候选邻居的选择概率。

    每个候选格的原始权重为 tau^alpha * eta^beta，其中 eta 是到终点距离的倒数。
    返回值是可直接传给 `numpy.random.Generator.choice(..., p=weights)` 的概率数组。
    """
    raw_weights = np.zeros(len(feasible_neighbors), dtype=float)

    for index, (coordinate, _) in enumerate(feasible_neighbors):
        row, col = coordinate
        # 信息素下限避免 tau 接近 0 时幂运算得到全 0 权重。
        tau = max(pheromone[row, col], 1e-12)
        # 加 1e-6 防止候选格恰好为终点时除零。
        eta = 1.0 / (distance_to_goal(coordinate, goal) + 1e-6)
        raw_weights[index] = (tau ** alpha) * (eta ** beta)

    total_weight = float(np.sum(raw_weights))
    if not math.isfinite(total_weight) or total_weight <= 0:
        # 极端数值场景下退化为均匀选择，保证算法继续运行。
        return np.full(len(feasible_neighbors), 1.0 / len(feasible_neighbors))

    return raw_weights / total_weight
