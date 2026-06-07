# 代码视角项目详解

本文档从代码实现角度讲解本项目。阅读目标不是介绍课题背景，而是回答以下问题：

- 程序从哪个入口启动？
- 地图、参数、结果在代码里分别是什么数据结构？
- 一张 `CSV` 地图如何变成可求解的 `GridMap`？
- 蚁群算法主循环具体怎么跑？
- CLI、Streamlit、自定义地图编辑器、输出保存和实验汇总分别如何调用核心模块？
- 当前测试覆盖了哪些代码路径？

项目采用 `src` 布局，核心包位于 `src/aco_path_planning/`。根目录下的 `main.py`、`streamlit_app.py` 和 `scripts/` 主要承担启动适配职责。

---

## 1. 代码目录与职责总览

```text
ant-colony-path-planning/
├── config/
│   └── aco_defaults.json
├── data/
│   ├── maps/
│   ├── maps/generated/
│   └── outputs/
├── scripts/
│   ├── generate_maps.py
│   ├── run_cli.py
│   ├── run_streamlit.py
│   └── summarize_results.py
├── src/
│   └── aco_path_planning/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── custom_map.py
│       ├── grid.py
│       ├── map_catalog.py
│       ├── map_loader.py
│       ├── models.py
│       ├── output_writer.py
│       ├── solver.py
│       ├── visualization.py
│       └── webapp.py
├── tests/
├── main.py
└── streamlit_app.py
```

核心职责可以概括为：

- `models.py`：定义项目内部共享的数据结构。
- `map_loader.py`：把外部 `CSV` 地图转换成内部 `GridMap`。
- `grid.py`：定义网格运动规则、邻居生成、路径长度和启发距离。
- `solver.py`：实现蚁群路径规划算法。
- `visualization.py`：生成路径图、收敛图和编辑器画布。
- `output_writer.py`：保存图片、路径文本和结构化 JSON。
- `cli.py`：命令行参数解析、参数合并、调用求解和输出结果。
- `webapp.py`：Streamlit 图形界面。
- `custom_map.py`：自定义地图编辑器的纯逻辑。
- `map_catalog.py`：示例地图的展示名、分类和说明。
- `scripts/*.py`：提供可直接运行的脚本入口和工具脚本。

代码组织的核心原则是：算法逻辑不依赖界面，界面逻辑不直接操作底层 CSV 细节，输入校验集中在加载模块和数据模型中。

---

## 2. 启动入口与调用链

项目有两个用户入口：命令行入口和 Streamlit 入口。

### 2.1 命令行入口

根目录 `main.py` 内容很薄：

```python
from scripts.run_cli import main

if __name__ == "__main__":
    raise SystemExit(main())
```

它只负责转发到 `scripts/run_cli.py`。真正的脚本入口会先把 `src` 目录加入 `sys.path`：

```python
PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from aco_path_planning.cli import main
```

这样做的目的，是让项目即使没有安装成 Python 包，也能直接通过：

```bash
python main.py
python scripts/run_cli.py
```

运行。

命令行完整调用链是：

```text
main.py
  -> scripts/run_cli.py
    -> aco_path_planning.cli.main()
      -> build_params()
      -> load_grid_map()
      -> solve_path()
      -> save_planning_artifacts()  # 仅当 --save-output 启用
      -> visualization 绘图        # 仅当未启用 --no-plot
```

### 2.2 Streamlit 入口

根目录 `streamlit_app.py` 同样只做转发：

```python
from scripts.run_streamlit import main

if __name__ == "__main__":
    main()
```

`scripts/run_streamlit.py` 将 `src` 加入 `sys.path` 后调用：

```python
from aco_path_planning.webapp import main
```

因此 Streamlit 的完整调用链是：

```text
streamlit_app.py
  -> scripts/run_streamlit.py
    -> aco_path_planning.webapp.main()
      -> _load_defaults()
      -> _render_sidebar_params()
      -> _run_example_mode() 或 _run_custom_mode()
      -> solve_path()
      -> _render_results()
      -> save_planning_artifacts()  # 如果勾选保存结果
```

---

## 3. 配置与路径管理

`src/aco_path_planning/config.py` 集中定义项目路径：

```python
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_MAP_DIR = PROJECT_ROOT / "data" / "maps"
DEFAULT_GENERATED_MAP_DIR = DEFAULT_MAP_DIR / "generated"
DEFAULT_PARAM_FILE = PROJECT_ROOT / "config" / "aco_defaults.json"
DEFAULT_OUTPUT_ROOT = PROJECT_ROOT / "data" / "outputs"
DEFAULT_CLI_OUTPUT_DIR = DEFAULT_OUTPUT_ROOT / "cli"
DEFAULT_STREAMLIT_OUTPUT_DIR = DEFAULT_OUTPUT_ROOT / "streamlit"
```

这里的 `PROJECT_ROOT` 从 `src/aco_path_planning/config.py` 向上两层得到项目根目录。这样 CLI、Streamlit、脚本和测试都可以复用同一套路径定义，避免每个入口自己拼路径。

默认参数文件是 `config/aco_defaults.json`：

```json
{
  "ant_count": 50,
  "iterations": 100,
  "alpha": 1.0,
  "beta": 4.0,
  "evaporation_rate": 0.3,
  "pheromone_deposit_q": 100.0,
  "initial_pheromone": 1.0,
  "local_evaporation_rate": 0.05,
  "elite_enabled": true,
  "elite_weight": 2.0,
  "random_seed": 42
}
```

CLI 的参数优先级为：

1. `AcoParams` 代码内默认值。
2. `config/aco_defaults.json`。
3. 命令行参数覆盖。

对应逻辑在 `cli.build_params()` 中完成。

---

## 4. 核心数据模型

`models.py` 定义三个核心模型：`GridMap`、`AcoParams`、`PlanningResult`。

### 4.1 坐标类型

```python
Coordinate = tuple[int, int]
```

项目统一使用 `(row, col)` 表示坐标，而不是 `(x, y)`。这和 NumPy 二维数组索引一致：

```python
grid[row, col]
```

文档、输出和测试都应保持这一约定。

### 4.2 GridMap

```python
@dataclass(frozen=True)
class GridMap:
    grid: np.ndarray
    start: Coordinate
    goal: Coordinate
    source: Path | None = None
```

`GridMap` 是算法真正使用的地图结构。注意一个重要设计：加载后 `grid` 只保留两类值：

- `0`：可通行
- `1`：障碍物

起点和终点不继续保存在 `grid` 的数值中，而是存到 `start` 和 `goal` 字段里。这样算法判断某个格子能否通行时，只需要看 `grid[row, col] == 0`。

`GridMap` 提供三个属性：

```python
rows          # 行数
cols          # 列数
walkable_mask # grid == 0 的布尔矩阵
```

`walkable_mask` 在求解器中用于初始化和更新可通行格的信息素。

### 4.3 AcoParams

`AcoParams` 保存所有蚁群算法参数：

```python
ant_count: int = 50
iterations: int = 100
alpha: float = 1.0
beta: float = 4.0
evaporation_rate: float = 0.3
pheromone_deposit_q: float = 100.0
initial_pheromone: float = 1.0
local_evaporation_rate: float = 0.05
elite_enabled: bool = True
elite_weight: float = 2.0
random_seed: int | None = 42
```

其中：

- `ant_count`：每轮派出的蚂蚁数量。
- `iterations`：总迭代轮数。
- `alpha`：信息素重要程度。
- `beta`：启发函数重要程度。
- `evaporation_rate`：全局挥发率。
- `pheromone_deposit_q`：路径沉积常数。
- `initial_pheromone`：可通行格初始信息素。
- `local_evaporation_rate`：局部信息素回拉系数。
- `elite_enabled`：是否启用精英强化。
- `elite_weight`：精英路径额外沉积倍数。
- `random_seed`：随机种子。

`validate()` 会在求解开始前检查所有参数：

- `ant_count`、`iterations` 必须是正整数。
- `alpha`、`beta` 必须非负。
- `evaporation_rate`、`local_evaporation_rate` 必须在 `[0, 1)`。
- `pheromone_deposit_q`、`initial_pheromone` 必须大于 0。
- `elite_weight` 必须非负。
- 数值参数必须是有限数，拒绝 `NaN` 和 `inf`。
- `random_seed` 必须是整数或 `None`。
- `elite_enabled` 必须是布尔值。
- 布尔值不能伪装成整数参数。

这一步可以防止错误参数进入算法主循环后导致难定位的问题。

### 4.4 PlanningResult

`PlanningResult` 是求解器的返回结果：

```python
found: bool
path: list[Coordinate]
path_length: float
best_iteration: int | None
history_best_length: list[float]
history_iteration_best_length: list[float]
history_iteration_mean_length: list[float]
history_success_count: list[int]
total_successful_paths: int
runtime_seconds: float
message: str
```

它不只保存最终路径，还保存四类过程指标：

- `history_best_length`：截至每轮的历史最优路径长度。
- `history_iteration_best_length`：每轮内部成功路径中的最短长度。
- `history_iteration_mean_length`：每轮内部成功路径的平均长度。
- `history_success_count`：每轮成功到达终点的蚂蚁数量。

这些字段直接支撑可视化曲线、实验汇总和课程报告分析。

---

## 5. 地图加载与校验

地图加载逻辑在 `map_loader.py`。

### 5.1 外部 CSV 格式

CSV 中允许的值是：

- `0`：空地
- `1`：障碍物
- `2`：起点
- `3`：终点

例如：

```csv
2,0,0,0
1,1,0,1
0,0,0,0
1,0,1,3
```

### 5.2 load_grid_map()

`load_grid_map(path)` 的流程是：

1. 检查文件是否存在。
2. 使用 `csv.reader` 逐行读取。
3. 跳过空行。
4. 将每个单元格去空格后转成整数。
5. 检查值是否属于 `{0, 1, 2, 3}`。
6. 检查地图非空。
7. 检查每一行宽度一致，即必须是矩形。
8. 转成 `np.ndarray`。
9. 调用 `build_grid_map_from_cells()` 统一构建 `GridMap`。

这里有两个细节：

- 文件用 `utf-8-sig` 打开，可以兼容带 BOM 的 CSV。
- 空行会被忽略，但非空行必须宽度一致。

### 5.3 build_grid_map_from_cells()

这个函数同时服务于 CSV 加载和自定义地图编辑器。它做更底层的统一校验：

1. 输入必须是非空二维数组。
2. 值只能是 `0/1/2/3`。
3. 必须恰好一个起点 `2`。
4. 必须恰好一个终点 `3`。
5. 将原始网格归一化：

```python
normalized_grid = np.where(raw_grid == 1, 1, 0).astype(np.int8)
```

归一化后，起点和终点在 `grid` 中都变成可通行格 `0`，而它们的坐标单独保存：

```python
start = tuple(int(value) for value in start_positions[0])
goal = tuple(int(value) for value in goal_positions[0])
```

这保证算法只面对“障碍 / 可通行”两种格子，起终点逻辑由模型字段表达。

### 5.4 discover_map_files()

```python
def discover_map_files(directory: str | Path) -> list[Path]:
    root = Path(directory)
    if not root.exists():
        return []
    return sorted(path for path in root.glob("*.csv") if path.is_file())
```

它只发现指定目录下一层的 `.csv` 文件，不递归。Streamlit 示例地图选择和自定义地图保存后的复用都依赖它。

---

## 6. 网格运动规则

网格规则在 `grid.py`，它不依赖蚁群算法，只描述“地图上能怎么走”。

### 6.1 移动代价

```python
ORTHOGONAL_COST = 1.0
DIAGONAL_COST = math.sqrt(2.0)
```

直行代价为 `1.0`，对角线代价为 `sqrt(2)`。

### 6.2 8 邻域偏移

`NEIGHBOR_OFFSETS` 包含 8 个方向：

- 左上、上、右上
- 左、右
- 左下、下、右下

每个方向同时携带移动代价。

### 6.3 is_in_bounds() 与 is_walkable()

`is_in_bounds()` 判断坐标是否在地图范围内。  
`is_walkable()` 先检查范围，再判断 `grid[row, col] == 0`。

这两个函数是后续邻居生成和防穿角判断的基础。

### 6.4 get_neighbors()

`get_neighbors(grid_map, coordinate)` 返回当前位置可走的邻居列表：

```python
list[tuple[Coordinate, float]]
```

每个元素包含：

- 邻居坐标
- 从当前格到该邻居的移动代价

流程：

1. 遍历 8 个方向。
2. 计算候选坐标。
3. 不可通行则跳过。
4. 如果是对角移动，调用 `_can_move_diagonally()`。
5. 合法则加入结果。

### 6.5 防穿角规则

对角移动时，必须保证两个相邻的正交格都可通行：

```python
adjacent_one = (current_row, next_col)
adjacent_two = (next_row, current_col)
return is_walkable(grid_map, adjacent_one) and is_walkable(grid_map, adjacent_two)
```

例如从 `(1, 1)` 斜走到 `(0, 0)` 时，必须 `(1, 0)` 和 `(0, 1)` 都可通行。否则路径会从障碍物角点中穿过去，这在实际运动中不合理。

### 6.6 path_length()

`path_length(path)` 用于计算最终路径长度：

- 相邻直行步加 `1.0`。
- 相邻对角步加 `sqrt(2)`。
- 如果出现跳格、原地不动或非邻接移动，直接抛 `ValueError`。

这种严格校验保证输出路径一定符合网格运动规则。

### 6.7 distance_to_goal()

启发函数使用 octile 距离：

```python
diagonal_steps = min(row_delta, col_delta)
straight_steps = max(row_delta, col_delta) - diagonal_steps
return diagonal_steps * DIAGONAL_COST + straight_steps * ORTHOGONAL_COST
```

在 8 邻域场景下，octile 距离比曼哈顿距离更贴近实际移动代价，因此被用于蚂蚁选择下一步时的启发信息。

---

## 7. 蚁群求解器

核心算法在 `solver.py`。

### 7.1 solve_path() 总体流程

入口函数：

```python
def solve_path(grid_map: GridMap, params: AcoParams) -> PlanningResult:
```

总体流程如下：

```text
校验参数
记录开始时间
创建随机数生成器
初始化信息素矩阵
初始化最优路径和历史指标

for iteration in 1..iterations:
    successful_paths = []

    for 每只蚂蚁:
        构建路径
        对该路径执行局部信息素更新
        如果到达终点:
            计算路径长度
            加入本轮成功路径
            更新全局最优

    对所有可通行格执行全局挥发
    对本轮成功路径执行信息素沉积
    如开启精英强化，则强化全局最优路径
    记录本轮统计指标

计算运行耗时
返回 PlanningResult
```

### 7.2 参数校验

`solve_path()` 的第一句是：

```python
params.validate()
```

这意味着无论调用来自 CLI、Streamlit 还是测试，只要进入求解器，都会经过统一的参数校验。

### 7.3 随机数生成器

```python
rng = np.random.default_rng(params.random_seed)
```

所有随机选择都来自这个生成器。固定 `random_seed` 后，同一地图和同一参数下的结果更容易复现。

### 7.4 信息素矩阵

```python
pheromone = np.zeros((grid_map.rows, grid_map.cols), dtype=float)
pheromone[grid_map.walkable_mask] = params.initial_pheromone
```

信息素矩阵和地图同形。障碍格信息素始终为 `0`，可通行格初始化为 `initial_pheromone`。

本项目采用的是“节点信息素”：信息素存在格子上，而不是存在边上。这样实现更直接，但对方向性的表达不如边信息素细。

### 7.5 单只蚂蚁构建路径

单只蚂蚁的逻辑在 `_build_ant_path()`：

```python
current = grid_map.start
goal = grid_map.goal
visited = {current}
path = [current]
max_steps = grid_map.rows * grid_map.cols
```

它从起点出发，维护：

- `current`：当前位置。
- `visited`：已经访问过的格子，避免原地绕圈。
- `path`：当前路径。
- `max_steps`：最多走 `rows * cols` 步，防止无限循环。

每一步：

1. 如果当前位置就是终点，返回成功。
2. 调用 `get_neighbors()` 获取合法邻居。
3. 过滤掉已访问坐标。
4. 如果没有可走邻居，返回失败。
5. 调用 `_calculate_weights()` 计算选择概率。
6. 使用 `rng.choice(..., p=weights)` 按概率选择下一格。
7. 把下一格加入路径和已访问集合。

### 7.6 状态转移概率

候选邻居权重在 `_calculate_weights()` 中计算：

```python
tau = max(pheromone[row, col], 1e-12)
eta = 1.0 / (distance_to_goal(coordinate, goal) + 1e-6)
raw_weights[index] = (tau ** alpha) * (eta ** beta)
```

含义：

- `tau`：候选格的信息素强度。
- `eta`：候选格到终点距离的倒数。
- `alpha`：信息素权重。
- `beta`：启发函数权重。

公式：

```text
weight(j) = tau(j)^alpha * eta(j)^beta
```

然后归一化：

```python
return raw_weights / total_weight
```

如果权重和不是有限数或小于等于 0，则退化为均匀分布：

```python
return np.full(len(feasible_neighbors), 1.0 / len(feasible_neighbors))
```

这个兜底可以避免极端数值导致 `rng.choice()` 收到非法概率。

### 7.7 局部信息素更新

每只蚂蚁走完后，无论成功与否，都会对其路径执行局部更新：

```python
pheromone[row, col] = (
    (1.0 - local_evaporation_rate) * pheromone[row, col]
    + local_evaporation_rate * initial_pheromone
)
```

作用是把走过路径的信息素往初始值拉回，减弱后续蚂蚁过度跟随同一路径的概率。

如果 `local_evaporation_rate <= 0`，函数直接返回，等于关闭局部更新。

### 7.8 全局挥发

每轮所有蚂蚁走完后，对所有可通行格执行全局挥发：

```python
pheromone[grid_map.walkable_mask] *= 1.0 - params.evaporation_rate
```

挥发用于削弱旧经验，避免早期路径永远占优势。

### 7.9 成功路径沉积

对本轮成功到达终点的路径，按路径长度反比沉积信息素：

```python
deposit = params.pheromone_deposit_q / max(candidate_length, 1e-9)
for row, col in candidate_path:
    pheromone[row, col] += deposit
```

路径越短，`deposit` 越大，因此短路径会在后续迭代中更容易被选择。

### 7.10 精英强化

如果开启 `elite_enabled` 且已经存在全局最优路径，则对全局最优路径额外沉积：

```python
elite_deposit = (
    params.elite_weight * params.pheromone_deposit_q / max(best_length, 1e-9)
)
for row, col in best_path:
    pheromone[row, col] += elite_deposit
```

精英强化有助于加快收敛，但如果权重过大，也可能过早强化当前次优路径。因此代码把它设计成可开关、可调权重的策略。

### 7.11 历史指标记录

每轮结束后记录：

```python
history_iteration_best_length.append(min(iteration_lengths))
history_iteration_mean_length.append(sum(iteration_lengths) / len(iteration_lengths))
history_best_length.append(best_length)
history_success_count.append(len(successful_paths))
```

如果本轮没有任何成功路径：

```python
history_iteration_best_length.append(math.inf)
history_iteration_mean_length.append(math.inf)
```

历史最优 `history_best_length` 仍记录当前全局最优。如果从头到尾没有成功路径，它会一直是 `inf`，后续保存 JSON 时会转成 `null`。

### 7.12 成功与失败返回

如果找到过路径：

```python
PlanningResult(
    found=True,
    path=best_path,
    path_length=best_length,
    best_iteration=best_iteration,
    message="Path found successfully.",
)
```

如果没有找到路径：

```python
PlanningResult(
    found=False,
    path=[],
    path_length=math.inf,
    best_iteration=None,
    message="No feasible path found under the current map and parameters.",
)
```

失败结果仍包含完整的历史数组和成功路径统计，这样无解场景也可以被保存和汇总。

---

## 8. 命令行模块

命令行逻辑在 `cli.py`。

### 8.1 parse_args()

CLI 支持的关键参数包括：

- `--map`：地图文件路径。
- `--params`：默认参数 JSON 文件。
- `--ants`：蚂蚁数量。
- `--iterations`：迭代次数。
- `--alpha`、`--beta`：状态转移权重。
- `--rho`：全局挥发率。
- `--q`：信息素沉积常数。
- `--initial-pheromone`：初始信息素。
- `--local-rho`：局部信息素更新率。
- `--elite-weight`：精英强化权重。
- `--disable-elite`：关闭精英强化。
- `--seed`：随机种子。
- `--save-output`：保存结果。
- `--output-dir`：输出根目录。
- `--no-plot`：不弹出 Matplotlib 窗口。

### 8.2 build_params()

参数合并逻辑：

```python
base_params = _load_params_from_file(args.param_file)
overrides = {...}
merged = {**base_params, **非 None 的命令行覆盖项}
if args.disable_elite:
    merged["elite_enabled"] = False
return AcoParams(**merged)
```

设计要点：

- JSON 文件不存在时，回退到 `AcoParams()` 默认值。
- JSON 文件只读取 `AcoParams` 已知字段，忽略未知字段。
- 命令行只覆盖用户实际传入的参数。
- `--disable-elite` 单独处理，因为它是布尔开关。

### 8.3 main()

CLI 主流程：

1. 解析命令行参数。
2. 构造 `AcoParams`。
3. 加载地图。
4. 调用 `solve_path()`。
5. 打印地图、起点、终点、是否找到路径、路径长度和路径坐标。
6. 打印运行耗时和成功路径总数。
7. 如果启用 `--save-output`，保存结果文件。
8. 如果未启用 `--no-plot`，显示路径图和收敛曲线。

异常处理覆盖：

- `FileNotFoundError`
- `ValueError`
- `json.JSONDecodeError`

出现这些异常时打印到 stderr 并返回退出码 `1`。

---

## 9. 可视化模块

可视化逻辑在 `visualization.py`，主要返回 Matplotlib figure 或 PIL image，而不是直接保存文件。

### 9.1 plot_grid_map()

功能：

- 绘制障碍物和空地。
- 标注起点和终点。
- 如果提供 `PlanningResult`，绘制最优路径。
- 支持 `compact=True` 用于 Streamlit 小预览。

坐标转换要注意：

- 数据坐标是 `(row, col)`。
- Matplotlib 绘图时横轴是 `col`，纵轴是 `row`。

所以路径绘制时：

```python
x_coords = [coordinate[1] for coordinate in result.path]
y_coords = [coordinate[0] for coordinate in result.path]
```

### 9.2 plot_convergence()

绘制历史最优路径长度：

```python
y_values = [value if math.isfinite(value) else np.nan for value in history_best_length]
```

把 `inf` 转成 `np.nan`，这样无解或暂时无成功路径时曲线不会画出错误的无限值。

### 9.3 plot_length_comparison()

绘制两条曲线：

- 每轮成功路径中的最短长度。
- 每轮成功路径的平均长度。

这张图用于观察某一轮内部的搜索质量，而不是只看历史最优。

### 9.4 plot_success_count()

绘制每轮成功路径数量。它可以反映参数是否让蚂蚁更容易找到通路。

### 9.5 format_path_coordinates()

将路径格式化为：

```text
(0, 0) -> (0, 1) -> (1, 2)
```

空路径返回：

```text
[]
```

CLI、输出文件和 Streamlit 路径展示都复用这个函数。

### 9.6 编辑器画布渲染

`render_editor_canvas()` 把一个编辑器原始网格渲染为 PIL 图片：

- `0`：浅色空地
- `1`：深色障碍
- `2`：蓝色起点
- `3`：红色终点

`cell_from_click()` 把点击坐标转成 `(row, col)`：

```python
col = int(x // cell_px)
row = int(y // cell_px)
```

这是点击版自定义地图编辑器的基础。

---

## 10. 输出保存模块

输出保存逻辑在 `output_writer.py`。

### 10.1 save_planning_artifacts()

入口函数：

```python
save_planning_artifacts(
    grid_map=grid_map,
    params=params,
    result=result,
    surface="cli" 或 "streamlit",
    output_root=...
)
```

它会生成一个独立输出目录，目录名包含：

- 时间戳，精确到微秒。
- 地图文件名 stem。

例如：

```text
data/outputs/cli/20260604_172335_123456_easy_alt/
```

### 10.2 输出文件

每次保存会写出：

```text
path_plot.png
convergence_plot.png
iteration_length_plot.png
success_count_plot.png
path.txt
result.json
```

其中：

- `path_plot.png`：地图和最优路径。
- `convergence_plot.png`：历史最优曲线。
- `iteration_length_plot.png`：本轮最优和本轮平均曲线。
- `success_count_plot.png`：每轮成功路径数量。
- `path.txt`：路径坐标文本。
- `result.json`：结构化结果。

### 10.3 result.json 内容

`result.json` 包含：

- 地图名称和路径。
- 来源界面：`cli` 或 `streamlit`。
- 保存时间。
- 是否找到路径。
- 路径长度。
- 最优轮次。
- 路径坐标。
- 消息文本。
- 运行耗时。
- 总成功路径数。
- 全部 ACO 参数。
- 四类历史曲线数组。

这使得单次运行结果可以完整复现和后续汇总。

### 10.4 唯一输出目录

`_create_unique_run_dir()` 使用最多 1000 次序号尝试：

```python
candidate = output_root / f"{directory_name}{suffix}"
candidate.mkdir()
```

如果同名目录已经存在，会尝试 `_1`、`_2` 等后缀。这样可以避免同一秒或同一地图多次保存时混写产物。

### 10.5 标准 JSON 处理

Python 默认允许把 `math.inf` 写成非标准 JSON 的 `Infinity`。项目通过两层处理避免这个问题：

1. `_json_safe()` 递归把非有限浮点数转成 `None`。
2. `json.dumps(..., allow_nan=False)` 禁止再次写出 `NaN` 或 `Infinity`。

因此无解结果中的 `path_length=inf` 会保存为：

```json
"path_length": null
```

---

## 11. 实验汇总脚本

`scripts/summarize_results.py` 用于扫描输出目录并生成 `summary.csv`。

### 11.1 collect_results()

它会递归查找：

```text
input_dir/**/result.json
```

对每个 `result.json`：

1. 读取 JSON。
2. 读取同目录下可选的 `experiment_label.txt`。
3. 提取地图、结果、耗时、成功路径数和参数。
4. 计算：
   - 平均每轮成功数。
   - 历史最优曲线最终有限值。
   - 本轮最优曲线最终有限值。
   - 本轮平均曲线最终有限值。
5. 记录结果目录路径。

### 11.2 summary.csv 字段

输出字段包括：

```text
experiment_label
surface
map_name
found
path_length
best_iteration
runtime_seconds
total_successful_paths
avg_success_count
best_length_curve_final
iteration_best_curve_final
iteration_mean_curve_final
ant_count
iterations
alpha
beta
evaporation_rate
pheromone_deposit_q
initial_pheromone
local_evaporation_rate
elite_enabled
elite_weight
random_seed
result_dir
```

这些字段足够支撑实验结果表和参数复现。

### 11.3 _last_finite()

曲线中可能含有无穷大，尤其是无解或某轮没有成功路径时。`_last_finite()` 从末尾向前找最后一个有限值，找不到则返回 `None`。

---

## 12. 地图目录与元数据

`map_catalog.py` 定义示例地图的展示信息。

### 12.1 MapMetadata

```python
@dataclass(frozen=True)
class MapMetadata:
    display_name: str
    category: str
    description: str
    expected_solvable: bool
    start: tuple[int, int]
    goal: tuple[int, int]
    analysis_ready: bool = False
```

这些字段主要服务 Streamlit 界面和测试：

- `display_name`：界面下拉框展示名。
- `category`：地图类别。
- `description`：地图特点说明。
- `expected_solvable`：预期是否可解。
- `start`、`goal`：用于和实际 CSV 校验。
- `analysis_ready`：标记适合做收敛分析的地图。

### 12.2 MAP_CATALOG

`MAP_CATALOG` 包含多类地图：

- 基础可达图
- 中等绕障图
- 无解图
- 狭窄通道图
- 小型迷宫图
- 高障碍密度图
- 大图稀疏障碍
- 大图密集障碍
- 大图无解

### 12.3 自定义地图兜底元数据

对于不在 `MAP_CATALOG` 中的地图，例如用户从前端保存的自定义地图：

```python
category = "custom"
display_name = f"custom / {stem}"
description = "自定义地图，由前端编辑器保存。"
```

这样 Streamlit 遇到未知地图时不会抛 `KeyError`，而是能正常展示。

### 12.4 排序逻辑

`get_sorted_map_files()` 按类别顺序和展示名排序。未知类别排在最后，因此自定义地图不会打乱精选地图顺序。

---

## 13. 自定义地图编辑器纯逻辑

自定义地图逻辑在 `custom_map.py`，它不依赖 Streamlit，因此可以单独测试。

### 13.1 原始编辑网格

编辑器网格仍使用原始值：

- `EMPTY = 0`
- `OBSTACLE = 1`
- `START = 2`
- `GOAL = 3`

这和 CSV 文件格式一致。

### 13.2 create_empty_grid()

创建空地图：

```python
grid = np.zeros((rows, cols), dtype=np.int8)
grid[0, 0] = START
grid[rows - 1, cols - 1] = GOAL
```

要求行列都至少为 `2`，因为至少需要容纳一个起点和一个终点。

### 13.3 apply_brush()

支持四种画笔：

- `obstacle`
- `start`
- `goal`
- `erase`

起点和终点必须唯一，所以画起点或终点时，会先清掉之前同类标记：

```python
if target_value in (START, GOAL):
    grid[grid == target_value] = EMPTY
```

### 13.4 拖动笔画栅格化

拖动画布返回 RGBA 图片层。代码取 alpha 通道判断哪些格子被笔画经过：

```python
alpha = array[:, :, 3]
```

`cells_from_stroke_alpha()` 会按格子切分像素块，计算 alpha 超过阈值的像素占比。如果占比超过 `min_coverage`，就认为该格被触碰。

这样可以过滤抗锯齿导致的微弱边缘像素，避免画一格时误伤邻格。

### 13.5 多格起终点笔画

障碍和擦除画笔会作用于所有触碰格。  
起点和终点只能有一个，因此多格笔画会收敛为一个代表格：

```python
_pick_single_cell(cells)
```

代表格选择逻辑是：找距离触碰格集合质心最近的格子。

### 13.6 保存前校验

`is_ready_to_save()` 要求：

```python
start_count == 1 and goal_count == 1
```

`save_custom_map()` 写文件前还会调用：

```python
build_grid_map_from_array(grid)
```

这样可以保证保存到磁盘的地图一定能被加载器正常读回。

### 13.7 文件命名安全

用户输入地图名时，代码会：

- 去掉路径，只保留 stem。
- 将不安全字符替换为 `_`。
- 空名时使用 `custom_<时间戳>_<序号>`。
- 同名时自动追加 `_1`、`_2`。

直接保存入口 `_safe_csv_filename()` 更严格：

- 文件名不能为空。
- 不能包含路径。
- 扩展名必须是 `.csv` 或无扩展名。
- stem 必须和清洗结果一致。

保存时使用 `open("x")`，如果文件已存在会抛 `FileExistsError`，避免静默覆盖。

---

## 14. Streamlit 界面代码

Streamlit 界面在 `webapp.py`。

### 14.1 组件兼容处理

项目使用 `streamlit-drawable-canvas==0.9.3` 支持拖动绘制。但该组件较旧，依赖 Streamlit 内部函数 `image_to_url` 的旧位置和旧签名。

`_patch_image_to_url()` 做兼容垫片：

1. 尝试导入旧模块位置 `streamlit.elements.image`。
2. 尝试导入新位置的 `image_to_url` 和 `LayoutConfig`。
3. 构造 `image_to_url_compat()`，把旧组件传入的整数宽度包装成 `LayoutConfig(width=width)`。
4. 挂回旧模块位置。

如果补丁失败，拖动画布不可用时，界面会尝试回退到点击版编辑器。

### 14.2 main()

`webapp.main()` 的职责：

1. 读取默认参数。
2. 设置页面标题和布局。
3. 在侧边栏选择地图来源。
4. 渲染参数控件。
5. 渲染“保存本次结果”和“开始规划”按钮。
6. 根据地图来源进入示例地图模式或自定义地图模式。

### 14.3 参数侧边栏

`_render_sidebar_params()` 使用 Streamlit 输入组件构造 `AcoParams`。每个参数都有合理的最小值、步长和中文提示。

比如：

- 蚂蚁数量和迭代次数用 `number_input`，最小为 `1`。
- `alpha`、`beta` 最小为 `0`。
- 全局和局部挥发率最大为 `0.99`。
- 精英强化用 `checkbox`。

最后返回一个新的 `AcoParams`。

### 14.4 示例地图模式

`_run_example_mode()` 流程：

1. 调用 `load_grid_map()` 加载选中 CSV。
2. 调用 `get_map_metadata()` 获取展示信息。
3. 左侧显示文件、尺寸、起点、终点、类别和特点。
4. 右侧用 `plot_grid_map(..., compact=True)` 预览地图。
5. 如果点击“开始规划”，调用 `solve_path()`。
6. 调用 `_render_results()` 展示结果。

### 14.5 自定义地图模式

`_run_custom_mode()` 管理编辑器状态：

- `editor_grid`：当前编辑网格。
- `editor_last_click`：点击版去重。
- `editor_saved_path`：保存后的 CSV 路径。
- `editor_canvas_version`：拖动画布 key 版本，用来清空上一次 stroke overlay。
- `editor_disable_drag_canvas`：运行期异常后禁用拖动画布。

用户流程：

1. 设置行数和列数。
2. 创建或重置画布。
3. 选择画笔。
4. 绘制地图。
5. 查看起点和终点数量。
6. 可选保存地图。
7. 点击开始规划。

如果地图还没有恰好一个起点和一个终点，保存和规划都会被阻止。

### 14.6 拖动画布模式

`_render_drag_canvas()` 使用 `st_canvas()`：

- 背景图来自 `render_editor_canvas()`。
- 用户自由绘制 stroke。
- 组件返回 stroke 图层。
- `cells_from_stroke_image()` 将 stroke 图层栅格化。
- `apply_brush_to_cells()` 更新编辑网格。
- 更新 `editor_canvas_version` 并 `st.rerun()`。

如果组件运行时抛异常，代码会设置：

```python
st.session_state["editor_disable_drag_canvas"] = True
```

然后回退到点击版。

### 14.7 点击版画布模式

`_render_click_canvas()` 使用 `streamlit_image_coordinates()`：

1. 把网格渲染成 PIL 图片。
2. 捕获点击坐标。
3. 调用 `cell_from_click()` 转成格子坐标。
4. 调用 `apply_brush()` 更新单个格子。

点击版没有拖动画笔体验，但能保证基本绘图功能可用。

### 14.8 结果展示

`_render_results()` 显示：

- 是否找到路径。
- 路径长度。
- 最优轮次。
- 运行耗时。
- 成功路径总数。
- 结果消息。
- 最终路径图。
- 历史最优曲线。
- 本轮最优 / 本轮平均曲线。
- 每轮成功路径数。
- 路径坐标文本。

如果勾选保存结果，则调用 `save_planning_artifacts()`，输出到 `data/outputs/streamlit/`。

---

## 15. 地图生成脚本

`scripts/generate_maps.py` 用于生成额外实验地图。

### 15.1 参数

支持：

- `--mode`：`maze`、`dense`、`large_sparse`
- `--rows`
- `--cols`
- `--density`
- `--seed`
- `--name`

输出目录固定为：

```text
data/maps/generated/
```

### 15.2 build_grid()

生成流程：

1. 要求地图至少 `2 x 2`。
2. 默认起点 `(0, 0)`，终点 `(rows - 1, cols - 1)`。
3. 根据模式放置障碍。
4. 调用 `carve_path()` 打通一条从起点到终点的基础路径。
5. 写入起点值 `2` 和终点值 `3`。

这保证生成地图至少包含一条可行通路。

### 15.3 safe_output_stem()

脚本复用 `custom_map.sanitize_map_name()` 清洗输出名。如果清洗后为空，抛出 `ValueError`。

---

## 16. 测试覆盖

项目使用 `unittest`。测试目录覆盖了核心模块和关键边界。

### 16.1 地图加载测试

`tests/test_map_loader.py` 覆盖：

- 正常读取起点、终点和障碍。
- 多起点报错。
- 非矩形地图报错。
- 非法单元格值报错。
- 缺起点报错。
- 缺终点报错。
- 多终点报错。

### 16.2 网格规则测试

`tests/test_grid.py` 覆盖：

- 对角穿角会被禁止。
- 路径长度包含对角代价。
- 跳格路径会报错。
- 原地不动路径会报错。

### 16.3 求解器测试

`tests/test_solver.py` 覆盖：

- 简单地图能找到路径。
- 中等地图能找到路径。
- 小无解图返回失败。
- 大无解图返回失败。
- 成功路径从起点开始、以终点结束。
- 每一步都必须是合法邻居。
- 历史曲线长度等于迭代次数。
- 运行耗时和成功路径数正常记录。

### 16.4 参数测试

`tests/test_params.py` 覆盖：

- 非正蚂蚁数量和迭代次数。
- 负 `alpha`、`beta`。
- 越界挥发率。
- 非正 `Q` 和初始信息素。
- 负精英权重。
- 非有限浮点数。
- 错误随机种子类型。
- 错误精英开关类型。
- 布尔值伪装成整数参数。

### 16.5 CLI 测试

`tests/test_cli.py` 覆盖：

- JSON 参数文件读取。
- 命令行参数覆盖。
- `--disable-elite` 关闭精英强化。
- 新增参数如 `local_rho`、`elite_weight`、`seed` 能正确进入 `AcoParams`。

### 16.6 输出测试

`tests/test_outputs.py` 覆盖：

- 保存目录中生成所有预期文件。
- `result.json` 包含来源、地图名、参数和历史曲线。
- 无解结果不会写出 `Infinity` 或 `NaN`。
- 无解路径长度保存为 `null`。
- 连续保存会生成不同目录。

### 16.7 汇总脚本测试

`tests/test_summarize_results.py` 覆盖：

- 从 `result.json` 收集结果。
- 读取 `experiment_label.txt`。
- 汇总成功路径统计。
- 保留主要 ACO 参数字段。
- 写出 `summary.csv`。

### 16.8 可视化测试

`tests/test_visualization.py` 覆盖：

- 历史最优收敛图能生成 figure。
- 本轮最优 / 平均长度图能生成 figure。
- 成功路径数图能生成 figure。

### 16.9 地图目录测试

`tests/test_map_catalog.py` 覆盖：

- 地图元数据与实际 CSV 起终点、尺寸一致。
- 预期可解性和求解器结果一致。
- 标记为分析用的地图有非平直历史最优曲线。
- 未知地图返回 custom 兜底元数据。
- 自定义地图排序靠后。

### 16.10 自定义地图测试

`tests/test_custom_map.py` 覆盖：

- 空地图创建。
- 四种画笔。
- 起点和终点唯一性。
- 保存前就绪判断。
- 地图命名清洗。
- 同名追加后缀。
- 内存网格构造 `GridMap`。
- 拒绝浮点、字符串和越界值。
- 保存后能被加载器读回。
- 拒绝路径组件和不安全文件名。
- 不覆盖已有文件。
- 拖动笔画 alpha 栅格化。
- 起点 / 终点多格笔画收敛为单个代表格。

### 16.11 Web 测试

`tests/test_webapp.py` 覆盖：

- 拖动画布可用且未禁用时使用拖动模式。
- 被禁用时跳过拖动画布。
- 组件不可用时跳过拖动画布。

---

## 17. 主要数据流

### 17.1 CLI 数据流

```text
命令行参数
  -> argparse.Namespace
  -> build_params()
  -> AcoParams

CSV 地图路径
  -> load_grid_map()
  -> GridMap

GridMap + AcoParams
  -> solve_path()
  -> PlanningResult

PlanningResult
  -> 控制台打印
  -> Matplotlib 图形
  -> save_planning_artifacts()
  -> result.json / png / txt
```

### 17.2 Streamlit 示例地图数据流

```text
discover_map_files()
  -> get_sorted_map_files()
  -> selectbox 选择地图
  -> load_grid_map()
  -> GridMap
  -> solve_path()
  -> _render_results()
```

### 17.3 Streamlit 自定义地图数据流

```text
create_empty_grid()
  -> 用户画笔操作
  -> apply_brush() / apply_brush_to_cells()
  -> is_ready_to_save()
  -> build_grid_map_from_array()
  -> solve_path()
  -> _render_results()
```

如果用户保存地图：

```text
编辑器原始网格
  -> resolve_map_filename()
  -> save_custom_map()
  -> data/maps/<name>.csv
  -> 之后可作为示例地图重新选择
```

### 17.4 实验汇总数据流

```text
data/outputs/**/result.json
  -> collect_results()
  -> rows
  -> write_summary()
  -> data/outputs/summary.csv
```

---

## 18. 代码中的关键设计取舍

### 18.1 使用节点信息素

项目把信息素存在格子上，而不是边上。优点是实现简单，和二维矩阵天然匹配；缺点是方向表达不如边信息素细。

### 18.2 GridMap 归一化

起点和终点在加载后不保留在 `grid` 数值中，而是独立保存。这样 `grid` 只关心可通行与障碍，求解器和网格规则更简单。

### 18.3 所有入口共享求解器

CLI 和 Streamlit 都调用同一个 `solve_path()`，不会出现“界面一套算法、命令行一套算法”的问题。

### 18.4 自定义地图逻辑可单测

画笔、命名、保存、笔画栅格化都放在 `custom_map.py`，不依赖 Streamlit。这样核心交互逻辑可以用普通单元测试验证。

### 18.5 输出结果可复现

`result.json` 保存地图来源、参数、路径和历史曲线；`summary.csv` 保留主要参数字段。这样实验结果不仅能展示，还能追溯配置。

### 18.6 非标准 JSON 防护

无解结果会产生 `math.inf`。保存前递归转成 `None`，并使用 `allow_nan=False`，确保输出是标准 JSON。

---

## 19. 如果要继续开发，应从哪里改

### 19.1 增加新的算法策略

优先修改：

- `solver.py`
- `models.AcoParams`
- `config/aco_defaults.json`
- `cli.py`
- `webapp.py`
- `tests/test_params.py`
- `tests/test_solver.py`

如果新增参数，还要同步：

- `output_writer.py` 的 `result.json` 参数区。
- `scripts/summarize_results.py` 的字段。
- 文档中的参数说明。

### 19.2 增加新的地图类型

优先修改：

- `data/maps/`
- `map_catalog.py`
- `tests/test_map_catalog.py`

如果地图用于实验分析，建议设置 `analysis_ready=True` 并补充实验输出。

### 19.3 增强自定义地图编辑器

优先修改：

- `custom_map.py`
- `visualization.py`
- `webapp.py`
- `tests/test_custom_map.py`
- `tests/test_webapp.py`

原则是：能放进 `custom_map.py` 的纯逻辑不要直接写在 Streamlit 页面函数里。

### 19.4 增加新的输出文件

优先修改：

- `visualization.py`：新增绘图函数。
- `output_writer.py`：保存新文件。
- `tests/test_outputs.py`：断言文件存在。
- `docs/03_RUNBOOK.md` 和实验文档：同步输出清单。

### 19.5 增加汇总字段

优先修改：

- `output_writer.py`：确保 `result.json` 有原始数据。
- `scripts/summarize_results.py`：提取字段。
- `tests/test_summarize_results.py`：断言字段。
- 文档和实验结果表：同步说明。

---

## 20. 阅读代码的推荐顺序

如果是第一次从代码角度接手项目，建议按下面顺序读：

1. `src/aco_path_planning/models.py`
2. `src/aco_path_planning/map_loader.py`
3. `src/aco_path_planning/grid.py`
4. `src/aco_path_planning/solver.py`
5. `src/aco_path_planning/visualization.py`
6. `src/aco_path_planning/output_writer.py`
7. `src/aco_path_planning/cli.py`
8. `src/aco_path_planning/webapp.py`
9. `src/aco_path_planning/custom_map.py`
10. `scripts/summarize_results.py`
11. `tests/test_solver.py`
12. `tests/test_outputs.py`
13. `tests/test_custom_map.py`
14. `tests/test_map_catalog.py`

先理解数据结构和算法，再看入口和界面，会比从 Streamlit 页面直接读更容易。

---

## 21. 一句话总结代码架构

本项目的代码架构可以概括为：

```text
CSV / 自定义地图
  -> 统一校验为 GridMap
  -> AcoParams 驱动 solve_path()
  -> PlanningResult 承载路径与过程指标
  -> visualization / output_writer / webapp / summary 跨场景复用结果
```

也就是说，项目最核心的稳定接口是：

- `GridMap`
- `AcoParams`
- `PlanningResult`
- `solve_path()`

只要这几个接口保持清晰，CLI、Streamlit、实验输出和后续扩展都可以围绕它们继续演进。
