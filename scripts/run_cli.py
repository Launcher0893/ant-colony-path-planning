from __future__ import annotations

"""CLI 脚本入口。

项目采用 `src` 布局，源码包不直接位于仓库根目录。为了让用户可以直接运行
`python scripts/run_cli.py`，这里先把 `src` 加入 `sys.path`，再导入包内 CLI。
"""

import sys
from pathlib import Path

# 仓库根目录：scripts/ 的上一层。
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    # 插到最前面，确保优先使用当前工作区源码，而不是环境里可能已安装的同名包。
    sys.path.insert(0, str(SRC_DIR))

from aco_path_planning.cli import main


if __name__ == "__main__":
    # `aco_path_planning.cli.main` 返回 0/1，代表 CLI 进程成功或失败。
    raise SystemExit(main())
