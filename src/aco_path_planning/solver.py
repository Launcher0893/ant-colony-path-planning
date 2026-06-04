from __future__ import annotations

import math
import time

import numpy as np

from .grid import distance_to_goal, get_neighbors, path_length
from .models import AcoParams, Coordinate, GridMap, PlanningResult


def solve_path(grid_map: GridMap, params: AcoParams) -> PlanningResult:
    params.validate()
    started_at = time.perf_counter()

    rng = np.random.default_rng(params.random_seed)
    pheromone = np.zeros((grid_map.rows, grid_map.cols), dtype=float)
    pheromone[grid_map.walkable_mask] = params.initial_pheromone

    best_path: list[Coordinate] = []
    best_length = math.inf
    best_iteration: int | None = None
    history_best_length: list[float] = []
    history_success_count: list[int] = []
    total_successful_paths = 0

    for iteration in range(1, params.iterations + 1):
        successful_paths: list[tuple[list[Coordinate], float]] = []

        for _ in range(params.ant_count):
            candidate_path, reached_goal = _build_ant_path(grid_map, pheromone, params, rng)
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

            if candidate_length < best_length:
                best_path = candidate_path
                best_length = candidate_length
                best_iteration = iteration

        pheromone[grid_map.walkable_mask] *= 1.0 - params.evaporation_rate

        for candidate_path, candidate_length in successful_paths:
            deposit = params.pheromone_deposit_q / max(candidate_length, 1e-9)
            for row, col in candidate_path:
                pheromone[row, col] += deposit

        if params.elite_enabled and best_path:
            elite_deposit = (
                params.elite_weight * params.pheromone_deposit_q / max(best_length, 1e-9)
            )
            for row, col in best_path:
                pheromone[row, col] += elite_deposit

        history_best_length.append(best_length)
        history_success_count.append(len(successful_paths))

    runtime_seconds = time.perf_counter() - started_at

    if best_path:
        return PlanningResult(
            found=True,
            path=best_path,
            path_length=best_length,
            best_iteration=best_iteration,
            history_best_length=history_best_length,
            history_success_count=history_success_count,
            total_successful_paths=total_successful_paths,
            runtime_seconds=runtime_seconds,
            message="Path found successfully.",
        )

    return PlanningResult(
        found=False,
        path=[],
        path_length=math.inf,
        best_iteration=None,
        history_best_length=history_best_length,
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
    current = grid_map.start
    goal = grid_map.goal
    visited = {current}
    path = [current]
    max_steps = grid_map.rows * grid_map.cols

    for _ in range(max_steps):
        if current == goal:
            return path, True

        feasible_neighbors = [
            (coordinate, move_cost)
            for coordinate, move_cost in get_neighbors(grid_map, current)
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
    raw_weights = np.zeros(len(feasible_neighbors), dtype=float)

    for index, (coordinate, _) in enumerate(feasible_neighbors):
        row, col = coordinate
        tau = max(pheromone[row, col], 1e-12)
        eta = 1.0 / (distance_to_goal(coordinate, goal) + 1e-6)
        raw_weights[index] = (tau ** alpha) * (eta ** beta)

    total_weight = float(np.sum(raw_weights))
    if not math.isfinite(total_weight) or total_weight <= 0:
        return np.full(len(feasible_neighbors), 1.0 / len(feasible_neighbors))

    return raw_weights / total_weight
