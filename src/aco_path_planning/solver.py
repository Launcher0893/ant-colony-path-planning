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

    for iteration in range(1, params.iterations + 1):
        successful_paths: list[tuple[list[Coordinate], float]] = []

        for _ in range(params.ant_count):
            candidate_path = _build_ant_path(grid_map, pheromone, params, rng)
            if not candidate_path:
                continue

            candidate_length = path_length(candidate_path)
            successful_paths.append((candidate_path, candidate_length))

            if candidate_length < best_length:
                best_path = candidate_path
                best_length = candidate_length
                best_iteration = iteration

        pheromone[grid_map.walkable_mask] *= 1.0 - params.evaporation_rate

        for candidate_path, candidate_length in successful_paths:
            deposit = params.pheromone_deposit_q / max(candidate_length, 1e-9)
            for row, col in candidate_path:
                pheromone[row, col] += deposit

        history_best_length.append(best_length)

    runtime_seconds = time.perf_counter() - started_at

    if best_path:
        return PlanningResult(
            found=True,
            path=best_path,
            path_length=best_length,
            best_iteration=best_iteration,
            history_best_length=history_best_length,
            runtime_seconds=runtime_seconds,
            message="Path found successfully.",
        )

    return PlanningResult(
        found=False,
        path=[],
        path_length=math.inf,
        best_iteration=None,
        history_best_length=history_best_length,
        runtime_seconds=runtime_seconds,
        message="No feasible path found under the current map and parameters.",
    )


def _build_ant_path(
    grid_map: GridMap,
    pheromone: np.ndarray,
    params: AcoParams,
    rng: np.random.Generator,
) -> list[Coordinate] | None:
    current = grid_map.start
    goal = grid_map.goal
    visited = {current}
    path = [current]
    max_steps = grid_map.rows * grid_map.cols

    for _ in range(max_steps):
        if current == goal:
            return path

        feasible_neighbors = [
            (coordinate, move_cost)
            for coordinate, move_cost in get_neighbors(grid_map, current)
            if coordinate not in visited
        ]

        if not feasible_neighbors:
            return None

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

    return path if current == goal else None


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
