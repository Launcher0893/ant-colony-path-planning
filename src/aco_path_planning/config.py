from __future__ import annotations

"""项目路径配置。

本模块只放路径常量，不放业务逻辑。这样 CLI、Streamlit、脚本、测试都能共享同一套
目录约定，避免每个入口自己拼接相对路径导致行为不一致。
"""

from pathlib import Path

# 当前文件位于 `src/aco_path_planning/config.py`，向上两层就是仓库根目录。
PROJECT_ROOT = Path(__file__).resolve().parents[2]

# 示例地图根目录。前端保存的自定义地图也会落在这个目录下，便于后续复用。
DEFAULT_MAP_DIR = PROJECT_ROOT / "data" / "maps"

# 地图生成脚本的默认输出目录，和人工维护的示例地图分开放置。
DEFAULT_GENERATED_MAP_DIR = DEFAULT_MAP_DIR / "generated"

# ACO 默认参数文件。CLI 和 Streamlit 启动时都会读取它作为参数基线。
DEFAULT_PARAM_FILE = PROJECT_ROOT / "config" / "aco_defaults.json"

# 实验结果根目录；不同运行界面会在下面再分 cli / streamlit 子目录。
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "data" / "outputs"
DEFAULT_CLI_OUTPUT_DIR = DEFAULT_OUTPUT_ROOT / "cli"
DEFAULT_STREAMLIT_OUTPUT_DIR = DEFAULT_OUTPUT_ROOT / "streamlit"
