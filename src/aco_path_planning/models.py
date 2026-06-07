from __future__ import annotations

"""核心数据模型。

本项目的不同模块通过这里的三个模型交换数据：

- `GridMap`：算法实际使用的地图。
- `AcoParams`：蚁群算法参数。
- `PlanningResult`：求解器输出结果和收敛历史。

把这些对象集中定义，可以避免 CLI、Streamlit、输出保存和测试各自发明一套字段。
"""

from dataclasses import dataclass
import math
from pathlib import Path

import numpy as np

# 坐标统一使用 (row, col)，与 NumPy 二维数组索引 `grid[row, col]` 保持一致。
Coordinate = tuple[int, int]


@dataclass(frozen=True)
class GridMap:
    """归一化后的栅格地图。

    `grid` 中只保留两类值：0 表示可通行，1 表示障碍。原始 CSV 中的起点 2、
    终点 3 会被转换为可通行格，并分别保存到 `start` 和 `goal` 字段中。
    """

    # 二维 NumPy 数组，形状为 (rows, cols)，元素只应为 0 或 1。
    grid: np.ndarray
    # 起点坐标，格式为 (row, col)。
    start: Coordinate
    # 终点坐标，格式为 (row, col)。
    goal: Coordinate
    # 地图来源文件；自定义地图未保存时可以为空。
    source: Path | None = None

    @property
    def rows(self) -> int:
        """地图行数。"""
        return int(self.grid.shape[0])

    @property
    def cols(self) -> int:
        """地图列数。"""
        return int(self.grid.shape[1])

    @property
    def walkable_mask(self) -> np.ndarray:
        """可通行格布尔掩码，用于批量初始化或更新信息素。"""
        return self.grid == 0


@dataclass(frozen=True)
class AcoParams:
    """蚁群算法参数集合。

    这些字段会从默认 JSON、CLI 参数或 Streamlit 控件中构造出来。求解开始前必须调用
    `validate()`，确保非法值不会进入算法主循环。
    """

    # 每轮派出的蚂蚁数量。
    ant_count: int = 50
    # 总迭代轮数。
    iterations: int = 100
    # 信息素重要程度，越大越依赖历史路径经验。
    alpha: float = 1.0
    # 启发函数重要程度，越大越倾向靠近终点方向。
    beta: float = 4.0
    # 全局信息素挥发率，取值范围 [0, 1)。
    evaporation_rate: float = 0.3
    # 信息素沉积常数 Q，成功路径沉积量约为 Q / 路径长度。
    pheromone_deposit_q: float = 100.0
    # 可通行格初始信息素 tau0。
    initial_pheromone: float = 1.0
    # 局部信息素更新率，用于把蚂蚁走过的格子向初始信息素回拉。
    local_evaporation_rate: float = 0.05
    # 是否启用精英强化，即对当前全局最优路径额外沉积信息素。
    elite_enabled: bool = True
    # 精英强化权重，越大表示越强调当前全局最优路径。
    elite_weight: float = 2.0
    # 随机种子；为 None 时由 NumPy 生成不可复现的随机序列。
    random_seed: int | None = 42

    def validate(self) -> None:
        """校验参数取值范围和关键类型。

        校验集中放在模型层，可以保证 CLI、Web 和测试入口都会获得同样的错误行为。
        """
        ant_count = _require_int("ant_count", self.ant_count)
        iterations = _require_int("iterations", self.iterations)
        alpha = _require_finite_number("alpha", self.alpha)
        beta = _require_finite_number("beta", self.beta)
        evaporation_rate = _require_finite_number("evaporation_rate", self.evaporation_rate)
        pheromone_deposit_q = _require_finite_number(
            "pheromone_deposit_q",
            self.pheromone_deposit_q,
        )
        initial_pheromone = _require_finite_number(
            "initial_pheromone",
            self.initial_pheromone,
        )
        local_evaporation_rate = _require_finite_number(
            "local_evaporation_rate",
            self.local_evaporation_rate,
        )
        elite_weight = _require_finite_number("elite_weight", self.elite_weight)

        if not isinstance(self.elite_enabled, bool):
            raise ValueError("elite_enabled must be a boolean.")
        if self.random_seed is not None:
            _require_int("random_seed", self.random_seed)

        if ant_count <= 0:
            raise ValueError("ant_count must be greater than 0.")
        if iterations <= 0:
            raise ValueError("iterations must be greater than 0.")
        if alpha < 0:
            raise ValueError("alpha must be non-negative.")
        if beta < 0:
            raise ValueError("beta must be non-negative.")
        if not 0 <= evaporation_rate < 1:
            raise ValueError("evaporation_rate must be in [0, 1).")
        if pheromone_deposit_q <= 0:
            raise ValueError("pheromone_deposit_q must be greater than 0.")
        if initial_pheromone <= 0:
            raise ValueError("initial_pheromone must be greater than 0.")
        if not 0 <= local_evaporation_rate < 1:
            raise ValueError("local_evaporation_rate must be in [0, 1).")
        if elite_weight < 0:
            raise ValueError("elite_weight must be non-negative.")


@dataclass(frozen=True)
class PlanningResult:
    """求解器输出结果。

    除最终路径外，还保存多条历史曲线。这样 CLI、Streamlit、图片输出和实验汇总都能
    从同一个结果对象中取数。
    """

    # 是否找到从起点到终点的可行路径。
    found: bool
    # 最优路径坐标序列，格式为 [(row, col), ...]；无解时为空列表。
    path: list[Coordinate]
    # 最优路径长度；无解时为 math.inf，保存 JSON 前会被转成 null。
    path_length: float
    # 最优路径首次出现的迭代轮次；无解时为 None。
    best_iteration: int | None
    # 每轮结束时的历史全局最优路径长度。
    history_best_length: list[float]
    # 每轮内部成功路径中的最短长度；该轮无成功路径时为 inf。
    history_iteration_best_length: list[float]
    # 每轮内部成功路径的平均长度；该轮无成功路径时为 inf。
    history_iteration_mean_length: list[float]
    # 每轮成功到达终点的蚂蚁数量。
    history_success_count: list[int]
    # 整次运行中所有成功路径的数量总和。
    total_successful_paths: int
    # 求解耗时，单位为秒。
    runtime_seconds: float
    # 面向用户展示的简短结果说明。
    message: str


def _require_int(name: str, value: object) -> int:
    """要求字段是严格整数。

    Python 中 `bool` 是 `int` 的子类，所以这里显式排除布尔值，避免 True/False
    被误当成 1/0。
    """
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer.")
    return value


def _require_finite_number(name: str, value: object) -> float:
    """要求字段是有限数值，并拒绝布尔值、NaN 和 Infinity。"""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number.")
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be a finite number.")
    return number
