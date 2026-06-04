# ant-colony-path-planning

基于蚁群算法的栅格路径规划系统。项目从 `CSV` 栅格地图文件读取起点、终点和障碍物，使用蚁群算法搜索可行路径，并提供命令行与 Streamlit 两种运行方式。

## 目录结构
- `config/`：默认参数配置
- `data/maps/`：示例与分级栅格地图
- `data/maps/generated/`：脚本生成的实验地图
- `data/outputs/`：CLI 与 Streamlit 运行结果输出
- `docs/`：参考分析和项目计划文档
- `references/`：老师提供的参考项目
- `scripts/`：CLI、Streamlit 与地图生成脚本
- `src/`：主源码目录
- `tests/`：自动化测试

## 功能概览
- 读取 `CSV` 栅格地图
- 支持 `8` 邻域路径规划，禁止对角穿角
- 支持配置蚂蚁数量、迭代次数、`alpha`、`beta`、`rho`、`Q` 和初始信息素
- 支持显式保存路径图、收敛曲线、路径坐标和结构化结果
- 提供手工地图集和地图生成脚本
- 显示最终路径、路径长度、路径坐标、运行耗时和收敛曲线
- 同时支持 `PyCharm`、`VS Code`、命令行和 `Streamlit` 运行

## 地图格式
地图文件存放在 `data/maps/` 目录下，使用 `CSV` 数字栅格格式：

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

## 环境安装
```bash
pip install -r requirements.txt
```

## 运行方式
命令行方式：

```bash
python main.py
```

或：

```bash
python scripts/run_cli.py
```

指定参数运行：

```bash
python main.py --map data/maps/medium.csv --ants 60 --iterations 120 --alpha 1.0 --beta 4.0 --rho 0.3 --q 100
```

保存输出示例：

```bash
python main.py --no-plot --save-output --output-dir data/outputs/cli --map data/maps/medium.csv
```

Streamlit 界面：

```bash
streamlit run streamlit_app.py
```

或：

```bash
streamlit run scripts/run_streamlit.py
```

## 参数配置
默认参数文件在 `config/aco_defaults.json`，CLI 启动时会先读取该文件，再应用命令行参数覆盖。

## 示例地图
- `data/maps/easy.csv`：基础可达地图
- `data/maps/medium.csv`：中等复杂度绕障地图
- `data/maps/blocked.csv`：无解地图
- `data/maps/hard_corridor.csv`：狭窄通道地图
- `data/maps/maze_small.csv`：小型迷宫地图
- `data/maps/dense_obstacles.csv`：高障碍密度地图
- `data/maps/large_sparse.csv`：大尺寸稀疏障碍地图
- `data/maps/large_dense.csv`：大尺寸密集障碍地图
- `data/maps/no_solution_large.csv`：大尺寸无解地图

## 地图生成
生成额外实验地图：

```bash
python scripts/generate_maps.py --mode dense --rows 12 --cols 12 --density 0.25 --seed 42 --name generated_dense_demo
```

## 测试
```bash
python -m unittest discover -s tests
```

## 项目文档
- [参考项目分析](./docs/00_REF_GA_PATH_PLANNING.md)
- [项目技术计划与交接文档](./docs/01_ACO_PROJECT_PLAN.md)
- [运行手册](./docs/03_RUNBOOK.md)

## 参考说明
`references/` 目录中的参考项目是基于遗传算法的固定节点图路径规划示例。本项目没有复用其算法代码，只参考了工程拆分和结果展示思路。
