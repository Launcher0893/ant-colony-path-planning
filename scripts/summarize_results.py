from __future__ import annotations

"""实验结果汇总脚本。

扫描 `data/outputs/` 下保存的 `result.json`，提取路径指标、运行耗时、成功路径数
和主要 ACO 参数，写成统一的 `summary.csv`，便于课程报告和参数对比实验使用。
"""

import argparse
import csv
import json
from pathlib import Path

# 工具脚本直接运行时需要把 src 加入导入路径。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
import sys

if str(SRC_DIR) not in sys.path:
    # 优先导入当前工作区源码，而不是环境中可能存在的旧安装版本。
    sys.path.insert(0, str(SRC_DIR))

from aco_path_planning.config import DEFAULT_OUTPUT_ROOT


def parse_args() -> argparse.Namespace:
    """解析汇总脚本参数。"""
    parser = argparse.ArgumentParser(description="Summarize saved experiment outputs.")
    parser.add_argument("--input-dir", default=str(DEFAULT_OUTPUT_ROOT))
    parser.add_argument("--output-file", default=str(DEFAULT_OUTPUT_ROOT / "summary.csv"))
    return parser.parse_args()


def main() -> int:
    """脚本主流程：收集结果、写出 CSV，并打印输出文件路径。"""
    args = parse_args()
    input_dir = Path(args.input_dir)
    output_file = Path(args.output_file)
    rows = collect_results(input_dir)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    write_summary(output_file, rows)
    print(output_file)
    return 0


def collect_results(input_dir: Path) -> list[dict[str, object]]:
    """递归收集输入目录下所有 `result.json`。

    每个结果目录可以额外放一个 `experiment_label.txt`，用于标记参数组名称，例如
    `baseline`、`high_ants`。没有标签文件时使用空字符串。
    """
    rows: list[dict[str, object]] = []
    for result_file in sorted(input_dir.rglob("result.json")):
        payload = json.loads(result_file.read_text(encoding="utf-8"))
        params = payload.get("params", {})
        label_file = result_file.parent / "experiment_label.txt"
        experiment_label = label_file.read_text(encoding="utf-8").strip() if label_file.exists() else ""
        rows.append(
            {
                # 手工或批量实验设置的参数组标签。
                "experiment_label": experiment_label,
                # 运行来源：cli 或 streamlit。
                "surface": payload.get("surface"),
                "map_name": payload.get("map_name"),
                "found": payload.get("found"),
                "path_length": payload.get("path_length"),
                "best_iteration": payload.get("best_iteration"),
                "runtime_seconds": payload.get("runtime_seconds"),
                "total_successful_paths": payload.get("total_successful_paths"),
                # 每轮平均成功蚂蚁数，反映该参数组合下搜索稳定性。
                "avg_success_count": _mean(payload.get("history_success_count", [])),
                # 三条曲线的最终有限值，方便不打开图片也能做表格对比。
                "best_length_curve_final": _last_finite(payload.get("history_best_length", [])),
                "iteration_best_curve_final": _last_finite(
                    payload.get("history_iteration_best_length", [])
                ),
                "iteration_mean_curve_final": _last_finite(
                    payload.get("history_iteration_mean_length", [])
                ),
                "ant_count": params.get("ant_count"),
                "iterations": params.get("iterations"),
                "alpha": params.get("alpha"),
                "beta": params.get("beta"),
                "evaporation_rate": params.get("evaporation_rate"),
                "pheromone_deposit_q": params.get("pheromone_deposit_q"),
                "initial_pheromone": params.get("initial_pheromone"),
                "local_evaporation_rate": params.get("local_evaporation_rate"),
                "elite_enabled": params.get("elite_enabled"),
                "elite_weight": params.get("elite_weight"),
                "random_seed": params.get("random_seed"),
                # 保留结果目录，方便从汇总表回溯到原始图片和 JSON。
                "result_dir": str(result_file.parent),
            }
        )
    return rows


def write_summary(path: Path, rows: list[dict[str, object]]) -> None:
    """把收集到的结果写成 CSV。

    字段顺序固定，避免多次运行时列顺序漂移，方便文档表格和脚本消费。
    """
    fieldnames = [
        "experiment_label",
        "surface",
        "map_name",
        "found",
        "path_length",
        "best_iteration",
        "runtime_seconds",
        "total_successful_paths",
        "avg_success_count",
        "best_length_curve_final",
        "iteration_best_curve_final",
        "iteration_mean_curve_final",
        "ant_count",
        "iterations",
        "alpha",
        "beta",
        "evaporation_rate",
        "pheromone_deposit_q",
        "initial_pheromone",
        "local_evaporation_rate",
        "elite_enabled",
        "elite_weight",
        "random_seed",
        "result_dir",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _mean(values: list[float | int]) -> float:
    """计算数值列表均值；空列表返回 0。"""
    if not values:
        return 0.0
    return float(sum(values) / len(values))


def _last_finite(values: list[float | int]) -> float | None:
    """从列表末尾向前寻找最后一个有限值。

    无解场景中的历史曲线可能包含 `inf`，保存为 JSON 后再读回来仍可能是浮点无穷。
    如果找不到有限值，返回 None，写入 CSV 时表现为空字段。
    """
    for value in reversed(values):
        if value != float("inf"):
            return float(value)
    return None


if __name__ == "__main__":
    # 将 main 的返回值作为脚本退出码。
    raise SystemExit(main())
