from __future__ import annotations

"""自定义地图编辑器的纯逻辑。

这里不直接依赖 Streamlit。前端页面只负责收集用户操作，真正的画笔上色、笔画
栅格化、起终点唯一性、命名清洗和 CSV 保存都放在本模块，便于单元测试。
"""

import csv
import re
from datetime import datetime
from pathlib import Path

import numpy as np

from .map_loader import build_grid_map_from_cells
from .models import GridMap

# 原始编辑网格和 CSV 文件使用的单元格值。
EMPTY = 0
OBSTACLE = 1
START = 2
GOAL = 3

# 前端画笔标识。画笔名称使用英文常量，界面层再映射为中文显示。
BRUSH_OBSTACLE = "obstacle"
BRUSH_START = "start"
BRUSH_GOAL = "goal"
BRUSH_ERASE = "erase"

# 每种画笔对应写入网格的数值。
BRUSH_VALUES = {
    BRUSH_OBSTACLE: OBSTACLE,
    BRUSH_START: START,
    BRUSH_GOAL: GOAL,
    BRUSH_ERASE: EMPTY,
}

# 用户留空地图名时自动生成的文件名前缀。
CUSTOM_MAP_PREFIX = "custom_"
# 只允许字母、数字、下划线和短横线保留，其余字符清洗为下划线。
_NAME_SANITIZE_PATTERN = re.compile(r"[^0-9A-Za-z_\-]+")


def create_empty_grid(rows: int, cols: int) -> np.ndarray:
    """创建一张可编辑空地图。

    参数：
    - `rows`：地图行数，至少为 2。
    - `cols`：地图列数，至少为 2。

    默认把左上角设为起点，右下角设为终点，保证新画布一创建就是可保存状态。
    """
    if rows < 2 or cols < 2:
        raise ValueError("Grid must be at least 2 x 2 to hold a start and a goal.")

    grid = np.zeros((rows, cols), dtype=np.int8)
    grid[0, 0] = START
    grid[rows - 1, cols - 1] = GOAL
    return grid


def apply_brush(grid: np.ndarray, row: int, col: int, brush: str) -> np.ndarray:
    """用指定画笔给单个格子上色。

    会直接修改传入的 `grid` 并返回它，方便 Streamlit 会话状态复用。
    起点和终点必须全图唯一，因此使用起点/终点画笔时会先清除原有同类标记。
    """
    if brush not in BRUSH_VALUES:
        raise ValueError(f"Unknown brush '{brush}'.")
    if not (0 <= row < grid.shape[0] and 0 <= col < grid.shape[1]):
        raise ValueError(f"Cell ({row}, {col}) is outside the grid.")

    target_value = BRUSH_VALUES[brush]

    # Start and goal must stay unique: clear any previous cell of the same kind.
    if target_value in (START, GOAL):
        grid[grid == target_value] = EMPTY

    grid[row, col] = target_value
    return grid


def cells_from_stroke_alpha(
    alpha: np.ndarray,
    cell_px: int,
    rows: int,
    cols: int,
    alpha_threshold: int = 32,
    min_coverage: float = 0.02,
) -> set[tuple[int, int]]:
    """把拖动画笔的 alpha 掩码转换为被经过的格子集合。

    参数：
    - `alpha`：画布分辨率下的二维透明度数组。
    - `cell_px`：一个地图格子的像素边长。
    - `rows` / `cols`：地图行列数。
    - `alpha_threshold`：像素透明度达到该阈值才算被笔画覆盖。
    - `min_coverage`：一个格子内被覆盖像素比例达到该值才算触碰。

    `min_coverage` 用于过滤抗锯齿造成的微弱边缘像素，避免误涂相邻格子。
    """
    if alpha.ndim != 2:
        raise ValueError("alpha mask must be a 2D array.")
    if cell_px <= 0:
        raise ValueError("cell_px must be positive.")

    touched: set[tuple[int, int]] = set()
    for row in range(rows):
        y0 = row * cell_px
        y1 = y0 + cell_px
        for col in range(cols):
            x0 = col * cell_px
            x1 = x0 + cell_px
            block = alpha[y0:y1, x0:x1]
            if block.size == 0:
                continue
            # 只统计透明度足够高的像素，避免低透明度边缘导致误判。
            covered = int(np.count_nonzero(block >= alpha_threshold))
            if covered / block.size >= min_coverage:
                touched.add((row, col))
    return touched


def cells_from_stroke_image(
    image_data,
    cell_px: int,
    rows: int,
    cols: int,
    **kwargs,
) -> set[tuple[int, int]]:
    """从 drawable-canvas 返回的 RGBA 笔画图层中提取被触碰格子。

    `image_data` 应是形状为 `(H, W, 4)` 的数组，其中第 4 个通道是 alpha。
    组件返回的是笔画层，不包含背景网格。
    """
    array = np.asarray(image_data)
    if array.ndim != 3 or array.shape[2] < 4:
        raise ValueError("image_data must be an (H, W, 4) RGBA array.")
    alpha = array[:, :, 3]
    return cells_from_stroke_alpha(alpha, cell_px, rows, cols, **kwargs)


def _pick_single_cell(cells: set[tuple[int, int]]) -> tuple[int, int]:
    """为多格起点/终点笔画选择一个代表格。

    起点和终点只能有一个。用户拖动时可能划过多个格子，因此选取最接近触碰格
    几何中心的格子作为最终落点。
    """
    cell_list = list(cells)
    mean_row = sum(row for row, _ in cell_list) / len(cell_list)
    mean_col = sum(col for _, col in cell_list) / len(cell_list)
    return min(
        cell_list,
        key=lambda rc: ((rc[0] - mean_row) ** 2 + (rc[1] - mean_col) ** 2, rc),
    )


def apply_brush_to_cells(
    grid: np.ndarray,
    cells: set[tuple[int, int]],
    brush: str,
) -> np.ndarray:
    """把一组格子按指定画笔上色。

    障碍和擦除画笔会作用于所有触碰格；起点和终点是单值标记，多格笔画会收敛为
    一个代表格。函数会原地修改 `grid`。
    """
    if brush not in BRUSH_VALUES:
        raise ValueError(f"Unknown brush '{brush}'.")
    if not cells:
        return grid

    if brush in (BRUSH_START, BRUSH_GOAL):
        row, col = _pick_single_cell(cells)
        apply_brush(grid, row, col, brush)
    else:
        for row, col in cells:
            if 0 <= row < grid.shape[0] and 0 <= col < grid.shape[1]:
                apply_brush(grid, row, col, brush)
    return grid


def count_markers(grid: np.ndarray) -> tuple[int, int]:
    """统计当前网格中的起点数量和终点数量。"""
    start_count = int(np.count_nonzero(grid == START))
    goal_count = int(np.count_nonzero(grid == GOAL))
    return start_count, goal_count


def is_ready_to_save(grid: np.ndarray) -> bool:
    """判断地图是否达到保存/规划条件：恰好一个起点和一个终点。"""
    start_count, goal_count = count_markers(grid)
    return start_count == 1 and goal_count == 1


def build_grid_map_from_array(grid: np.ndarray, source: Path | None = None) -> GridMap:
    """从内存编辑网格构造经过校验的 `GridMap`。

    与 CSV 加载不同，内存数组可能来自前端状态或测试，所以这里先检查维度、整数类型
    和值域，再复用 `map_loader.build_grid_map_from_cells` 做起终点唯一性和归一化。
    """
    raw_grid = np.asarray(grid)
    if raw_grid.ndim != 2 or raw_grid.size == 0:
        raise ValueError("Map must be a non-empty 2D grid.")
    if not np.issubdtype(raw_grid.dtype, np.integer):
        raise ValueError("Map grid values must be integers.")
    # 先在原始 dtype 上检查值域，避免 int8 转换前把 259 之类的值截断成合法数。
    invalid_values = set(np.unique(raw_grid).tolist()) - {EMPTY, OBSTACLE, START, GOAL}
    if invalid_values:
        sample = sorted(invalid_values)[0]
        raise ValueError(f"Unsupported cell value {sample}. Allowed values: 0, 1, 2, 3.")
    raw_grid = raw_grid.astype(np.int8, copy=True)
    return build_grid_map_from_cells(raw_grid, source=source)


def sanitize_map_name(name: str) -> str:
    """把用户输入的地图名清洗成安全的 CSV 文件 stem。

    会去掉路径和扩展名，并把空格、中文标点等不安全字符替换成下划线。
    """
    stem = Path(name.strip()).stem
    stem = _NAME_SANITIZE_PATTERN.sub("_", stem).strip("_")
    return stem


def generate_custom_map_name(
    existing_names: list[str],
    now: datetime | None = None,
) -> str:
    """生成不冲突的自动地图名 stem。

    文件名格式为 `custom_<年月日>_<时分秒>_<序号>`。`existing_names` 是当前地图目录
    下已有文件名列表，用于避免冲突。
    """
    current_time = now or datetime.now()
    timestamp = current_time.strftime("%Y%m%d_%H%M%S")
    existing_stems = {Path(name).stem for name in existing_names}

    sequence = sum(1 for name in existing_names if Path(name).stem.startswith(CUSTOM_MAP_PREFIX)) + 1
    candidate = f"{CUSTOM_MAP_PREFIX}{timestamp}_{sequence}"
    while candidate in existing_stems:
        sequence += 1
        candidate = f"{CUSTOM_MAP_PREFIX}{timestamp}_{sequence}"
    return candidate


def _resolve_unique_stem(stem: str, existing_names: list[str]) -> str:
    """在用户给定 stem 已存在时追加 `_1`、`_2` 等后缀。"""
    existing_stems = {Path(name).stem.lower() for name in existing_names}
    candidate = stem
    sequence = 1
    while candidate.lower() in existing_stems:
        candidate = f"{stem}_{sequence}"
        sequence += 1
    return candidate


def resolve_map_filename(
    user_name: str,
    existing_names: list[str],
    now: datetime | None = None,
) -> str:
    """根据可选用户输入决定最终 `<name>.csv` 文件名。

    用户填写名称时优先使用清洗后的名称；留空时生成时间戳名称；两种情况都会避免
    和已有地图同名。
    """
    cleaned = sanitize_map_name(user_name) if user_name else ""
    stem = _resolve_unique_stem(cleaned, existing_names) if cleaned else generate_custom_map_name(existing_names, now=now)
    return f"{stem}.csv"


def _safe_csv_filename(file_name: str) -> str:
    """校验直接保存入口收到的文件名是否安全。

    与 `sanitize_map_name` 不同，这里不自动修正危险输入，而是直接拒绝。这样可以防止
    调用方绕过 `resolve_map_filename` 后传入路径逃逸或不安全文件名。
    """
    raw_name = file_name.strip()
    if not raw_name:
        raise ValueError("Map file name must not be empty.")

    candidate = Path(raw_name)
    if candidate.is_absolute() or candidate.name != raw_name:
        raise ValueError("Map file name must not include a path.")
    if candidate.suffix and candidate.suffix != ".csv":
        raise ValueError("Map file name must use the .csv extension.")

    stem = candidate.stem if candidate.suffix else candidate.name
    if not stem or sanitize_map_name(stem) != stem:
        raise ValueError("Map file name contains unsafe characters.")
    return f"{stem}.csv"


def save_custom_map(
    grid: np.ndarray,
    file_name: str,
    directory: str | Path,
) -> Path:
    """校验并保存自定义地图到指定目录。

    保存前会先构造 `GridMap`，因此缺起点、缺终点、非法值等问题都会提前报错。
    文件写入使用 `"x"` 模式，目标文件已存在时不会覆盖。
    """
    # Validate before writing so we never persist an unusable map.
    build_grid_map_from_array(grid)

    target_dir = Path(directory)
    target_dir.mkdir(parents=True, exist_ok=True)

    safe_name = _safe_csv_filename(file_name)
    output_path = target_dir / safe_name

    with output_path.open("x", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerows(np.asarray(grid, dtype=int).tolist())

    return output_path
