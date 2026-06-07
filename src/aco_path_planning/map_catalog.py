from __future__ import annotations

"""示例地图元数据目录。

地图 CSV 本身只记录格子数值，不适合直接展示给用户。本模块给每张精选地图补充
展示名、类别、特点说明和预期可解性，主要供 Streamlit 界面和地图一致性测试使用。
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class MapMetadata:
    """地图展示与验证信息。

    字段说明：
    - `display_name`：界面下拉框中的展示名。
    - `category`：地图类别，用于排序和分组。
    - `description`：地图特点说明。
    - `expected_solvable`：预期是否存在可行路径。
    - `start` / `goal`：期望起终点坐标，用于测试校验 CSV 是否被误改。
    - `analysis_ready`：是否适合作为收敛分析代表图。
    """

    display_name: str
    category: str
    description: str
    expected_solvable: bool
    start: tuple[int, int]
    goal: tuple[int, int]
    analysis_ready: bool = False


# 精选地图目录。key 必须与 data/maps/ 下的 CSV 文件名一致。
MAP_CATALOG: dict[str, MapMetadata] = {
    "easy.csv": MapMetadata(
        display_name="easy / 基础可达图 A",
        category="easy",
        description="基础可达图，障碍少，适合快速验证运行链路。",
        expected_solvable=True,
        start=(5, 0),
        goal=(0, 5),
    ),
    "easy_alt.csv": MapMetadata(
        display_name="easy / 基础可达图 B",
        category="easy",
        description="基础可达图的变体，起终点改到右下与左上，适合观察方向变化。",
        expected_solvable=True,
        start=(5, 5),
        goal=(0, 0),
        analysis_ready=True,
    ),
    "medium.csv": MapMetadata(
        display_name="medium / 中等绕障图 A",
        category="medium",
        description="中等复杂度绕障图，路径选择较多，适合观察普通收敛。",
        expected_solvable=True,
        start=(8, 1),
        goal=(1, 8),
    ),
    "medium_alt.csv": MapMetadata(
        display_name="medium / 中等绕障图 B",
        category="medium",
        description="中等绕障图的变体，起点与终点落在左右两侧，适合做同类对照。",
        expected_solvable=True,
        start=(0, 1),
        goal=(9, 8),
        analysis_ready=True,
    ),
    "blocked.csv": MapMetadata(
        display_name="blocked / 无解图 A",
        category="blocked",
        description="小尺寸无解图，适合验证失败返回逻辑。",
        expected_solvable=False,
        start=(4, 0),
        goal=(0, 4),
    ),
    "blocked_alt.csv": MapMetadata(
        display_name="blocked / 无解图 B",
        category="blocked",
        description="接近可达但实际封死的无解图，适合演示陷阱场景。",
        expected_solvable=False,
        start=(0, 0),
        goal=(4, 4),
    ),
    "hard_corridor.csv": MapMetadata(
        display_name="hard_corridor / 狭窄通道图 A",
        category="hard_corridor",
        description="狭窄通道图，主通路细长，适合观察局部更新与精英强化效果。",
        expected_solvable=True,
        start=(9, 1),
        goal=(1, 10),
    ),
    "hard_corridor_alt.csv": MapMetadata(
        display_name="hard_corridor / 狭窄通道图 B",
        category="hard_corridor",
        description="狭窄通道图变体，通道转折更多，适合比较收敛稳定性。",
        expected_solvable=True,
        start=(1, 1),
        goal=(9, 10),
    ),
    "maze_small.csv": MapMetadata(
        display_name="maze_small / 小型迷宫图 A",
        category="maze_small",
        description="小型迷宫图，死路较多，适合观察搜索稳定性。",
        expected_solvable=True,
        start=(9, 1),
        goal=(1, 8),
    ),
    "maze_small_alt.csv": MapMetadata(
        display_name="maze_small / 小型迷宫图 B",
        category="maze_small",
        description="小型迷宫图变体，起点改到侧边，适合观察起点变化的影响。",
        expected_solvable=True,
        start=(4, 0),
        goal=(0, 8),
    ),
    "dense_obstacles.csv": MapMetadata(
        display_name="dense_obstacles / 高障碍密度图 A",
        category="dense_obstacles",
        description="高障碍密度图，可通路较细，适合观察成功路径数量变化。",
        expected_solvable=True,
        start=(5, 0),
        goal=(0, 11),
    ),
    "dense_obstacles_alt.csv": MapMetadata(
        display_name="dense_obstacles / 高障碍密度图 B",
        category="dense_obstacles",
        description="高障碍密度图变体，终点不在边角，适合减少终点位置偏置。",
        expected_solvable=True,
        start=(10, 1),
        goal=(2, 9),
    ),
    "large_sparse.csv": MapMetadata(
        display_name="large_sparse / 大图稀疏障碍 A",
        category="large_sparse",
        description="大尺寸稀疏障碍图，适合观察大图上的收敛速度。",
        expected_solvable=True,
        start=(13, 1),
        goal=(1, 13),
        analysis_ready=True,
    ),
    "large_sparse_alt.csv": MapMetadata(
        display_name="large_sparse / 大图稀疏障碍 B",
        category="large_sparse",
        description="大图稀疏障碍变体，起终点位于上下中部，适合减少对角偏置。",
        expected_solvable=True,
        start=(13, 7),
        goal=(0, 7),
    ),
    "large_dense.csv": MapMetadata(
        display_name="large_dense / 大图密集障碍 A",
        category="large_dense",
        description="大尺寸密集障碍图，适合观察复杂地图上的成功路径统计。",
        expected_solvable=True,
        start=(12, 1),
        goal=(1, 13),
    ),
    "large_dense_alt.csv": MapMetadata(
        display_name="large_dense / 大图密集障碍 B",
        category="large_dense",
        description="大图密集障碍变体，起终点都避开角落，适合观察方向变化。",
        expected_solvable=True,
        start=(13, 12),
        goal=(1, 2),
        analysis_ready=True,
    ),
    "no_solution_large.csv": MapMetadata(
        display_name="no_solution_large / 大图无解 A",
        category="no_solution_large",
        description="大尺寸无解图，适合演示复杂场景中的失败处理。",
        expected_solvable=False,
        start=(9, 0),
        goal=(4, 8),
    ),
    "no_solution_large_alt.csv": MapMetadata(
        display_name="no_solution_large / 大图无解 B",
        category="no_solution_large",
        description="大图无解变体，视觉上接近可达，但关键通路被封闭。",
        expected_solvable=False,
        start=(0, 9),
        goal=(8, 2),
    ),
}

# 地图在界面下拉框中的类别排序。没有出现在这里的类别会排到最后。
MAP_CATEGORY_ORDER = [
    "easy",
    "medium",
    "hard_corridor",
    "maze_small",
    "dense_obstacles",
    "large_sparse",
    "large_dense",
    "blocked",
    "no_solution_large",
]


CUSTOM_CATEGORY = "custom"


def _fallback_metadata(file_name: str) -> MapMetadata:
    """为不在精选目录中的地图构造兜底元数据。

    典型场景是前端保存的自定义地图。兜底后界面仍能展示和排序，不会因为缺元数据
    抛出 `KeyError`。
    """
    stem = file_name[:-4] if file_name.endswith(".csv") else file_name
    return MapMetadata(
        display_name=f"custom / {stem}",
        category=CUSTOM_CATEGORY,
        description="自定义地图，由前端编辑器保存。",
        expected_solvable=True,
        start=(0, 0),
        goal=(0, 0),
    )


def get_map_metadata(file_name: str) -> MapMetadata:
    """获取地图元数据；未知地图返回 custom 兜底信息。"""
    metadata = MAP_CATALOG.get(file_name)
    if metadata is None:
        return _fallback_metadata(file_name)
    return metadata


def get_sorted_map_files(file_names: list[str]) -> list[str]:
    """按地图类别和展示名排序文件名列表。

    已知类别按 `MAP_CATEGORY_ORDER` 排序，未知/自定义地图排在最后。
    """
    category_rank = {name: index for index, name in enumerate(MAP_CATEGORY_ORDER)}
    return sorted(
        file_names,
        key=lambda file_name: (
            category_rank.get(get_map_metadata(file_name).category, 999),
            get_map_metadata(file_name).display_name,
        ),
    )
