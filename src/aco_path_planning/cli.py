from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt

from .config import DEFAULT_MAP_DIR, DEFAULT_PARAM_FILE
from .map_loader import load_grid_map
from .models import AcoParams
from .solver import solve_path
from .visualization import format_path_coordinates, plot_convergence, plot_grid_map


def parse_args() -> argparse.Namespace:
    default_map = DEFAULT_MAP_DIR / "easy.csv"

    parser = argparse.ArgumentParser(
        description="Grid-based path planning with ant colony optimization."
    )
    parser.add_argument("--map", dest="map_path", default=str(default_map))
    parser.add_argument("--params", dest="param_file", default=str(DEFAULT_PARAM_FILE))
    parser.add_argument("--ants", dest="ant_count", type=int)
    parser.add_argument("--iterations", type=int)
    parser.add_argument("--alpha", type=float)
    parser.add_argument("--beta", type=float)
    parser.add_argument("--rho", dest="evaporation_rate", type=float)
    parser.add_argument("--q", dest="pheromone_deposit_q", type=float)
    parser.add_argument("--initial-pheromone", type=float)
    parser.add_argument("--seed", dest="random_seed", type=int)
    parser.add_argument(
        "--no-plot",
        action="store_true",
        help="Skip matplotlib windows and only print the result.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    try:
        params = build_params(args)
        grid_map = load_grid_map(args.map_path)
        result = solve_path(grid_map, params)
    except (FileNotFoundError, ValueError, json.JSONDecodeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print(f"Map: {Path(args.map_path).resolve()}")
    print(f"Start: {grid_map.start}")
    print(f"Goal: {grid_map.goal}")
    print(f"Found path: {'yes' if result.found else 'no'}")
    print(f"Message: {result.message}")

    if result.found:
        print(f"Best iteration: {result.best_iteration}")
        print(f"Path length: {result.path_length:.3f}")
        print(f"Path coordinates: {format_path_coordinates(result.path)}")
    else:
        print("Path length: inf")
        print("Path coordinates: []")

    if not args.no_plot:
        plot_grid_map(grid_map, result)
        plot_convergence(result.history_best_length)
        plt.show()

    return 0


def build_params(args: argparse.Namespace) -> AcoParams:
    base_params = _load_params_from_file(args.param_file)
    overrides = {
        "ant_count": args.ant_count,
        "iterations": args.iterations,
        "alpha": args.alpha,
        "beta": args.beta,
        "evaporation_rate": args.evaporation_rate,
        "pheromone_deposit_q": args.pheromone_deposit_q,
        "initial_pheromone": args.initial_pheromone,
        "random_seed": args.random_seed,
    }
    merged = {**base_params, **{key: value for key, value in overrides.items() if value is not None}}
    return AcoParams(**merged)


def _load_params_from_file(path: str | Path) -> dict[str, int | float | None]:
    param_path = Path(path)
    if not param_path.exists():
        return AcoParams().__dict__.copy()

    with param_path.open("r", encoding="utf-8") as handle:
        raw_data = json.load(handle)

    defaults = AcoParams().__dict__.copy()
    for key in defaults:
        if key in raw_data:
            defaults[key] = raw_data[key]
    return defaults
