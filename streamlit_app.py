from __future__ import annotations

"""Streamlit 根入口。

保留这个文件是为了支持 `streamlit run streamlit_app.py` 这种最直观的启动方式。
真正的页面逻辑在 `aco_path_planning.webapp` 中，这里只做入口转发。
"""

from scripts.run_streamlit import main


if __name__ == "__main__":
    # Streamlit 页面函数不需要返回退出码，直接执行即可。
    main()
