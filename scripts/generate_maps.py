from __future__ import annotations

"""实验地图生成脚本。

用于生成额外的 benchmark 栅格地图，默认输出到 `data/maps/generated/`。生成出的
地图仍使用项目统一的 CSV 数值格式：0 空地、1 障碍、2 起点、3 终点。
"""

import argparse
import csv
import random
from pathlib import Path

# scripts/ 目录下的工具脚本需要手动把 src 放进导入路径，才能直接用
# `python scripts/generate_maps.py ...` 运行。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
import sys

if str(SRC_DIR) not in sys.path:
    # 优先导入当前工作区源码。
    sys.path.insert(0, str(SRC_DIR))

from aco_path_planning.config import DEFAULT_GENERATED_MAP_DIR
from aco_path_planning.custom_map import sanitize_map_name


def parse_args() -> argparse.Namespace:
    """解析地图生成参数。

    参数说明：
    - `mode`：生成模式，目前支持迷宫、密集障碍、大图稀疏障碍。
    - `rows` / `cols`：地图行列数，后续会要求至少 2 x 2。
    - `density`：障碍密度，部分模式会限制最大有效密度。
    - `seed`：随机种子，用于复现实验地图。
    - `name`：输出文件名 stem，不带 `.csv`。
    """
    parser = argparse.ArgumentParser(description="Generate benchmark grid maps.")
    parser.add_argument("--mode", choices=["maze", "dense", "large_sparse"], required=True)
    parser.add_argument("--rows", type=int, default=15)
    parser.add_argument("--cols", type=int, default=15)
    parser.add_argument("--density", type=float, default=0.28)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--name", required=True, help="Output filename without extension.")
    return parser.parse_args()


def main() -> int:
    """脚本主流程，生成地图并写入 CSV。"""
    args = parse_args()
    # 使用标准库 random.Random，保证同一 seed 下生成结果稳定。
    rng = random.Random(args.seed)
    grid = build_grid(args.mode, args.rows, args.cols, args.density, rng)
    output_dir = DEFAULT_GENERATED_MAP_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{safe_output_stem(args.name)}.csv"
    write_csv(output_path, grid)
    print(output_path)
    return 0


def build_grid(
    mode: str,
    rows: int,
    cols: int,
    density: float,
    rng: random.Random,
) -> list[list[int]]:
    """根据模式生成原始地图矩阵。

    返回值仍是 0/1/2/3 网格。无论哪种模式，都会调用 `carve_path` 打通一条从
    左上角到右下角的基础路径，保证生成图至少可达。
    """
    if rows < 2 or cols < 2:
        raise ValueError("Generated maps must be at least 2 x 2.")

    grid = [[0 for _ in range(cols)] for _ in range(rows)]
    # 生成脚本固定使用左上为起点、右下为终点，便于快速造图。
    start = (0, 0)
    goal = (rows - 1, cols - 1)

    if mode == "maze":
        # 迷宫模式：只在内部区域按棋盘式位置随机放障碍，边界先保持通畅。
        for row in range(rows):
            for col in range(cols):
                if row in (0, rows - 1) or col in (0, cols - 1):
                    continue
                if (row + col) % 2 == 0 and rng.random() < 0.55:
                    grid[row][col] = 1
        carve_path(grid, start, goal)
    elif mode == "dense":
        # 密集模式：按用户给定密度随机撒障碍，然后打通一条保证可达的路径。
        for row in range(rows):
            for col in range(cols):
                if rng.random() < density:
                    grid[row][col] = 1
        carve_path(grid, start, goal)
    elif mode == "large_sparse":
        # 稀疏大图模式：限制最高密度，避免生成过于拥堵而不适合展示的大图。
        sparse_density = min(density, 0.18)
        for row in range(rows):
            for col in range(cols):
                if rng.random() < sparse_density:
                    grid[row][col] = 1
        carve_path(grid, start, goal)

    # 起点和终点最后写入，避免被障碍或 carve_path 覆盖。
    grid[start[0]][start[1]] = 2
    grid[goal[0]][goal[1]] = 3
    return grid


def carve_path(grid: list[list[int]], start: tuple[int, int], goal: tuple[int, int]) -> None:
    """在地图中打通一条从 start 到 goal 的 L 形通路。

    先向下走到目标行，再向右走到目标列。这个函数会直接修改传入的 `grid`。
    """
    row, col = start
    goal_row, goal_col = goal
    while row < goal_row:
        grid[row][col] = 0
        row += 1
    while col < goal_col:
        grid[row][col] = 0
        col += 1
    grid[goal_row][goal_col] = 0


def write_csv(path: Path, grid: list[list[int]]) -> None:
    """把二维整数网格写成 CSV 文件。"""
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerows(grid)


def safe_output_stem(name: str) -> str:
    """清洗并校验输出文件名 stem。

    复用自定义地图模块的清洗规则，防止 `--name` 携带路径或危险字符。
    """
    stem = sanitize_map_name(name)
    if not stem:
        raise ValueError("Output map name must contain at least one safe character.")
    return stem


if __name__ == "__main__":
    # 将 main 的返回值作为脚本退出码。
    raise SystemExit(main())
