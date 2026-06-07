from __future__ import annotations

"""Streamlit 脚本入口。

用于支持 `streamlit run scripts/run_streamlit.py`。与 CLI 脚本一样，这里负责
把 `src` 放到导入路径中，具体页面渲染逻辑交给 `aco_path_planning.webapp`。
"""

import sys
from pathlib import Path

# 仓库根目录：scripts/ 的上一层。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    # 保证运行的是当前仓库源码，便于开发和答辩演示。
    sys.path.insert(0, str(SRC_DIR))

from aco_path_planning.webapp import main


if __name__ == "__main__":
    # Streamlit 入口只负责渲染页面，不需要进程退出码。
    main()
