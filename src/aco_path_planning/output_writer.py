from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt

from .models import AcoParams, GridMap, PlanningResult
from .visualization import format_path_coordinates, plot_convergence, plot_grid_map


def save_planning_artifacts(
    *,
    grid_map: GridMap,
    params: AcoParams,
    result: PlanningResult,
    surface: str,
    output_root: str | Path,
) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    map_name = (grid_map.source.stem if grid_map.source else "unknown_map").replace(" ", "_")
    run_dir = Path(output_root) / f"{timestamp}_{map_name}"
    run_dir.mkdir(parents=True, exist_ok=True)

    path_figure = plot_grid_map(grid_map, result)
    path_figure.savefig(run_dir / "path_plot.png", bbox_inches="tight")
    plt.close(path_figure)

    convergence_figure = plot_convergence(result.history_best_length)
    convergence_figure.savefig(run_dir / "convergence_plot.png", bbox_inches="tight")
    plt.close(convergence_figure)

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
        "params": {
            "ant_count": params.ant_count,
            "iterations": params.iterations,
            "alpha": params.alpha,
            "beta": params.beta,
            "evaporation_rate": params.evaporation_rate,
            "pheromone_deposit_q": params.pheromone_deposit_q,
            "initial_pheromone": params.initial_pheromone,
            "random_seed": params.random_seed,
        },
        "history_best_length": result.history_best_length,
    }
    (run_dir / "result.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return run_dir
