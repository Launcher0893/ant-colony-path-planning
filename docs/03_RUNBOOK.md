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

依赖定义见 [requirements.txt](/abs/path/D:/Program Files/Code/VS Code/Python/ant-colony-path-planning/requirements.txt)。

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

- 选择地图
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

- [实验记录模板](/abs/path/D:/Program Files/Code/VS Code/Python/ant-colony-path-planning/docs/02_EXPERIMENT_LOG.md)
- [项目技术计划与交接文档](/abs/path/D:/Program Files/Code/VS Code/Python/ant-colony-path-planning/docs/01_ACO_PROJECT_PLAN.md)
- [参考项目分析文档](/abs/path/D:/Program Files/Code/VS Code/Python/ant-colony-path-planning/docs/00_REF_GA_PATH_PLANNING.md)
- [运行手册](/abs/path/D:/Program Files/Code/VS Code/Python/ant-colony-path-planning/docs/03_RUNBOOK.md)
