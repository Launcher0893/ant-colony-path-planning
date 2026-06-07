from __future__ import annotations

from dataclasses import dataclass
import math
from pathlib import Path

import numpy as np

Coordinate = tuple[int, int]


@dataclass(frozen=True)
class GridMap:
    grid: np.ndarray
    start: Coordinate
    goal: Coordinate
    source: Path | None = None

    @property
    def rows(self) -> int:
        return int(self.grid.shape[0])

    @property
    def cols(self) -> int:
        return int(self.grid.shape[1])

    @property
    def walkable_mask(self) -> np.ndarray:
        return self.grid == 0


@dataclass(frozen=True)
class AcoParams:
    ant_count: int = 50
    iterations: int = 100
    alpha: float = 1.0
    beta: float = 4.0
    evaporation_rate: float = 0.3
    pheromone_deposit_q: float = 100.0
    initial_pheromone: float = 1.0
    local_evaporation_rate: float = 0.05
    elite_enabled: bool = True
    elite_weight: float = 2.0
    random_seed: int | None = 42

    def validate(self) -> None:
        ant_count = _require_int("ant_count", self.ant_count)
        iterations = _require_int("iterations", self.iterations)
        alpha = _require_finite_number("alpha", self.alpha)
        beta = _require_finite_number("beta", self.beta)
        evaporation_rate = _require_finite_number("evaporation_rate", self.evaporation_rate)
        pheromone_deposit_q = _require_finite_number(
            "pheromone_deposit_q",
            self.pheromone_deposit_q,
        )
        initial_pheromone = _require_finite_number(
            "initial_pheromone",
            self.initial_pheromone,
        )
        local_evaporation_rate = _require_finite_number(
            "local_evaporation_rate",
            self.local_evaporation_rate,
        )
        elite_weight = _require_finite_number("elite_weight", self.elite_weight)

        if not isinstance(self.elite_enabled, bool):
            raise ValueError("elite_enabled must be a boolean.")
        if self.random_seed is not None:
            _require_int("random_seed", self.random_seed)

        if ant_count <= 0:
            raise ValueError("ant_count must be greater than 0.")
        if iterations <= 0:
            raise ValueError("iterations must be greater than 0.")
        if alpha < 0:
            raise ValueError("alpha must be non-negative.")
        if beta < 0:
            raise ValueError("beta must be non-negative.")
        if not 0 <= evaporation_rate < 1:
            raise ValueError("evaporation_rate must be in [0, 1).")
        if pheromone_deposit_q <= 0:
            raise ValueError("pheromone_deposit_q must be greater than 0.")
        if initial_pheromone <= 0:
            raise ValueError("initial_pheromone must be greater than 0.")
        if not 0 <= local_evaporation_rate < 1:
            raise ValueError("local_evaporation_rate must be in [0, 1).")
        if elite_weight < 0:
            raise ValueError("elite_weight must be non-negative.")


@dataclass(frozen=True)
class PlanningResult:
    found: bool
    path: list[Coordinate]
    path_length: float
    best_iteration: int | None
    history_best_length: list[float]
    history_iteration_best_length: list[float]
    history_iteration_mean_length: list[float]
    history_success_count: list[int]
    total_successful_paths: int
    runtime_seconds: float
    message: str


def _require_int(name: str, value: object) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer.")
    return value


def _require_finite_number(name: str, value: object) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number.")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be a finite number.")
    return number
