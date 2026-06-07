"""蚁群路径规划包的公共导出入口。

外部代码如果只想使用核心能力，优先从包根导入这里列出的对象，例如：

`from aco_path_planning import AcoParams, load_grid_map, solve_path`

这样调用方不需要关心具体实现分散在哪个模块中。
"""

from .config import (
    DEFAULT_CLI_OUTPUT_DIR,
    DEFAULT_GENERATED_MAP_DIR,
    DEFAULT_MAP_DIR,
    DEFAULT_OUTPUT_ROOT,
    DEFAULT_PARAM_FILE,
    DEFAULT_STREAMLIT_OUTPUT_DIR,
    PROJECT_ROOT,
)
from .map_loader import discover_map_files, load_grid_map
from .models import AcoParams, GridMap, PlanningResult
from .solver import solve_path

# 只把稳定的公共接口放入 __all__，避免调用方依赖内部辅助函数。
__all__ = [
    "AcoParams",
    "DEFAULT_CLI_OUTPUT_DIR",
    "DEFAULT_GENERATED_MAP_DIR",
    "DEFAULT_MAP_DIR",
    "DEFAULT_OUTPUT_ROOT",
    "DEFAULT_PARAM_FILE",
    "DEFAULT_STREAMLIT_OUTPUT_DIR",
    "GridMap",
    "PROJECT_ROOT",
    "PlanningResult",
    "discover_map_files",
    "load_grid_map",
    "solve_path",
]
