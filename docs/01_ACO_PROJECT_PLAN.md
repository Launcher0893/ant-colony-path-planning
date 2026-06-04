# 基于蚁群算法的栅格路径规划系统

## 1. 文档目的

本文档不是摘要，而是项目的长期技术交接文档。目标有两个：

1. 约束当前实现，避免多次会话开发时架构漂移。
2. 让新的会话在只阅读本文件和仓库目录的前提下，快速理解项目状态、设计选择、已完成内容、未完成内容和下一步开发方式。

本项目的主题是：**从给定的栅格地图文件中读取起点、终点和障碍物信息，利用蚁群算法规划从起点到终点的可行路径，并提供可视化交互界面**。

---

## 2. 当前项目文件结构

项目必须遵循以下目录结构，后续新增内容也应优先放在对应位置：

```text
ant-colony-path-planning/
├── config/                  # 参数配置、默认值、后续可扩展的环境配置
│   └── aco_defaults.json
├── data/                    # 地图、样例数据、后续实验输出数据
│   ├── maps/
│   │   ├── easy.csv
│   │   ├── medium.csv
│   │   └── blocked.csv
│   └── outputs/
│       ├── cli/
│       └── streamlit/
├── docs/                    # 技术文档、参考分析、开发计划、实验记录
│   ├── 00_REF_GA_PATH_PLANNING.md
│   └── 01_ACO_PROJECT_PLAN.md
├── references/              # 老师给的参考项目，保留原样，不作为主实现目录
├── scripts/                 # 可直接运行的脚本入口
│   ├── run_cli.py
│   ├── run_streamlit.py
│   └── generate_maps.py
├── src/                     # 主源码目录
│   └── aco_path_planning/
│       ├── __init__.py
│       ├── cli.py
│       ├── config.py
│       ├── grid.py
│       ├── map_loader.py
│       ├── models.py
│       ├── solver.py
│       ├── visualization.py
│       └── webapp.py
├── tests/                   # 单元测试与集成测试
├── main.py                  # 兼容 PyCharm / VS Code 直接运行的 CLI 根入口
├── streamlit_app.py         # 兼容 Streamlit 直接运行的根入口
├── README.md
└── requirements.txt
```

### 2.1 各目录职责约束

- `config/`
  - 放项目默认参数、后续可调策略、实验预设。
  - 不放代码逻辑。
- `data/`
  - 放地图文件、实验输入输出、后续生成的结果样本。
  - 当前 `data/maps/` 是栅格地图根目录。
- `docs/`
  - 放结构说明、算法设计、技术决策、后续实验记录。
  - `01` 文档是后续会话最重要的接手入口。
- `references/`
  - 只读参考资料区。
  - 不在里面修改主项目实现。
- `scripts/`
  - 放用户可直接执行的脚本包装层。
  - 用于解决 `src` 布局下的导入问题。
- `src/`
  - 唯一主业务代码目录。
  - 所有算法、解析、可视化逻辑都必须在这里维护。

---

## 3. 课设目标与需求映射

### 3.1 老师要求拆解

原始目标：

- 从给定的栅格地图文件中读取起点、终点和障碍物信息。
- 利用蚁群算法规划从起点到终点的可行路径。

原始要求：

1. 理解栅格地图表示方法。
2. 理解蚁群算法基本流程，包括蚂蚁路径搜索、信息素选择概率、信息素挥发和信息素更新。
3. 搭建环境并跑通算法，安装 PyCharm，配置 Python 环境；导入 NumPy、Matplotlib、Streamlit 等必要库，运行程序得到路径规划结果。
4. 完成可视化界面功能，支持选择地图、设置蚂蚁数量、迭代次数、信息素参数，并显示最终路径和路径坐标。

### 3.2 当前实现对应关系

已完成：

- 已支持从 `CSV` 栅格地图读取起点、终点、障碍物。
- 已实现基于蚁群算法的 8 邻域路径搜索。
- 已支持 CLI 运行和 Streamlit 界面运行。
- 已支持地图选择、蚂蚁数量、迭代次数、`alpha / beta / rho / Q / 初始信息素 / 随机种子` 参数设置。
- 已显示最终路径、路径长度、最优轮次、路径坐标、运行耗时、收敛曲线。
- 已支持显式保存运行结果到 `data/outputs/`。
- 已提供分级手工地图集和地图生成脚本。
- 已支持局部信息素更新与精英强化。
- 已支持成功路径数量统计与结果汇总。
- 已提供 PyCharm / VS Code 可直接运行的根入口。

未完全完成或后续可加强：

- 参数说明、实验结果记录、截图留档还不完整。
- 尚未提供老师可能需要的“实验报告式”章节文档。
- 尚未增加批量实验脚本与结果导出功能。
- 尚未做更强的结果复现实验和性能比较。

---

## 4. 为什么参考项目不能直接照搬

老师给的参考项目位于 `references/genetic-algorithm-path-planning/`，它是一个**遗传算法路径规划示例**，只能作为工程组织和展示思路参考，不能作为算法实现参考。

### 4.1 可以参考的部分

- 主流程拆分为“数据准备 -> 求解 -> 可视化 -> 结果展示”。
- 将配置、算法逻辑和绘图逻辑解耦。
- 使用 `matplotlib` 展示路径结果。
- 用独立文档解释项目。

### 4.2 不能参考甚至必须避免的部分

- 算法不对：
  - 参考项目使用遗传算法，不是蚁群算法。
  - 它的核心是种群、适应度、轮盘赌、交叉、变异，本项目不应复用这些逻辑。
- 地图建模不对：
  - 参考项目是固定节点图，不是栅格地图。
  - 它依赖硬编码点和连边，不满足“读取地图文件”的要求。
- 避障方式不对：
  - 参考项目通过合法连边隐式绕障。
  - 本项目必须直接在栅格上判断障碍和邻域可行性。
- 参数结构不对：
  - 遗传算法参数与蚁群算法参数没有直接对应关系。

结论：

- `references/` 只保留供论文写作、思路对比、结构借鉴。
- `src/` 中不应再出现遗传算法术语和实现模式。

---

## 5. 地图文件格式设计

### 5.1 当前格式

项目当前统一使用 `CSV` 栅格格式，每个单元格用一个整数表示：

- `0`：空地，可通行
- `1`：障碍物，不可通行
- `2`：起点
- `3`：终点

示例：

```csv
2,0,0,0
1,1,0,1
0,0,0,0
1,0,1,3
```

### 5.2 解析约束

当前 `src/aco_path_planning/map_loader.py` 中的加载器执行以下校验：

- 文件必须存在。
- 文件不能是空文件。
- 地图必须是规则矩形。
- 单元格值只能是 `0/1/2/3`。
- 起点 `2` 必须且只能出现一次。
- 终点 `3` 必须且只能出现一次。

### 5.3 加载后的内部表示

加载后转换为 `GridMap`：

- `grid: np.ndarray`
  - 内部只保留“是否障碍”语义。
  - 起点和终点在 `grid` 中都会被归一化成可通行格 `0`。
- `start: tuple[int, int]`
- `goal: tuple[int, int]`
- `source: Path | None`

坐标统一采用：

- `(row, col)`，即 `(行, 列)`。
- 这是整个项目的主坐标体系。

后续文档、输出、测试、界面都不应切换成 `(x, y)` 作为主表示。

---

## 6. 蚁群算法设计说明

### 6.1 采用的算法形态

本项目当前采用的是**基于节点信息素的栅格蚁群算法**，而不是基于边信息素的图搜索蚁群算法。

这样选择的原因：

- 课设目标是跑通、展示和讲清原理，不是做最复杂版本。
- 栅格地图直接给每个可通行格维护信息素，数据结构更直观。
- 更适合和 `numpy`、`matplotlib`、`streamlit` 配合实现。
- 便于在文档里解释“信息素场”的概念。

### 6.2 移动规则

当前固定使用 `8 邻域`：

- 上、下、左、右
- 左上、右上、左下、右下

代价规则：

- 正交移动代价：`1.0`
- 对角移动代价：`sqrt(2)`

### 6.3 防穿角规则

对角移动不是只要目标格为空就允许，还必须满足：

- 若从 `(r, c)` 对角走到 `(r+1, c+1)`，
- 则 `(r+1, c)` 和 `(r, c+1)` 也必须都可通行。

这条规则用于避免蚂蚁“穿过障碍物角点”，否则对角移动会出现视觉上穿墙的问题。

### 6.4 单只蚂蚁的搜索过程

每轮迭代中，每只蚂蚁从起点出发，执行以下流程：

1. 初始化当前位置为起点。
2. 将起点加入访问集合。
3. 枚举当前位置所有可行邻居：
   - 在边界内
   - 非障碍物
   - 满足防穿角规则
   - 本轮尚未访问
4. 若没有可选邻居，本只蚂蚁失败。
5. 若当前位置已经是终点，本只蚂蚁成功。
6. 根据状态转移概率从可选邻居中抽样出下一个位置。
7. 重复，直到：
   - 到达终点，或
   - 没有可行邻居，或
   - 步数达到上限

步数上限当前设为：

- `rows * cols`

作用：

- 防止异常地图或随机游走导致单只蚂蚁运行过久。

### 6.5 状态转移概率

对于当前位置的某个候选邻居 `j`，权重计算为：

```text
weight(j) = tau(j)^alpha * eta(j)^beta
```

其中：

- `tau(j)`：邻居格子的当前信息素强度
- `eta(j)`：启发函数
- `alpha`：信息素影响因子
- `beta`：启发函数影响因子

当前启发函数定义为：

```text
eta(j) = 1 / (distance_to_goal(j) + 1e-6)
```

其中 `distance_to_goal` 采用 8 邻域下的一致距离估计：

- 尽可能走对角
- 剩余部分走直线

这比单纯欧氏距离更贴近本网格代价模型。

### 6.6 信息素挥发与更新

每轮迭代结束后：

1. 所有可通行节点先进行挥发：

```text
tau = tau * (1 - rho)
```

2. 对所有成功蚂蚁的路径进行沉积：

```text
deposit = Q / path_length
```

3. 成功路径上的每个节点都增加该沉积量。

特点：

- 路径越短，沉积越大。
- 路径越好，后续更容易被采样。
- 若某轮没有成功蚂蚁，则只挥发不沉积。

### 6.7 最优解维护

当前实现采用全局最优记录：

- 如果某只蚂蚁本轮路径长度优于全局最优，则更新最优路径。
- 即使后续多轮没有更好结果，也保留历史最优。

输出记录包括：

- `found`
- `path`
- `path_length`
- `best_iteration`
- `history_best_length`
- `history_success_count`
- `total_successful_paths`
- `runtime_seconds`
- `message`

### 6.8 第三阶段算法增强

当前已实现两项增强：

1. **局部信息素更新**
   - 每只蚂蚁完成一次搜索后，对其走过的路径执行局部更新
   - 更新形式为：

```text
tau = (1 - local_rho) * tau + local_rho * tau0
```

其中：

- `local_rho` 为局部挥发率
- `tau0` 为初始信息素

2. **精英强化（Elite Reinforcement）**
   - 每轮全局挥发和普通沉积结束后，如果当前已有全局最优路径，则对该路径追加一次精英沉积
   - 强化量与 `elite_weight` 成正比

作用：

- 提高历史最优路径的稳定强化能力
- 在复杂地图上改善收敛表现
- 通过开关控制，方便做对照实验

---

## 7. 当前源码模块设计

### 7.1 `src/aco_path_planning/models.py`

定义核心数据模型：

- `GridMap`
- `AcoParams`
- `PlanningResult`

这是整个项目最基础的接口层，后续若新增结果导出、实验统计或更多 UI，也应继续围绕这三个模型扩展。

### 7.2 `src/aco_path_planning/config.py`

定义项目关键路径：

- `PROJECT_ROOT`
- `DEFAULT_MAP_DIR`
- `DEFAULT_GENERATED_MAP_DIR`
- `DEFAULT_PARAM_FILE`
- `DEFAULT_OUTPUT_ROOT`
- `DEFAULT_CLI_OUTPUT_DIR`
- `DEFAULT_STREAMLIT_OUTPUT_DIR`

作用：

- 避免不同入口自己拼路径。
- 统一 `config/` 和 `data/` 的真实位置。

### 7.3 `src/aco_path_planning/map_loader.py`

负责：

- 地图发现
- CSV 解析
- 格式校验
- `GridMap` 构建

这是从“外部文件”进入“内部模型”的唯一入口。

### 7.4 `src/aco_path_planning/grid.py`

负责纯网格层工具函数：

- 判断是否越界
- 判断是否可通行
- 邻居生成
- 路径长度计算
- 启发距离计算
- 防穿角逻辑

该模块不关心 ACO，只关心“栅格运动规则”。

### 7.5 `src/aco_path_planning/solver.py`

负责蚁群算法主循环：

- 初始化信息素
- 多只蚂蚁搜索
- 成功路径收集
- 信息素挥发
- 信息素沉积
- 局部信息素更新
- 精英强化
- 最优解维护
- 运行耗时统计
- 成功路径总数统计

这是后续算法增强的主战场。

### 7.6 `src/aco_path_planning/visualization.py`

负责：

- 栅格地图绘制
- 障碍物显示
- 起终点显示
- 最优路径绘制
- 收敛曲线绘制
- 路径坐标格式化

### 7.6.1 `src/aco_path_planning/output_writer.py`

负责实验输出持久化：

- 保存路径图
- 保存收敛曲线图
- 保存路径文本
- 保存结构化 `result.json`

### 7.7 `src/aco_path_planning/cli.py`

负责命令行模式：

- 读取参数文件
- 合并命令行覆盖参数
- 调用求解器
- 打印结果
- 打印运行耗时
- 打印成功路径总数
- 显式触发输出保存
- 控制是否弹出图形窗口

### 7.8 `src/aco_path_planning/webapp.py`

负责 Streamlit 页面：

- 地图选择
- 参数输入
- 结果展示
- 显示运行耗时
- 显示成功路径总数
- 可选保存本次结果
- 路径图和收敛曲线展示

### 7.9 `scripts/summarize_results.py`

负责对 `data/outputs/` 下的实验结果做汇总：

- 扫描所有 `result.json`
- 生成 `summary.csv`
- 汇总关键指标，便于实验对比和报告整理

### 7.9 `scripts/`

存在原因：

- 项目采用 `src` 布局。
- 为了保证 `PyCharm`、`VS Code`、命令行直接运行方便，需要脚本层把 `src` 插入 `sys.path`。

当前脚本：

- `scripts/run_cli.py`
- `scripts/run_streamlit.py`
- `scripts/generate_maps.py`

### 7.10 根入口兼容层

当前保留：

- `main.py`
- `streamlit_app.py`

作用：

- 满足老师或 IDE 直接运行根文件的习惯。
- 避免强制用户先理解 `scripts/`。

---

## 8. 配置系统设计

### 8.1 当前默认参数文件

位置：

- `config/aco_defaults.json`

默认内容：

- `ant_count = 50`
- `iterations = 100`
- `alpha = 1.0`
- `beta = 4.0`
- `evaporation_rate = 0.3`
- `pheromone_deposit_q = 100.0`
- `initial_pheromone = 1.0`
- `local_evaporation_rate = 0.05`
- `elite_enabled = true`
- `elite_weight = 2.0`
- `random_seed = 42`

### 8.2 参数优先级

CLI 当前采用以下优先级：

1. 代码默认值
2. `config/aco_defaults.json`
3. 命令行参数覆盖

这样做的意义：

- 便于统一维护课设默认值。
- 便于实验时用命令行临时覆盖。

### 8.3 后续可扩展方向

后续如果需要，可把 `config/` 扩展为：

- `aco_defaults.json`
- `experiment_fast.json`
- `experiment_stable.json`
- `report_demo.json`

并在 CLI / Streamlit 中提供预设选择。

---

## 9. 运行方式设计

### 9.1 命令行运行

推荐：

```bash
python main.py
```

或：

```bash
python scripts/run_cli.py
```

带参数运行示例：

```bash
python main.py --map data/maps/medium.csv --ants 60 --iterations 120 --alpha 1.0 --beta 4.0 --rho 0.3 --q 100
```

保存输出示例：

```bash
python main.py --no-plot --save-output --output-dir data/outputs/cli --map data/maps/medium.csv
```

### 9.2 Streamlit 运行

推荐：

```bash
streamlit run streamlit_app.py
```

或：

```bash
streamlit run scripts/run_streamlit.py
```

### 9.3 PyCharm / VS Code 兼容性设计

为了满足“PyCharm 和 VS Code 都能启动”的要求，当前设计是：

- 根目录保留 `main.py`
- 根目录保留 `streamlit_app.py`
- 内部真实逻辑放在 `src/`
- `scripts/` 负责路径注入

这样无论用户：

- 直接点运行 `main.py`
- 在终端运行 `python main.py`
- 用 `streamlit run streamlit_app.py`

都不需要额外设置 `PYTHONPATH`。

---

## 10. 测试设计与当前覆盖

### 10.1 当前测试文件

- `tests/test_map_loader.py`
- `tests/test_grid.py`
- `tests/test_solver.py`
- `tests/test_params.py`
- `tests/test_cli.py`
- `tests/test_outputs.py`
- `tests/test_generate_maps.py`
- `tests/test_summarize_results.py`

### 10.2 已覆盖内容

`test_map_loader.py`

- 正常地图读取
- 多起点报错
- 非矩形地图报错
- 非法值报错
- 缺起点报错
- 缺终点报错
- 多终点报错

`test_grid.py`

- 禁止对角穿角
- 对角路径长度计算

`test_solver.py`

- `easy.csv` 上能找到路径
- `blocked.csv` 上能正确返回无解
- `medium.csv` 上能稳定找到路径
- `no_solution_large.csv` 上能正确返回无解

`test_params.py`

- 参数非法值校验

`test_cli.py`

- JSON 参数文件读取与命令行覆盖

`test_outputs.py`

- 结果输出目录与产物文件生成

`test_generate_maps.py`

- 地图生成脚本输出合法矩形地图
- 保证只生成一个起点和一个终点

`test_summarize_results.py`

- 汇总脚本能从 `result.json` 生成 `summary.csv`

### 10.3 当前测试不足

还缺少：

- 路径坐标合法性更细粒度检查
- Streamlit 保存逻辑的更细粒度测试
- 第三阶段参数组合的更系统化实验测试

这些都适合后续继续补。

---

## 11. 已完成开发清单

截至当前会话，以下内容已实现：

1. 完成主项目从参考遗传算法思路向蚁群算法思路的切换。
2. 完成基于 `CSV` 栅格地图的解析与校验。
3. 完成 8 邻域网格移动与防穿角逻辑。
4. 完成基于节点信息素的 ACO 求解器。
5. 完成 Matplotlib 路径图与收敛曲线绘制。
6. 完成 Streamlit 页面基础交互。
7. 完成 `config/data/docs/references/scripts/src` 结构对齐。
8. 完成默认参数文件。
9. 完成样例地图文件。
10. 完成基础单元测试与无解场景验证。
11. 完成分级手工地图集。
12. 完成地图生成脚本。
13. 完成 CLI / Streamlit 结果导出能力。
14. 完成运行耗时统计。
15. 完成局部信息素更新。
16. 完成精英强化。
17. 完成结果汇总脚本。
18. 完成实验记录模板。

---

## 12. 当前实现的局限与风险

### 12.1 算法层局限

- 当前采用“禁止回访”策略，单只蚂蚁不会重复访问节点。
  - 优点：简单，避免死循环。
  - 风险：某些复杂地图下可能过早走入死路。

- 当前信息素存储在节点上，而不是边上。
  - 优点：实现简单。
  - 风险：对方向性表达不如边信息素细腻。

- 当前没有自适应参数。

### 12.2 工程层局限

- 未做日志系统。
- 未做批量实验脚本。
- 未做更正式的配置 schema 校验。

### 12.3 课设交付层局限

- 还没有“实验报告”版本文档。
- 还没有整理算法流程图。
- 还没有固定一组用于答辩演示的参数模板。

---

## 13. 后续开发优先级建议

后续如果继续做，建议严格按下面顺序推进。

### 第一优先级：巩固当前实现

1. 增加路径坐标合法性的更细测试。
2. 增加 Streamlit 保存逻辑的更细测试。
3. 补充 README 中的 PyCharm / VS Code 操作截图或说明。
4. 用 `summary.csv` 建立更正式的实验对比表。

### 第二优先级：增强课设展示效果

1. 在 Streamlit 中显示参数说明。
2. 增加地图文件上传功能。
3. 增加每轮最优值表格展示。
4. 增加“运行耗时”显示。
5. 增加“是否成功到达终点的蚂蚁数量”统计。

### 第三优先级：增强算法质量

1. 增加边信息素版本作为对照实验。
2. 增加路径平滑处理。
3. 比较不同参数下的收敛速度与路径长度。
4. 增加成功路径比例分析。
5. 尝试自适应参数。

### 第四优先级：课设材料补完

1. 新建实验记录文档，例如 `docs/02_EXPERIMENT_LOG.md`
2. 新建运行说明文档，例如 `docs/03_RUNBOOK.md`
3. 新建答辩提纲文档，例如 `docs/04_DEFENSE_NOTES.md`
4. 整理结果截图和参数对比表

---

## 14. 新会话接手指南

如果后续是新会话接手，建议按以下顺序理解项目：

1. 先看本文件 `docs/01_ACO_PROJECT_PLAN.md`
   - 明确目标、结构、设计边界、当前状态
2. 再看 `README.md`
   - 明确如何运行
3. 再看 `src/aco_path_planning/solver.py`
   - 理解当前算法核心
4. 再看 `src/aco_path_planning/webapp.py`
   - 理解可视化界面逻辑
5. 再看 `tests/`
   - 明确当前验证覆盖面

如果要继续开发，不要再把主代码写回根目录；继续扩展时应遵守：

- 业务逻辑进 `src/`
- 可运行包装进 `scripts/`
- 数据进 `data/`
- 配置进 `config/`
- 文档进 `docs/`

---

## 15. 本项目的当前“完成定义”

对当前阶段来说，可认为项目达到“阶段性可交付”的标准是：

- 可以从 `CSV` 栅格地图读取地图数据。
- 可以运行 ACO 找到可行路径或正确返回无解。
- 可以显示路径图、路径长度、路径坐标和收敛曲线。
- 可以在 PyCharm 和 VS Code 中直接启动 CLI。
- 可以通过 Streamlit 启动界面进行交互。
- 项目结构符合 `config/data/docs/references/scripts/src` 约束。
- 文档足够让后续多会话继续开发而不丢上下文。

当前会话的重构目标就是达到这个状态。
