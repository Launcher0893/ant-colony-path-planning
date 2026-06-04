from __future__ import annotations

from dataclasses import dataclass
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
        if self.ant_count <= 0:
            raise ValueError("ant_count must be greater than 0.")
        if self.iterations <= 0:
            raise ValueError("iterations must be greater than 0.")
        if self.alpha < 0:
            raise ValueError("alpha must be non-negative.")
        if self.beta < 0:
            raise ValueError("beta must be non-negative.")
        if not 0 <= self.evaporation_rate < 1:
            raise ValueError("evaporation_rate must be in [0, 1).")
        if self.pheromone_deposit_q <= 0:
            raise ValueError("pheromone_deposit_q must be greater than 0.")
        if self.initial_pheromone <= 0:
            raise ValueError("initial_pheromone must be greater than 0.")
        if not 0 <= self.local_evaporation_rate < 1:
            raise ValueError("local_evaporation_rate must be in [0, 1).")
        if self.elite_weight < 0:
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
