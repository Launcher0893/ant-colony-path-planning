from __future__ import annotations

from pathlib import Path

import streamlit as st

from .config import DEFAULT_MAP_DIR, DEFAULT_PARAM_FILE, DEFAULT_STREAMLIT_OUTPUT_DIR
from .map_loader import discover_map_files, load_grid_map
from .models import AcoParams
from .output_writer import save_planning_artifacts
from .solver import solve_path
from .visualization import format_path_coordinates, plot_convergence, plot_grid_map


def main() -> None:
    map_files = discover_map_files(DEFAULT_MAP_DIR)
    defaults = _load_defaults()

    st.set_page_config(page_title="ACO Path Planning", layout="wide")
    st.title("基于蚁群算法的栅格路径规划系统")
    st.caption("从 CSV 栅格地图读取起点、终点和障碍物信息，并进行路径规划。")

    if not map_files:
        st.error("未找到可用地图文件，请先在 data/maps/ 目录下添加 CSV 地图。")
        return

    with st.sidebar:
        st.header("参数设置")
        selected_map_name = st.selectbox(
            "选择地图",
            options=[path.name for path in map_files],
            index=0,
        )
        ant_count = st.number_input(
            "蚂蚁数量",
            min_value=1,
            value=int(defaults.ant_count),
            step=1,
        )
        iterations = st.number_input(
            "迭代次数",
            min_value=1,
            value=int(defaults.iterations),
            step=1,
        )
        alpha = st.number_input("alpha", min_value=0.0, value=float(defaults.alpha), step=0.1)
        beta = st.number_input("beta", min_value=0.0, value=float(defaults.beta), step=0.1)
        evaporation_rate = st.number_input(
            "rho",
            min_value=0.0,
            max_value=0.99,
            value=float(defaults.evaporation_rate),
            step=0.05,
        )
        pheromone_deposit_q = st.number_input(
            "Q",
            min_value=1.0,
            value=float(defaults.pheromone_deposit_q),
            step=1.0,
        )
        initial_pheromone = st.number_input(
            "初始信息素",
            min_value=0.1,
            value=float(defaults.initial_pheromone),
            step=0.1,
        )
        random_seed = st.number_input(
            "随机种子",
            min_value=0,
            value=int(defaults.random_seed if defaults.random_seed is not None else 42),
            step=1,
        )
        save_output = st.checkbox("保存本次结果", value=False)
        run_clicked = st.button("开始规划", type="primary")

    selected_map_path = next(path for path in map_files if path.name == selected_map_name)
    grid_map = load_grid_map(selected_map_path)

    info_col, preview_col = st.columns([1, 2])
    with info_col:
        st.subheader("地图信息")
        st.write(f"文件: `{selected_map_path.relative_to(Path.cwd()) if selected_map_path.is_relative_to(Path.cwd()) else selected_map_path.name}`")
        st.write(f"尺寸: `{grid_map.rows} x {grid_map.cols}`")
        st.write(f"起点: `{grid_map.start}`")
        st.write(f"终点: `{grid_map.goal}`")
        st.write(f"默认参数文件: `{DEFAULT_PARAM_FILE.name}`")
    with preview_col:
        st.subheader("地图预览")
        st.pyplot(plot_grid_map(grid_map, title="Map Preview"))

    if not run_clicked:
        st.info("调整参数后点击“开始规划”执行路径搜索。")
        return

    params = AcoParams(
        ant_count=int(ant_count),
        iterations=int(iterations),
        alpha=float(alpha),
        beta=float(beta),
        evaporation_rate=float(evaporation_rate),
        pheromone_deposit_q=float(pheromone_deposit_q),
        initial_pheromone=float(initial_pheromone),
        random_seed=int(random_seed),
    )
    result = solve_path(grid_map, params)

    metric_col_1, metric_col_2, metric_col_3 = st.columns(3)
    metric_col_1.metric("是否找到路径", "是" if result.found else "否")
    metric_col_2.metric(
        "路径长度",
        f"{result.path_length:.3f}" if result.found else "inf",
    )
    metric_col_3.metric(
        "最优轮次",
        str(result.best_iteration) if result.best_iteration is not None else "-",
    )
    st.write(f"运行耗时: `{result.runtime_seconds:.4f}` 秒")
    st.write(result.message)

    if save_output:
        saved_dir = save_planning_artifacts(
            grid_map=grid_map,
            params=params,
            result=result,
            surface="streamlit",
            output_root=DEFAULT_STREAMLIT_OUTPUT_DIR,
        )
        st.success(f"结果已保存到: `{saved_dir}`")

    chart_col, curve_col = st.columns(2)
    with chart_col:
        st.subheader("最终路径")
        st.pyplot(plot_grid_map(grid_map, result))
    with curve_col:
        st.subheader("收敛曲线")
        st.pyplot(plot_convergence(result.history_best_length))

    st.subheader("路径坐标")
    st.code(format_path_coordinates(result.path), language="text")


def _load_defaults() -> AcoParams:
    from .cli import _load_params_from_file

    defaults = _load_params_from_file(DEFAULT_PARAM_FILE)
    return AcoParams(**defaults)
