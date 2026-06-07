from __future__ import annotations

"""命令行运行逻辑。

本模块负责把命令行参数、默认 JSON 参数和地图文件组合起来，然后调用核心求解器。
它不直接实现算法，只负责用户输入、结果打印、可选绘图和可选保存。
"""

import argparse
import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt

from .config import DEFAULT_CLI_OUTPUT_DIR, DEFAULT_MAP_DIR, DEFAULT_PARAM_FILE
from .map_loader import load_grid_map
from .models import AcoParams
from .output_writer import save_planning_artifacts
from .solver import solve_path
from .visualization import format_path_coordinates, plot_convergence, plot_grid_map


def parse_args() -> argparse.Namespace:
    """定义并解析 CLI 参数。

    默认地图为 `data/maps/easy.csv`；默认参数文件为 `config/aco_defaults.json`。
    """
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
    # CLI 中使用短名 rho / q，对应模型字段 evaporation_rate / pheromone_deposit_q。
    parser.add_argument("--rho", dest="evaporation_rate", type=float)
    parser.add_argument("--q", dest="pheromone_deposit_q", type=float)
    parser.add_argument("--initial-pheromone", type=float)
    parser.add_argument("--local-rho", dest="local_evaporation_rate", type=float)
    parser.add_argument("--elite-weight", type=float)
    parser.add_argument(
        "--disable-elite",
        action="store_true",
        help="Disable elite pheromone reinforcement.",
    )
    parser.add_argument("--seed", dest="random_seed", type=int)
    parser.add_argument(
        "--save-output",
        action="store_true",
        help="Save path plot, convergence plot, path text, and result metadata to data/outputs.",
    )
    parser.add_argument(
        "--output-dir",
        default=str(DEFAULT_CLI_OUTPUT_DIR),
        help="Root directory used when --save-output is enabled.",
    )
    parser.add_argument(
        "--no-plot",
        action="store_true",
        help="Skip matplotlib windows and only print the result.",
    )
    return parser.parse_args()


def main() -> int:
    """CLI 主流程，返回进程退出码。

    返回 0 表示正常完成；输入文件、参数文件或参数值有问题时返回 1。
    """
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

    print(f"Runtime seconds: {result.runtime_seconds:.4f}")
    print(f"Successful paths: {result.total_successful_paths}")

    if args.save_output:
        # 保存完整实验产物，包含图片、路径文本和 result.json。
        saved_dir = save_planning_artifacts(
            grid_map=grid_map,
            params=params,
            result=result,
            surface="cli",
            output_root=args.output_dir,
        )
        print(f"Saved output: {saved_dir}")

    if not args.no_plot:
        # 交互式运行时展示两张最常用图；更完整的四张图会在保存输出时生成。
        plot_grid_map(grid_map, result)
        plot_convergence(result.history_best_length)
        plt.show()

    return 0


def build_params(args: argparse.Namespace) -> AcoParams:
    """根据默认参数文件和命令行覆盖项构造 `AcoParams`。

    合并顺序：
    1. 读取参数 JSON；文件不存在时使用 `AcoParams` 代码默认值。
    2. 用命令行中非 None 的字段覆盖。
    3. 如果传入 `--disable-elite`，强制关闭精英强化。
    """
    base_params = _load_params_from_file(args.param_file)
    overrides = {
        "ant_count": getattr(args, "ant_count", None),
        "iterations": getattr(args, "iterations", None),
        "alpha": getattr(args, "alpha", None),
        "beta": getattr(args, "beta", None),
        "evaporation_rate": getattr(args, "evaporation_rate", None),
        "pheromone_deposit_q": getattr(args, "pheromone_deposit_q", None),
        "initial_pheromone": getattr(args, "initial_pheromone", None),
        "local_evaporation_rate": getattr(args, "local_evaporation_rate", None),
        "elite_weight": getattr(args, "elite_weight", None),
        "random_seed": getattr(args, "random_seed", None),
    }
    merged = {**base_params, **{key: value for key, value in overrides.items() if value is not None}}
    if getattr(args, "disable_elite", False):
        merged["elite_enabled"] = False
    return AcoParams(**merged)


def _load_params_from_file(path: str | Path) -> dict[str, int | float | None]:
    """读取参数 JSON，并只保留 `AcoParams` 已知字段。

    这样配置文件中即使出现额外字段，也不会直接传入 dataclass 构造函数导致异常。
    """
    param_path = Path(path)
    if not param_path.exists():
        # 没有参数文件时允许程序继续运行，使用模型内置默认值。
        return AcoParams().__dict__.copy()

    with param_path.open("r", encoding="utf-8") as handle:
        raw_data = json.load(handle)

    defaults = AcoParams().__dict__.copy()
    for key in defaults:
        if key in raw_data:
            defaults[key] = raw_data[key]
    return defaults
