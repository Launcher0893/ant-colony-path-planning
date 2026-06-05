# 运行手册

本文档面向项目使用者和后续开发者，说明如何在本地安装环境、运行项目、执行测试，以及在 `PyCharm` 和 `VS Code` 中使用当前项目。

---

## 1. 适用范围

本手册适用于当前仓库中的蚁群算法栅格路径规划系统，适用场景包括：

- 首次在本机部署项目
- 运行命令行版路径规划
- 运行 Streamlit 可视化界面
- 执行自动化测试
- 在 `PyCharm` 和 `VS Code` 中启动项目

---

## 2. 项目结构速览

运行相关的关键目录和文件如下：

```text
ant-colony-path-planning/
├── config/
│   └── aco_defaults.json      # 默认 ACO 参数配置
├── data/
│   ├── maps/                  # 示例与分级地图
│   └── outputs/               # 运行结果输出目录
├── docs/
│   ├── 01_ACO_PROJECT_PLAN.md # 技术交接文档
│   └── 03_RUNBOOK.md          # 当前运行手册
├── scripts/
│   ├── run_cli.py             # CLI 启动脚本
│   ├── run_streamlit.py       # Streamlit 启动脚本
│   └── generate_maps.py       # 地图生成脚本
├── src/
│   └── aco_path_planning/     # 主业务代码
├── tests/                     # 自动化测试
├── main.py                    # 根目录 CLI 入口
├── streamlit_app.py           # 根目录 Streamlit 入口
├── requirements.txt           # 依赖列表
└── README.md
```

---

## 3. 环境要求

### 3.1 Python 版本

建议使用：

- `Python 3.10` 或更高版本

理论上 `Python 3.9+` 也可以运行，但当前未单独做版本兼容性验证。

### 3.2 依赖库

当前项目依赖：

- `numpy>=1.23`
- `matplotlib>=3.7`
- `streamlit>=1.30`
- `streamlit-image-coordinates>=0.1.6`（自定义地图点击版回退所需）
- `pillow>=9.0`（自定义地图画布渲染所需）
- `streamlit-drawable-canvas==0.9.3`（自定义地图拖动上色所需）

依赖定义见 [requirements.txt](/abs/path/D:/Program Files/Code/VS Code/Python/ant-colony-path-planning/requirements.txt)。

说明：`streamlit-drawable-canvas` 已停更，且依赖 Streamlit 内部函数 `image_to_url`。
在 Streamlit 1.50 上，`webapp.py` 启动时会打一个兼容补丁修正该函数的位置与签名变化；
若补丁或组件不可用，自定义地图会自动回退到逐格点击版，界面不会崩溃。

---

## 4. 安装步骤

### 4.1 进入项目目录

```bash
cd "D:\Program Files\Code\VS Code\Python\ant-colony-path-planning"
```

如果你已经在项目目录中，可跳过这一步。

### 4.2 创建虚拟环境

推荐使用虚拟环境，避免污染全局 Python。

Windows PowerShell：

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Windows CMD：

```cmd
python -m venv .venv
.\.venv\Scripts\activate.bat
```

### 4.3 安装依赖

```bash
pip install -r requirements.txt
```

### 4.4 验证依赖安装

可以执行：

```bash
python -c "import numpy, matplotlib, streamlit; print('deps ok')"
```

如果输出 `deps ok`，说明核心依赖已安装成功。

如需验证自定义地图相关组件，可再执行：

```bash
python -c "import PIL, streamlit_image_coordinates, streamlit_drawable_canvas; print('canvas deps ok')"
```

---

## 5. 地图文件说明

地图文件位于 [data/maps](/abs/path/D:/Program Files/Code/VS Code/Python/ant-colony-path-planning/data/maps)。

当前示例地图：

- [easy.csv](/abs/path/D:/Program Files/Code/VS Code/Python/ant-colony-path-planning/data/maps/easy.csv)
- [easy_alt.csv](/abs/path/D:/Program Files/Code/VS Code/Python/ant-colony-path-planning/data/maps/easy_alt.csv)
- [medium.csv](/abs/path/D:/Program Files/Code/VS Code/Python/ant-colony-path-planning/data/maps/medium.csv)
- [medium_alt.csv](/abs/path/D:/Program Files/Code/VS Code/Python/ant-colony-path-planning/data/maps/medium_alt.csv)
- [blocked.csv](/abs/path/D:/Program Files/Code/VS Code/Python/ant-colony-path-planning/data/maps/blocked.csv)
- [blocked_alt.csv](/abs/path/D:/Program Files/Code/VS Code/Python/ant-colony-path-planning/data/maps/blocked_alt.csv)
- [hard_corridor.csv](/abs/path/D:/Program Files/Code/VS Code/Python/ant-colony-path-planning/data/maps/hard_corridor.csv)
- [hard_corridor_alt.csv](/abs/path/D:/Program Files/Code/VS Code/Python/ant-colony-path-planning/data/maps/hard_corridor_alt.csv)
- [maze_small.csv](/abs/path/D:/Program Files/Code/VS Code/Python/ant-colony-path-planning/data/maps/maze_small.csv)
- [maze_small_alt.csv](/abs/path/D:/Program Files/Code/VS Code/Python/ant-colony-path-planning/data/maps/maze_small_alt.csv)
- [dense_obstacles.csv](/abs/path/D:/Program Files/Code/VS Code/Python/ant-colony-path-planning/data/maps/dense_obstacles.csv)
- [dense_obstacles_alt.csv](/abs/path/D:/Program Files/Code/VS Code/Python/ant-colony-path-planning/data/maps/dense_obstacles_alt.csv)
- [large_sparse.csv](/abs/path/D:/Program Files/Code/VS Code/Python/ant-colony-path-planning/data/maps/large_sparse.csv)
- [large_sparse_alt.csv](/abs/path/D:/Program Files/Code/VS Code/Python/ant-colony-path-planning/data/maps/large_sparse_alt.csv)
- [large_dense.csv](/abs/path/D:/Program Files/Code/VS Code/Python/ant-colony-path-planning/data/maps/large_dense.csv)
- [large_dense_alt.csv](/abs/path/D:/Program Files/Code/VS Code/Python/ant-colony-path-planning/data/maps/large_dense_alt.csv)
- [no_solution_large.csv](/abs/path/D:/Program Files/Code/VS Code/Python/ant-colony-path-planning/data/maps/no_solution_large.csv)
- [no_solution_large_alt.csv](/abs/path/D:/Program Files/Code/VS Code/Python/ant-colony-path-planning/data/maps/no_solution_large_alt.csv)

地图格式是 `CSV` 数字栅格：

- `0`：可通行空地
- `1`：障碍物
- `2`：起点
- `3`：终点

示例：

```csv
2,0,0,0
1,1,0,1
0,0,0,0
1,0,1,3
```

注意：

- 地图必须是规则矩形
- 起点必须只有一个
- 终点必须只有一个

---

## 6. 默认参数说明

默认参数文件位于 [config/aco_defaults.json](/abs/path/D:/Program Files/Code/VS Code/Python/ant-colony-path-planning/config/aco_defaults.json)。

当前默认值：

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

输出目录约定：

- CLI 默认输出到 `data/outputs/cli/`
- Streamlit 默认输出到 `data/outputs/streamlit/`

CLI 启动时参数优先级为：

1. 代码内默认值
2. `config/aco_defaults.json`
3. 命令行参数覆盖

---

## 7. 命令行运行

### 7.1 最简单启动方式

直接运行根入口：

```bash
python main.py
```

这会：

- 默认读取 `data/maps/easy.csv`
- 默认读取 `config/aco_defaults.json`
- 在控制台输出路径结果
- 弹出 `matplotlib` 窗口显示地图路径图和收敛曲线

### 7.2 使用脚本入口启动

也可以运行：

```bash
python scripts/run_cli.py
```

与 `python main.py` 效果一致。

### 7.3 不弹图，仅看控制台输出

```bash
python main.py --no-plot
```

适用于：

- 仅测试算法输出
- 在无图形环境中运行
- 避免频繁弹出窗口

### 7.4 指定地图

```bash
python main.py --map data/maps/medium.csv
```

### 7.5 指定完整参数

```bash
python main.py --map data/maps/medium.csv --ants 60 --iterations 120 --alpha 1.0 --beta 4.0 --rho 0.3 --q 100 --initial-pheromone 1.0 --seed 42
```

### 7.6 CLI 参数列表

当前支持的参数：

- `--map`：地图文件路径
- `--params`：参数配置文件路径
- `--ants`：蚂蚁数量
- `--iterations`：迭代次数
- `--alpha`：信息素影响因子
- `--beta`：启发函数影响因子
- `--rho`：信息素挥发率
- `--q`：信息素沉积常数
- `--initial-pheromone`：初始信息素强度
- `--local-rho`：局部信息素挥发率
- `--elite-weight`：精英强化权重
- `--disable-elite`：关闭精英强化
- `--seed`：随机种子
- `--save-output`：显式保存本次运行结果
- `--output-dir`：保存目录根路径
- `--no-plot`：禁用绘图窗口

### 7.7 保存输出

如果需要把本次运行结果保存到 `data/outputs/`，使用：

```bash
python main.py --no-plot --save-output --output-dir data/outputs/cli --map data/maps/medium.csv
```

一次保存会生成一个独立目录，目录下包含：

- `result.json`
- `path_plot.png`
- `convergence_plot.png`
- `path.txt`

额外统计字段会保存在 `result.json` 中，包括：

- `runtime_seconds`
- `total_successful_paths`
- `history_success_count`
- `local_evaporation_rate`
- `elite_enabled`
- `elite_weight`

### 7.8 CLI 正常输出示例

正常运行后，控制台通常会输出：

```text
Map: ...\data\maps\easy.csv
Start: (0, 0)
Goal: (5, 5)
Found path: yes
Message: Path found successfully.
Best iteration: 1
Path length: 10.000
Path coordinates: (0, 0) -> ...
```

---

## 8. Streamlit 界面运行

### 8.1 推荐启动方式

```bash
streamlit run streamlit_app.py
```

### 8.2 备用启动方式

```bash
streamlit run scripts/run_streamlit.py
```

### 8.3 界面功能

当前界面支持：

- 选择地图来源（示例地图 / 自定义地图）
- 选择地图
- 在自定义地图来源下绘制地图（设置尺寸、拖动上色、保存为 CSV）
- 设置蚂蚁数量
- 设置迭代次数
- 设置 `alpha`
- 设置 `beta`
- 设置 `rho`
- 设置 `Q`
- 设置初始信息素
- 设置局部信息素挥发率
- 设置精英强化开关
- 设置精英强化权重
- 设置随机种子
- 设置是否保存本次结果
- 为关键算法参数显示中文释义与 `help` 提示
- 展示地图预览
- 展示最终路径图
- 展示收敛曲线
- 展示路径坐标
- 展示运行耗时
- 展示成功路径总数

### 8.4 使用流程

1. 启动 Streamlit
2. 打开浏览器中的本地页面
3. 在左侧边栏选择地图与参数
4. 点击“开始规划”
5. 查看路径结果、路径长度和收敛曲线

补充说明：

- 右侧 `Map Preview` 已采用更紧凑的显示尺寸，避免预览图过度占用版面
- 地图集中的起点和终点位置已做分布拉开，不再集中在左上和右下
- 当前地图信息区会显示地图类别和简要特点说明
- 收敛分析已区分为历史最优、本轮最优/本轮平均、每轮成功路径数三类图

### 8.5 自定义地图编辑器使用流程

在左侧边栏“地图来源”选择“自定义地图”后，主区域会显示地图编辑器。操作流程如下：

1. 设置地图行数和列数（范围 2 到 40），点击“创建 / 重置画布”。
2. 新画布默认在左上角放起点、右下角放终点。
3. 在“选择画笔”中选择障碍、起点、终点或擦除。
4. 在画布上**按住鼠标拖动绘制**：松开鼠标后，笔画经过的格子会按当前画笔着色。
   - 障碍、擦除画笔对划过的每个格子生效。
   - 起点、终点画笔即使划过多个格子，也只落一个代表格，保持全图唯一。
5. 界面会实时显示起点数量和终点数量；只有恰好一个起点和一个终点时才能保存或规划。
6. 在“保存地图”处可选填地图名称：
   - 填写名称则保存为 `<名称>.csv`。
   - 留空则按 `custom_<时间戳>_<序号>.csv` 自动命名。
   - 保存到 `data/maps/` 后，可在“示例地图”来源中重新选择复用。
7. 绘制完成后，点击侧边栏“开始规划”，即可在自定义地图上运行蚁群算法并查看结果。

说明：

- 拖动绘制依赖 `streamlit-drawable-canvas` 组件。
- 该组件较旧，本项目在 `webapp.py` 启动时打了一个兼容补丁以适配新版 Streamlit 的 `image_to_url` 接口。
- 若组件不可用，编辑器会自动回退到“逐格点击”绘制模式，功能不丢，只是手感退化为点一次画一格。

---

## 9. 自动化测试

### 9.1 运行全部测试

```bash
python -m unittest discover -s tests
```

### 9.2 当前测试覆盖

测试目录：[tests](/abs/path/D:/Program Files/Code/VS Code/Python/ant-colony-path-planning/tests)

当前测试文件：

- [test_map_loader.py](/abs/path/D:/Program Files/Code/VS Code/Python/ant-colony-path-planning/tests/test_map_loader.py)
- [test_grid.py](/abs/path/D:/Program Files/Code/VS Code/Python/ant-colony-path-planning/tests/test_grid.py)
- [test_solver.py](/abs/path/D:/Program Files/Code/VS Code/Python/ant-colony-path-planning/tests/test_solver.py)
- [test_params.py](/abs/path/D:/Program Files/Code/VS Code/Python/ant-colony-path-planning/tests/test_params.py)
- [test_cli.py](/abs/path/D:/Program Files/Code/VS Code/Python/ant-colony-path-planning/tests/test_cli.py)
- [test_outputs.py](/abs/path/D:/Program Files/Code/VS Code/Python/ant-colony-path-planning/tests/test_outputs.py)
- [test_generate_maps.py](/abs/path/D:/Program Files/Code/VS Code/Python/ant-colony-path-planning/tests/test_generate_maps.py)
- [test_map_catalog.py](/abs/path/D:/Program Files/Code/VS Code/Python/ant-colony-path-planning/tests/test_map_catalog.py)
- [test_summarize_results.py](/abs/path/D:/Program Files/Code/VS Code/Python/ant-colony-path-planning/tests/test_summarize_results.py)
- [test_visualization.py](/abs/path/D:/Program Files/Code/VS Code/Python/ant-colony-path-planning/tests/test_visualization.py)
- [test_custom_map.py](/abs/path/D:/Program Files/Code/VS Code/Python/ant-colony-path-planning/tests/test_custom_map.py)

覆盖内容包括：

- 地图读取
- 地图合法性校验
- 8 邻域与防穿角
- 可解地图求解
- 无解地图处理
- 参数校验
- CLI 参数文件加载
- 输出保存逻辑
- 地图生成脚本
- 地图目录与元数据一致性
- 结果汇总脚本
- 收敛图绘制函数
- 自定义地图画笔、笔画栅格化、命名与保存
- 自定义地图保存后能被加载器正确读回
- 地图目录元数据的兜底逻辑

### 9.3 运行单个测试文件

```bash
python -m unittest tests.test_solver
```

或：

```bash
python -m unittest tests.test_map_loader
```

---

## 10. PyCharm 使用方式

### 10.1 打开项目

在 `PyCharm` 中打开整个项目根目录：

```text
ant-colony-path-planning
```

### 10.2 配置解释器

建议使用：

- 项目虚拟环境 `.venv`

### 10.3 运行命令行版

可直接右键运行：

- [main.py](/abs/path/D:/Program Files/Code/VS Code/Python/ant-colony-path-planning/main.py)

### 10.4 运行测试

可直接右键运行：

- `tests/` 目录
- 单个测试文件
- 单个测试类或测试方法

### 10.5 运行 Streamlit

在 `PyCharm` 终端执行：

```bash
streamlit run streamlit_app.py
```

---

## 11. VS Code 使用方式

### 11.1 打开项目

用 `VS Code` 打开项目根目录。

### 11.2 选择 Python 解释器

建议选择：

- `.venv` 对应的 Python 解释器

### 11.3 运行命令行版

可直接运行：

- [main.py](/abs/path/D:/Program Files/Code/VS Code/Python/ant-colony-path-planning/main.py)

或在终端执行：

```bash
python main.py
```

### 11.4 运行测试

在终端执行：

```bash
python -m unittest discover -s tests
```

### 11.5 运行 Streamlit

在终端执行：

```bash
streamlit run streamlit_app.py
```

---

## 12. 常见问题排查

### 12.1 `ModuleNotFoundError`

现象：

- 启动时提示找不到 `aco_path_planning`

原因：

- 没有从根入口 `main.py` / `streamlit_app.py`
- 或没有通过 `scripts/run_cli.py` / `scripts/run_streamlit.py` 启动

正确做法：

- 使用 `python main.py`
- 或 `python scripts/run_cli.py`
- 或 `streamlit run streamlit_app.py`

不要直接执行 `src/aco_path_planning/cli.py`。

### 12.2 地图读取失败

常见原因：

- 地图路径写错
- CSV 中有非法值
- 地图不是规则矩形
- 没有起点或终点
- 起点或终点出现多次

建议先用 `data/maps/easy.csv` 验证环境是否正常。

### 12.3 Streamlit 命令不可用

现象：

- 提示 `streamlit` 不是内部或外部命令

处理方式：

```bash
python -m streamlit run streamlit_app.py
```

如果仍失败，先重新安装依赖：

```bash
pip install -r requirements.txt
```

### 12.4 Matplotlib 不弹窗

可能原因：

- 当前环境无图形界面
- 使用了 `--no-plot`
- IDE 图形后端设置异常

可先用：

```bash
python main.py --no-plot
```

确认算法本身是否正常。

### 12.5 测试无法发现

优先使用：

```bash
python -m unittest discover -s tests
```

不要直接从 `src/` 内部切目录后再执行测试。

### 12.6 当前解释器缺少依赖

如果你使用的是 `conda` 环境 `aco_path`，建议统一通过这个环境运行：

```bash
conda run -n aco_path python -m unittest discover -s tests
conda run -n aco_path python main.py --no-plot
```

如果直接 `python` 找不到 `numpy`，通常是当前终端没有切到正确解释器。

### 12.7 自定义地图无法拖动绘制

现象：

- 进入“自定义地图”后，编辑器退回到“逐格点击”模式，或提示缺少绘图组件。

原因：

- 缺少 `streamlit-drawable-canvas` 组件，或该组件与当前 Streamlit 版本不兼容。

处理方式：

```bash
pip install -r requirements.txt
```

补充说明：

- 拖动绘制依赖 `streamlit-drawable-canvas`，该组件较旧，`webapp.py` 启动时会打一个兼容补丁，适配新版 Streamlit 中 `image_to_url` 的模块位置与参数签名变化。
- 若补丁或组件仍不可用，编辑器会自动回退到逐格点击模式，功能不丢，只是手感退化。

---

## 13. 推荐日常操作流程

如果是日常开发，建议固定按下面顺序：

1. 激活虚拟环境
2. 执行 `python -m unittest discover -s tests`
3. 执行 `python main.py --no-plot`
4. 需要界面时执行 `streamlit run streamlit_app.py`
5. 修改代码后重复测试
6. 需要留档时使用 `--save-output`

---

## 14. 地图生成脚本

当前提供地图生成脚本：

- [scripts/generate_maps.py](/abs/path/D:/Program Files/Code/VS Code/Python/ant-colony-path-planning/scripts/generate_maps.py)

支持模式：

- `maze`
- `dense`
- `large_sparse`

示例：

```bash
python scripts/generate_maps.py --mode dense --rows 12 --cols 12 --density 0.25 --seed 42 --name generated_dense_demo
```

生成结果默认放在：

- `data/maps/generated/`

---

## 15. 结果汇总脚本

当前提供结果汇总脚本：

- [scripts/summarize_results.py](/abs/path/D:/Program Files/Code/VS Code/Python/ant-colony-path-planning/scripts/summarize_results.py)

功能：

- 扫描 `data/outputs/` 下所有 `result.json`
- 生成 `summary.csv`
- 汇总关键指标，便于后续做实验对比和报告整理

示例：

```bash
python scripts/summarize_results.py --input-dir data/outputs --output-file data/outputs/summary.csv
```

---

## 16. 相关文档

- [文档总览](/abs/path/D:/Program Files/Code/VS Code/Python/ant-colony-path-planning/docs/README.md)
- [实验记录模板](/abs/path/D:/Program Files/Code/VS Code/Python/ant-colony-path-planning/docs/02_EXPERIMENT_LOG.md)
- [项目技术计划与交接文档](/abs/path/D:/Program Files/Code/VS Code/Python/ant-colony-path-planning/docs/01_ACO_PROJECT_PLAN.md)
- [参考项目分析文档](/abs/path/D:/Program Files/Code/VS Code/Python/ant-colony-path-planning/docs/00_REF_GA_PATH_PLANNING.md)
- [运行手册](/abs/path/D:/Program Files/Code/VS Code/Python/ant-colony-path-planning/docs/03_RUNBOOK.md)
- [实验结果文档](/abs/path/D:/Program Files/Code/VS Code/Python/ant-colony-path-planning/docs/04_EXPERIMENT_RESULTS.md)
