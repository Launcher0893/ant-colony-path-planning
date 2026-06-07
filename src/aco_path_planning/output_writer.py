from __future__ import annotations

"""实验结果输出保存。

本模块把一次规划运行保存成一组可复现、可分析的产物，包括图片、路径文本和
结构化 JSON。CLI 和 Streamlit 都复用这里的保存逻辑。
"""

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
    """保存一次规划运行的全部产物，并返回输出目录。

    参数：
    - `grid_map`：本次运行使用的地图。
    - `params`：本次运行使用的 ACO 参数，会完整写入 `result.json`。
    - `result`：求解器输出，提供路径、曲线和耗时。
    - `surface`：来源界面，例如 `cli` 或 `streamlit`。
    - `output_root`：输出根目录，例如 `data/outputs/cli`。
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    map_name = (grid_map.source.stem if grid_map.source else "unknown_map").replace(" ", "_")
    run_dir = _create_unique_run_dir(Path(output_root), f"{timestamp}_{map_name}")

    # 1. 最终路径图。
    path_figure = plot_grid_map(grid_map, result)
    path_figure.savefig(run_dir / "path_plot.png", bbox_inches="tight")
    plt.close(path_figure)

    # 2. 历史全局最优收敛图。
    convergence_figure = plot_convergence(result.history_best_length)
    convergence_figure.savefig(run_dir / "convergence_plot.png", bbox_inches="tight")
    plt.close(convergence_figure)

    # 3. 本轮最优和本轮平均路径长度对比图。
    comparison_figure = plot_length_comparison(
        result.history_iteration_best_length,
        result.history_iteration_mean_length,
    )
    comparison_figure.savefig(run_dir / "iteration_length_plot.png", bbox_inches="tight")
    plt.close(comparison_figure)

    # 4. 每轮成功路径数量曲线。
    success_count_figure = plot_success_count(result.history_success_count)
    success_count_figure.savefig(run_dir / "success_count_plot.png", bbox_inches="tight")
    plt.close(success_count_figure)

    # 5. 文本路径，便于直接复制到报告或控制台查看。
    (run_dir / "path.txt").write_text(
        format_path_coordinates(result.path),
        encoding="utf-8",
    )

    # 6. 结构化结果。字段尽量完整，便于后续汇总脚本复现实验配置。
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
    """创建唯一输出目录。

    即使同一秒内多次保存同一张地图，也会通过 `_1`、`_2` 后缀避免覆盖。
    """
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
    """递归转换 JSON 不支持的非有限浮点值。

    标准 JSON 不允许 `NaN`、`Infinity`。无解结果中的 `math.inf` 会在这里转换为
    `None`，最终写入 JSON 时表现为 `null`。
    """
    if isinstance(value, float):
        return value if math.isfinite(value) else None
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value
