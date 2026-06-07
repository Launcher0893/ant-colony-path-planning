from __future__ import annotations

"""Streamlit 图形界面。

本模块负责页面渲染和用户交互：选择地图、配置参数、运行求解器、展示结果、
保存输出，以及提供自定义地图编辑器。核心算法仍然只由 `solver.solve_path`
完成，界面层不直接实现路径规划逻辑。
"""

from pathlib import Path

import streamlit as st

from .config import DEFAULT_MAP_DIR, DEFAULT_PARAM_FILE, DEFAULT_STREAMLIT_OUTPUT_DIR
from .custom_map import (
    BRUSH_ERASE,
    BRUSH_GOAL,
    BRUSH_OBSTACLE,
    BRUSH_START,
    apply_brush,
    apply_brush_to_cells,
    build_grid_map_from_array,
    cells_from_stroke_image,
    count_markers,
    create_empty_grid,
    is_ready_to_save,
    resolve_map_filename,
    save_custom_map,
)
from .map_catalog import get_map_metadata, get_sorted_map_files
from .map_loader import discover_map_files, load_grid_map
from .models import AcoParams
from .output_writer import save_planning_artifacts
from .solver import solve_path
from .visualization import (
    cell_from_click,
    format_path_coordinates,
    plot_convergence,
    plot_grid_map,
    plot_length_comparison,
    plot_success_count,
    render_editor_canvas,
)

try:
    from streamlit_image_coordinates import streamlit_image_coordinates

    _HAS_IMAGE_COORDS = True
except ImportError:  # pragma: no cover - depends on optional dependency
    _HAS_IMAGE_COORDS = False


def _patch_image_to_url() -> bool:
    """适配 streamlit-drawable-canvas 0.9.3 对 `image_to_url` 的旧调用方式。

    Streamlit 1.50 对 `image_to_url` 做了两处会破坏旧绘图组件的改动：

    1. 函数位置从 `streamlit.elements.image` 移到
       `streamlit.elements.lib.image_utils`。
    2. 第二个参数从 `width: int` 改成了 `layout_config: LayoutConfig`。

    旧组件仍会从旧位置导入并传入整数宽度。这里把一个兼容垫片挂回旧模块位置，
    把整数宽度包装成 `LayoutConfig` 后再转调新版函数。

    返回 True 表示当前运行环境已经具备可用的 `image_to_url`。
    """
    try:
        import streamlit.elements.image as st_image_module
    except ImportError:  # pragma: no cover - defensive
        return False

    try:
        from streamlit.elements.lib.image_utils import image_to_url as new_image_to_url
        from streamlit.elements.lib.layout_utils import LayoutConfig
    except ImportError:  # pragma: no cover - older streamlit layout
        # 旧版 Streamlit 原本就在旧位置提供旧签名函数；如果存在，就不需要垫片。
        return hasattr(st_image_module, "image_to_url")

    def image_to_url_compat(image, width, clamp, channels, output_format, image_id):
        # 绘图组件传入 int 宽度；新版函数需要 LayoutConfig。非 int 参数原样转发。
        layout_config = LayoutConfig(width=width) if isinstance(width, int) else width
        return new_image_to_url(image, layout_config, clamp, channels, output_format, image_id)

    st_image_module.image_to_url = image_to_url_compat
    return True


try:
    if _patch_image_to_url():
        from streamlit_drawable_canvas import st_canvas

        _HAS_DRAWABLE_CANVAS = True
    else:  # pragma: no cover - depends on streamlit internals
        _HAS_DRAWABLE_CANVAS = False
except Exception:  # pragma: no cover - depends on optional dependency
    _HAS_DRAWABLE_CANVAS = False

# 前端中文画笔标签到内部英文画笔常量的映射。
_BRUSH_BY_LABEL = {
    "障碍": BRUSH_OBSTACLE,
    "起点": BRUSH_START,
    "终点": BRUSH_GOAL,
    "擦除": BRUSH_ERASE,
}
# 拖动画布上的 stroke 颜色只影响临时覆盖层；真正的网格颜色会在栅格化后重新渲染。
_BRUSH_STROKE_COLORS = {
    BRUSH_OBSTACLE: "#30343f",
    BRUSH_START: "#1f77b4",
    BRUSH_GOAL: "#d62728",
    BRUSH_ERASE: "#f59e0b",
}
# 编辑器画布最大像素尺寸，用于根据地图行列数自动计算单格大小。
_EDITOR_MAX_CANVAS_PX = 560


def _should_use_drag_canvas(has_drawable_canvas: bool, drag_disabled: bool) -> bool:
    """判断当前是否应使用拖动画布模式。

    参数：
    - `has_drawable_canvas`：依赖组件是否成功导入并完成兼容适配。
    - `drag_disabled`：当前会话是否因运行期异常禁用了拖动画布。
    """
    return has_drawable_canvas and not drag_disabled


def main() -> None:
    """Streamlit 页面主函数。"""
    defaults = _load_defaults()

    st.set_page_config(page_title="ACO Path Planning", layout="wide")
    st.title("基于蚁群算法的栅格路径规划系统")
    st.caption("从 CSV 栅格地图读取或在前端自定义绘制地图，并进行路径规划。")

    with st.sidebar:
        st.header("地图来源")
        # 两种来源共享同一套求解器：示例地图来自 CSV，自定义地图来自前端内存网格。
        map_source = st.radio(
            "选择地图来源",
            ("示例地图", "自定义地图"),
            key="map_source",
        )

        selected_map_path: Path | None = None
        if map_source == "示例地图":
            map_files = discover_map_files(DEFAULT_MAP_DIR)
            if map_files:
                # 先按元数据排序，再用展示名渲染下拉框；真实值仍保留文件名。
                sorted_file_names = get_sorted_map_files([path.name for path in map_files])
                path_by_name = {path.name: path for path in map_files}
                selected_map_name = st.selectbox(
                    "选择地图",
                    options=sorted_file_names,
                    format_func=lambda file_name: get_map_metadata(file_name).display_name,
                    index=0,
                    key="selected_map",
                )
                selected_map_path = path_by_name[selected_map_name]

        st.header("参数设置")
        params = _render_sidebar_params(defaults)
        save_output = st.checkbox(
            "保存本次结果",
            value=False,
            key="save_output",
            help="将图片、路径和 JSON 结果写入 data/outputs/。",
        )
        run_clicked = st.button("开始规划", type="primary")

    if map_source == "示例地图":
        if selected_map_path is None:
            st.error("未找到可用地图文件，请先在 data/maps/ 目录下添加 CSV 地图。")
            return
        _run_example_mode(selected_map_path, params, save_output, run_clicked)
    else:
        _run_custom_mode(params, save_output, run_clicked)


def _render_sidebar_params(defaults: AcoParams) -> AcoParams:
    """渲染侧边栏参数控件，并组装成 `AcoParams`。

    `defaults` 来自配置文件或模型默认值。这里的控件约束只是第一层用户体验限制，
    真正的最终校验仍由 `AcoParams.validate()` 在求解器入口完成。
    """
    ant_count = st.number_input(
        "蚂蚁数量",
        min_value=1,
        value=int(defaults.ant_count),
        step=1,
        key="p_ant_count",
    )
    iterations = st.number_input(
        "迭代次数",
        min_value=1,
        value=int(defaults.iterations),
        step=1,
        key="p_iterations",
    )
    alpha = st.number_input(
        "alpha（信息素重要程度）",
        min_value=0.0,
        value=float(defaults.alpha),
        step=0.1,
        key="p_alpha",
        help="越大越偏向跟随高信息素路径。",
    )
    beta = st.number_input(
        "beta（启发函数重要程度）",
        min_value=0.0,
        value=float(defaults.beta),
        step=0.1,
        key="p_beta",
        help="越大越偏向选择更接近目标的方向。",
    )
    evaporation_rate = st.number_input(
        "rho（全局信息素挥发率）",
        min_value=0.0,
        max_value=0.99,
        value=float(defaults.evaporation_rate),
        step=0.05,
        key="p_rho",
        help="每轮结束后全局信息素衰减比例。",
    )
    pheromone_deposit_q = st.number_input(
        "Q（信息素沉积常数）",
        min_value=1.0,
        value=float(defaults.pheromone_deposit_q),
        step=1.0,
        key="p_q",
        help="成功路径每轮沉积信息素的基准强度。",
    )
    initial_pheromone = st.number_input(
        "初始信息素 tau0",
        min_value=0.1,
        value=float(defaults.initial_pheromone),
        step=0.1,
        key="p_tau0",
        help="所有可通行节点的初始信息素水平。",
    )
    local_evaporation_rate = st.number_input(
        "局部 rho（局部信息素挥发率）",
        min_value=0.0,
        max_value=0.99,
        value=float(defaults.local_evaporation_rate),
        step=0.01,
        key="p_local_rho",
        help="单只蚂蚁走过路径后执行局部更新的强度。",
    )
    elite_enabled = st.checkbox(
        "启用精英强化",
        value=bool(defaults.elite_enabled),
        key="p_elite_enabled",
        help="是否对当前全局最优路径进行额外信息素强化。",
    )
    elite_weight = st.number_input(
        "精英权重（最优路径额外强化倍数）",
        min_value=0.0,
        value=float(defaults.elite_weight),
        step=0.1,
        key="p_elite_weight",
        help="精英路径相对普通成功路径的额外强化倍数。",
    )
    random_seed = st.number_input(
        "随机种子",
        min_value=0,
        value=int(defaults.random_seed if defaults.random_seed is not None else 42),
        step=1,
        key="p_seed",
        help="固定随机过程，方便复现实验。",
    )

    return AcoParams(
        ant_count=int(ant_count),
        iterations=int(iterations),
        alpha=float(alpha),
        beta=float(beta),
        evaporation_rate=float(evaporation_rate),
        pheromone_deposit_q=float(pheromone_deposit_q),
        initial_pheromone=float(initial_pheromone),
        local_evaporation_rate=float(local_evaporation_rate),
        elite_enabled=bool(elite_enabled),
        elite_weight=float(elite_weight),
        random_seed=int(random_seed),
    )


def _run_example_mode(
    selected_map_path: Path,
    params: AcoParams,
    save_output: bool,
    run_clicked: bool,
) -> None:
    """运行“示例地图”模式。

    示例地图来自 `data/maps/` 下的 CSV 文件。这里负责展示地图元数据和预览图，
    真正点击运行后仍然调用统一的 `solve_path()`。
    """
    grid_map = load_grid_map(selected_map_path)
    metadata = get_map_metadata(selected_map_path.name)

    info_col, preview_col = st.columns([1.2, 0.8])
    with info_col:
        st.subheader("地图信息")
        relative_or_name = (
            selected_map_path.relative_to(Path.cwd())
            if selected_map_path.is_relative_to(Path.cwd())
            else selected_map_path.name
        )
        st.write(f"文件: `{relative_or_name}`")
        st.write(f"尺寸: `{grid_map.rows} x {grid_map.cols}`")
        st.write(f"起点: `{grid_map.start}`")
        st.write(f"终点: `{grid_map.goal}`")
        st.write(f"类别: `{metadata.category}`")
        st.write(f"特点: {metadata.description}")
        st.write(f"默认参数文件: `{DEFAULT_PARAM_FILE.name}`")
    with preview_col:
        st.subheader("地图预览")
        st.pyplot(
            plot_grid_map(
                grid_map,
                title="Map Preview",
                figure_size=(4.5, 4.5),
                compact=True,
            )
        )

    if not run_clicked:
        st.info("调整参数后点击“开始规划”执行路径搜索。")
        return

    # 用户点击开始规划后，才执行可能较耗时的求解过程。
    result = solve_path(grid_map, params)
    _render_results(grid_map, params, result, save_output)


def _render_drag_canvas(
    grid,
    grid_rows: int,
    grid_cols: int,
    cell_px: int,
    brush: str,
) -> None:
    """拖动绘制模式：鼠标松开后将笔画栅格化为地图格子。

    已绘制的地图作为 canvas 背景图；用户新画的 freedraw 笔画在背景上方。
    组件返回的 `image_data` 只包含新笔画图层，不包含背景，因此需要按 alpha 通道
    判断本次笔画经过了哪些格子。
    """
    st.caption(
        "按住鼠标拖动绘制：蓝色=起点，红色=终点，深色=障碍，橙色=擦除。"
        "起点与终点全图唯一，松开鼠标后生效。"
    )

    background = render_editor_canvas(grid, cell_px=cell_px)
    canvas_version = st.session_state.get("editor_canvas_version", 0)
    # 每次应用笔画后换一个 key，迫使组件清空上一笔 overlay，避免下次 rerun 重复计数。
    canvas_key = f"editor_drawable_{grid_rows}x{grid_cols}_{cell_px}_{canvas_version}"

    result = st_canvas(
        fill_color="rgba(0, 0, 0, 0)",
        stroke_width=max(2, cell_px // 2),
        stroke_color=_BRUSH_STROKE_COLORS.get(brush, "#30343f"),
        background_image=background,
        update_streamlit=True,
        height=grid_rows * cell_px,
        width=grid_cols * cell_px,
        drawing_mode="freedraw",
        key=canvas_key,
    )

    if result is None or result.image_data is None:
        return

    touched = cells_from_stroke_image(result.image_data, cell_px, grid_rows, grid_cols)
    if not touched:
        return

    # 把本次笔画影响的格子写回编辑器状态，并清除已保存路径标记。
    apply_brush_to_cells(grid, touched, brush)
    st.session_state["editor_grid"] = grid
    st.session_state["editor_saved_path"] = None
    st.session_state["editor_canvas_version"] = canvas_version + 1
    st.rerun()


def _render_click_canvas(
    grid,
    grid_rows: int,
    grid_cols: int,
    cell_px: int,
    brush: str,
) -> None:
    """点击绘制模式。

    这是拖动画布不可用或运行期失败时的降级方案。每次点击只修改一个格子，体验比
    拖动模式慢，但不影响核心功能。
    """
    st.caption("点击格子绘制：蓝色=起点，红色=终点，深色=障碍，浅色=空地。起点与终点全图唯一。")

    canvas_image = render_editor_canvas(grid, cell_px=cell_px)
    coords = streamlit_image_coordinates(canvas_image, key="editor_canvas")

    if coords is not None:
        click = (coords["x"], coords["y"])
        # Streamlit rerun 可能反复返回同一次点击坐标，这里去重避免重复触发。
        if st.session_state.get("editor_last_click") != click:
            st.session_state["editor_last_click"] = click
            cell = cell_from_click(coords["x"], coords["y"], cell_px, grid_rows, grid_cols)
            if cell is not None:
                apply_brush(grid, cell[0], cell[1], brush)
                st.session_state["editor_grid"] = grid
                st.session_state["editor_saved_path"] = None
                st.rerun()


def _run_custom_mode(params: AcoParams, save_output: bool, run_clicked: bool) -> None:
    """运行“自定义地图”模式。

    自定义地图保存在 `st.session_state["editor_grid"]` 中。页面层只管理交互状态，
    保存和校验逻辑交给 `custom_map.py`。
    """
    st.subheader("自定义地图编辑器")
    if not (_HAS_DRAWABLE_CANVAS or _HAS_IMAGE_COORDS):
        st.error(
            "缺少绘图组件，请运行 "
            "`pip install streamlit-drawable-canvas streamlit-image-coordinates` 后重新启动。"
        )
        return

    size_col1, size_col2, size_col3 = st.columns([1, 1, 1])
    with size_col1:
        rows = st.number_input("行数", min_value=2, max_value=40, value=10, step=1, key="editor_rows")
    with size_col2:
        cols = st.number_input("列数", min_value=2, max_value=40, value=10, step=1, key="editor_cols")
    with size_col3:
        st.write("")
        st.write("")
        create_clicked = st.button("创建 / 重置画布")

    if create_clicked or "editor_grid" not in st.session_state:
        # 初始化或重置编辑器状态。默认地图左上为起点、右下为终点。
        st.session_state["editor_grid"] = create_empty_grid(int(rows), int(cols))
        st.session_state["editor_last_click"] = None
        st.session_state["editor_saved_path"] = None
        st.session_state["editor_canvas_version"] = st.session_state.get("editor_canvas_version", 0) + 1

    grid = st.session_state["editor_grid"]
    grid_rows, grid_cols = int(grid.shape[0]), int(grid.shape[1])

    brush_label = st.radio(
        "选择画笔",
        ("障碍", "起点", "终点", "擦除"),
        horizontal=True,
        key="editor_brush",
    )
    brush = _BRUSH_BY_LABEL[brush_label]

    # 切换画笔时重置点击去重，这样同一格可以被新画笔重新涂色。
    if st.session_state.get("editor_prev_brush") != brush_label:
        st.session_state["editor_prev_brush"] = brush_label
        st.session_state["editor_last_click"] = None

    # 根据行列数自适应单格像素，保证大地图不会撑爆页面宽度。
    cell_px = max(10, min(30, _EDITOR_MAX_CANVAS_PX // max(grid_rows, grid_cols)))

    use_drag_canvas = _should_use_drag_canvas(
        _HAS_DRAWABLE_CANVAS,
        bool(st.session_state.get("editor_disable_drag_canvas", False)),
    )
    if use_drag_canvas:
        try:
            _render_drag_canvas(grid, grid_rows, grid_cols, cell_px, brush)
        except Exception as exc:  # pragma: no cover - depends on component runtime
            # 组件运行期失败后，本会话禁用拖动画布，避免每次 rerun 都再次触发异常。
            st.session_state["editor_disable_drag_canvas"] = True
            if not _HAS_IMAGE_COORDS:
                st.error(f"拖动画布组件运行失败，且点击版组件不可用：{exc}")
                return
            st.warning("拖动画布组件运行失败，已自动切换到点击绘制模式。")

    if not use_drag_canvas or st.session_state.get("editor_disable_drag_canvas", False):
        _render_click_canvas(grid, grid_rows, grid_cols, cell_px, brush)

    start_count, goal_count = count_markers(grid)
    ready = is_ready_to_save(grid)
    status_col1, status_col2 = st.columns(2)
    status_col1.metric("起点数量", start_count)
    status_col2.metric("终点数量", goal_count)
    if not ready:
        st.warning("需要恰好一个起点和一个终点，才能保存或规划。")

    st.subheader("保存地图")
    name_col, button_col = st.columns([2, 1])
    with name_col:
        map_name = st.text_input("地图名称（留空则按时间自动命名）", key="editor_name")
    with button_col:
        st.write("")
        st.write("")
        save_clicked = st.button("保存地图")

    if save_clicked:
        if not ready:
            st.error("地图尚未就绪，无法保存。")
        else:
            # 保存前先根据当前目录生成不冲突的最终文件名，再由 save_custom_map 做安全校验。
            existing = [path.name for path in discover_map_files(DEFAULT_MAP_DIR)]
            file_name = resolve_map_filename(map_name, existing)
            saved_path = save_custom_map(grid, file_name, DEFAULT_MAP_DIR)
            st.session_state["editor_saved_path"] = saved_path
            st.success(
                f"地图已保存：`{saved_path.name}`，可在“示例地图”来源中选择复用。"
            )

    if not run_clicked:
        st.info("绘制完成后，点击侧边栏“开始规划”。")
        return
    if not ready:
        st.error("地图尚未就绪（需要恰好一个起点和一个终点），无法规划。")
        return

    saved_path = st.session_state.get("editor_saved_path")
    # 如果用户已保存地图，则 source 使用保存路径；未保存时 source 为 None。
    grid_map = build_grid_map_from_array(grid, source=saved_path)
    result = solve_path(grid_map, params)
    _render_results(grid_map, params, result, save_output)


def _render_results(
    grid_map,
    params: AcoParams,
    result,
    save_output: bool,
) -> None:
    """展示求解结果，并按需保存输出产物。"""
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
    st.write(f"成功路径总数: `{result.total_successful_paths}`")
    st.write(result.message)

    if save_output:
        # Streamlit 运行结果统一保存到 data/outputs/streamlit/。
        saved_dir = save_planning_artifacts(
            grid_map=grid_map,
            params=params,
            result=result,
            surface="streamlit",
            output_root=DEFAULT_STREAMLIT_OUTPUT_DIR,
        )
        st.success(f"结果已保存到: `{saved_dir}`")

    row1_col1, row1_col2 = st.columns(2)
    with row1_col1:
        st.subheader("最终路径")
        st.pyplot(plot_grid_map(grid_map, result))
    with row1_col2:
        st.subheader("历史最优路径长度")
        st.pyplot(plot_convergence(result.history_best_length))

    row2_col1, row2_col2 = st.columns(2)
    with row2_col1:
        st.subheader("本轮最优 / 本轮平均路径长度")
        st.pyplot(
            plot_length_comparison(
                result.history_iteration_best_length,
                result.history_iteration_mean_length,
            )
        )
    with row2_col2:
        st.subheader("每轮成功路径数")
        st.pyplot(plot_success_count(result.history_success_count))

    st.subheader("路径坐标")
    st.code(format_path_coordinates(result.path), language="text")


def _load_defaults() -> AcoParams:
    """读取默认参数文件并构造 `AcoParams`。

    复用 CLI 的参数文件读取函数，保证 CLI 和 Streamlit 默认参数来源一致。
    """
    from .cli import _load_params_from_file

    defaults = _load_params_from_file(DEFAULT_PARAM_FILE)
    return AcoParams(**defaults)
