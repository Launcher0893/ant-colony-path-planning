from __future__ import annotations

"""CSV 地图加载与统一校验。

外部地图文件使用 0/1/2/3 表示空地、障碍、起点、终点；算法内部只需要知道
哪些格子可通行以及起终点坐标。因此本模块负责把外部格式转换成 `GridMap`。
"""

import csv
from pathlib import Path

import numpy as np

from .models import GridMap

# CSV 和自定义地图编辑器允许出现的原始单元格值。
VALID_CELL_VALUES = {0, 1, 2, 3}


def build_grid_map_from_cells(
    raw_grid: np.ndarray,
    source: Path | None = None,
) -> GridMap:
    """校验原始 0/1/2/3 网格并构造 `GridMap`。

    CSV 加载和前端自定义地图都会走这里，保证起点/终点唯一性和归一化规则只有一份。
    """
    if raw_grid.ndim != 2 or raw_grid.size == 0:
        raise ValueError("Map must be a non-empty 2D grid.")

    # 用集合差快速找出不在 0/1/2/3 中的值，报错时只展示一个样例，避免信息过长。
    invalid_values = set(np.unique(raw_grid).tolist()) - VALID_CELL_VALUES
    if invalid_values:
        sample = sorted(invalid_values)[0]
        raise ValueError(
            f"Unsupported cell value {sample}. Allowed values: 0, 1, 2, 3."
        )

    start_positions = np.argwhere(raw_grid == 2)
    goal_positions = np.argwhere(raw_grid == 3)

    if len(start_positions) != 1:
        raise ValueError("Map must contain exactly one start cell with value 2.")
    if len(goal_positions) != 1:
        raise ValueError("Map must contain exactly one goal cell with value 3.")

    # 算法内部只区分障碍和可通行。起点/终点是可通行格，坐标单独存储。
    normalized_grid = np.where(raw_grid == 1, 1, 0).astype(np.int8)
    start = tuple(int(value) for value in start_positions[0])
    goal = tuple(int(value) for value in goal_positions[0])

    return GridMap(grid=normalized_grid, start=start, goal=goal, source=source)


def load_grid_map(path: str | Path) -> GridMap:
    """从 CSV 文件读取地图并返回 `GridMap`。

    允许文件中存在空行；非空行必须是矩形，且每个单元格必须能解析为 0/1/2/3。
    """
    map_path = Path(path)
    if not map_path.exists():
        raise FileNotFoundError(f"Map file not found: {map_path}")

    rows: list[list[int]] = []
    # utf-8-sig 可以兼容 Windows/Excel 常见的 BOM 头。
    with map_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle)
        for row_index, raw_row in enumerate(reader, start=1):
            # 空行不参与矩形宽度校验，方便手工编辑 CSV 时留空行。
            if not raw_row or all(cell.strip() == "" for cell in raw_row):
                continue

            parsed_row: list[int] = []
            for col_index, cell in enumerate(raw_row, start=1):
                value_text = cell.strip()
                try:
                    value = int(value_text)
                except ValueError as exc:
                    raise ValueError(
                        f"Invalid cell value '{value_text}' at row {row_index}, "
                        f"column {col_index}."
                    ) from exc
                if value not in VALID_CELL_VALUES:
                    raise ValueError(
                        f"Unsupported cell value {value} at row {row_index}, "
                        f"column {col_index}. Allowed values: 0, 1, 2, 3."
                    )
                parsed_row.append(value)
            rows.append(parsed_row)

    if not rows:
        raise ValueError("Map file is empty.")

    expected_width = len(rows[0])
    if expected_width == 0:
        raise ValueError("Map file contains an empty row.")

    # 所有非空行宽度必须一致，否则无法构造规则二维数组。
    for index, row in enumerate(rows[1:], start=2):
        if len(row) != expected_width:
            raise ValueError(
                f"Map must be rectangular. Row 1 has width {expected_width}, "
                f"but row {index} has width {len(row)}."
            )

    raw_grid = np.array(rows, dtype=np.int8)
    return build_grid_map_from_cells(raw_grid, source=map_path)


def discover_map_files(directory: str | Path) -> list[Path]:
    """发现指定目录下一层的 CSV 地图文件。

    不递归搜索子目录，避免把 `data/maps/generated/` 中的临时实验地图自动混入精选地图列表。
    """
    root = Path(directory)
    if not root.exists():
        return []
    return sorted(path for path in root.glob("*.csv") if path.is_file())
