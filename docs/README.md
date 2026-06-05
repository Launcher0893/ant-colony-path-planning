# 文档总览

本目录收纳了本项目从参考分析、技术设计、运行手册到实验结果的完整文档。  
如果其他人第一次接手项目，建议按下面顺序阅读。

---

## 1. 快速阅读顺序

1. [01_ACO_PROJECT_PLAN.md](./01_ACO_PROJECT_PLAN.md)
   - 项目目标、系统结构、算法设计、测试范围、当前局限
2. [03_RUNBOOK.md](./03_RUNBOOK.md)
   - 环境配置、命令行运行、Streamlit 运行、测试与常见问题
3. [04_EXPERIMENT_RESULTS.md](./04_EXPERIMENT_RESULTS.md)
   - 真实参数实验结果、图表和结论
4. [00_REF_GA_PATH_PLANNING.md](./00_REF_GA_PATH_PLANNING.md)
   - 老师给的遗传算法参考项目分析，帮助理解“为什么本项目不直接照搬参考实现”
5. [02_EXPERIMENT_LOG.md](./02_EXPERIMENT_LOG.md)
   - 后续扩展实验时可复用的记录模板

---

## 2. 各文档作用

### `00_REF_GA_PATH_PLANNING.md`
- 解释参考项目的目录结构、功能和算法思路
- 说明哪些地方可借鉴，哪些地方不能直接照搬

### `01_ACO_PROJECT_PLAN.md`
- 项目最核心的技术文档
- 说明目录结构、功能需求、地图格式、算法设计、模块划分、测试覆盖和当前状态
- 新会话接手时应优先阅读

### `02_EXPERIMENT_LOG.md`
- 实验记录模板
- 用于后续新增参数实验、地图实验或对照实验时快速记账

### `03_RUNBOOK.md`
- 面向实际运行与使用
- 说明如何在 `PyCharm`、`VS Code`、命令行和 `Streamlit` 中启动项目
- 说明如何运行测试、保存输出、汇总结果

### `04_EXPERIMENT_RESULTS.md`
- 当前项目已经完成的一轮真实参数实验
- 包含实验目标、参数组、结果表、图片引用和结果分析

---

## 3. 当前项目状态概览

从文档层面看，当前项目已经具备：

- 可运行的栅格地图路径规划系统
- 可调参数的蚁群算法实现
- CLI 与 Streamlit 双入口
- 多类地图与地图元数据说明
- Streamlit 自定义地图编辑器（鼠标拖动绘制障碍、起点、终点并保存复用）
- 自动化测试
- 实验结果输出与汇总
- 真实实验文档

当前仍可继续补充的主要内容是：

- 学校格式的课程设计正文报告
- 算法流程图
- 答辩提纲
- 更多对照实验与更细测试

---

## 4. 建议配合阅读的代码文件

如果文档阅读后想继续看代码，建议按这个顺序：

1. [../src/aco_path_planning/solver.py](../src/aco_path_planning/solver.py)
2. [../src/aco_path_planning/webapp.py](../src/aco_path_planning/webapp.py)
3. [../src/aco_path_planning/map_catalog.py](../src/aco_path_planning/map_catalog.py)
4. [../scripts/summarize_results.py](../scripts/summarize_results.py)
5. [../tests/test_map_catalog.py](../tests/test_map_catalog.py)
