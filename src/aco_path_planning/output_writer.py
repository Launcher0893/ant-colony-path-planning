from __future__ import annotations

import json
import math
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt

from .models import AcoParams, GridMap, PlanningResult
from .visualization import (
    format_path_coordinates,
    plot_convergence,
    plot_grid_map,
    plot_length_comparison,
    plot_success_count,
)


def save_planning_artifacts(
    *,
    grid_map: GridMap,
    params: AcoParams,
    result: PlanningResult,
    surface: str,
    output_root: str | Path,
) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    map_name = (grid_map.source.stem if grid_map.source else "unknown_map").replace(" ", "_")
    run_dir = _create_unique_run_dir(Path(output_root), f"{timestamp}_{map_name}")

    path_figure = plot_grid_map(grid_map, result)
    path_figure.savefig(run_dir / "path_plot.png", bbox_inches="tight")
    plt.close(path_figure)

    convergence_figure = plot_convergence(result.history_best_length)
    convergence_figure.savefig(run_dir / "convergence_plot.png", bbox_inches="tight")
    plt.close(convergence_figure)

    comparison_figure = plot_length_comparison(
        result.history_iteration_best_length,
        result.history_iteration_mean_length,
    )
    comparison_figure.savefig(run_dir / "iteration_length_plot.png", bbox_inches="tight")
    plt.close(comparison_figure)

    success_count_figure = plot_success_count(result.history_success_count)
    success_count_figure.savefig(run_dir / "success_count_plot.png", bbox_inches="tight")
    plt.close(success_count_figure)

    (run_dir / "path.txt").write_text(
        format_path_coordinates(result.path),
        encoding="utf-8",
    )

    payload = {
        "map_name": f"{map_name}.csv" if grid_map.source else "unknown_map.csv",
        "map_path": str(grid_map.source) if grid_map.source else None,
        "surface": surface,
        "saved_at": datetime.now().isoformat(timespec="seconds"),
        "found": result.found,
        "path_length": result.path_length,
        "best_iteration": result.best_iteration,
        "path": result.path,
        "message": result.message,
        "runtime_seconds": result.runtime_seconds,
        "total_successful_paths": result.total_successful_paths,
        "params": {
            "ant_count": params.ant_count,
            "iterations": params.iterations,
            "alpha": params.alpha,
            "beta": params.beta,
            "evaporation_rate": params.evaporation_rate,
            "pheromone_deposit_q": params.pheromone_deposit_q,
            "initial_pheromone": params.initial_pheromone,
            "local_evaporation_rate": params.local_evaporation_rate,
            "elite_enabled": params.elite_enabled,
            "elite_weight": params.elite_weight,
            "random_seed": params.random_seed,
        },
        "history_best_length": result.history_best_length,
        "history_iteration_best_length": result.history_iteration_best_length,
        "history_iteration_mean_length": result.history_iteration_mean_length,
        "history_success_count": result.history_success_count,
    }
    (run_dir / "result.json").write_text(
        json.dumps(_json_safe(payload), ensure_ascii=False, indent=2, allow_nan=False),
        encoding="utf-8",
    )

    return run_dir


def _create_unique_run_dir(output_root: Path, directory_name: str) -> Path:
    output_root.mkdir(parents=True, exist_ok=True)

    for sequence in range(1000):
        suffix = "" if sequence == 0 else f"_{sequence}"
        candidate = output_root / f"{directory_name}{suffix}"
        try:
            candidate.mkdir()
            return candidate
        except FileExistsError:
            continue

    raise RuntimeError(f"Could not create a unique output directory under {output_root}.")


def _json_safe(value):
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value
