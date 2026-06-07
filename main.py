from __future__ import annotations

"""命令行根入口。

保留这个文件是为了让 PyCharm、VS Code 或老师检查项目时，可以直接运行
`python main.py`，而不必先理解 `src` 布局和 `scripts/` 启动脚本。
实际业务逻辑在 `scripts.run_cli` 和 `aco_path_planning.cli` 中。
"""

from scripts.run_cli import main


if __name__ == "__main__":
    # CLI 主函数返回进程退出码；用 SystemExit 把返回值传给操作系统。
    raise SystemExit(main())
