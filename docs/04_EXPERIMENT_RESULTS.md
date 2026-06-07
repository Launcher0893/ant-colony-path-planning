# 参数实验结果

本文档记录本项目在最终阶段选定的 4 张收敛分析图上的实测结果。  
所有数据均来自真实运行输出，并由 `data/outputs/summary.csv` 汇总。

---

## 1. 实验目标

本轮实验主要验证以下内容：

1. 在少量“收敛分析图”上，`history_best_length` 是否会在后续轮次继续下降，而不是一开始就变成直线。
2. 调整蚂蚁数量、迭代次数和信息素参数后，对路径长度、最优轮次、成功路径数量和运行耗时有什么影响。
3. 第三阶段加入的局部信息素更新、精英强化和多条收敛曲线是否足以支撑最终展示和报告分析。

---

## 2. 实验环境

- 运行环境：`conda` 虚拟环境 `aco_path`
- Python：与 `aco_path` 环境一致
- 核心依赖：
  - `numpy`
  - `matplotlib`
  - `streamlit`
- 运行方式：命令行批量执行并保存输出到 `data/outputs/cli/`

---

## 3. 测试地图

本轮选用 4 张已经验证过“历史最优路径长度不是整条直线”的分析图：

| 地图 | 类型 | 说明 |
|---|---|---|
| `easy_alt.csv` | easy | 基础可达图变体，用于观察简单场景下的后续改进 |
| `medium_alt.csv` | medium | 中等绕障图变体，用于观察中等复杂度下的收敛 |
| `large_sparse.csv` | large_sparse | 大图稀疏障碍图，适合展示明显的后续改进 |
| `large_dense_alt.csv` | large_dense | 大图密集障碍图变体，适合观察复杂场景中的稳定收敛 |

---

## 4. 参数组设计

本轮共使用 4 组参数：

| 组别 | 蚂蚁数量 | 迭代次数 | alpha | beta | 全局 rho | 局部 rho | 精英强化 |
|---|---:|---:|---:|---:|---:|---:|---|
| `baseline` | 12 | 100 | 1.0 | 2.0 | 0.30 | 0.05 | 关闭 |
| `high_ants` | 24 | 100 | 1.0 | 2.0 | 0.30 | 0.05 | 关闭 |
| `high_iterations` | 12 | 160 | 1.0 | 2.0 | 0.30 | 0.05 | 关闭 |
| `strong_pheromone` | 12 | 100 | 1.2 | 2.5 | 0.25 | 0.05 | 开启，`elite_weight=2.0` |

除表中列出的差异外，本轮实验统一使用 `pheromone_deposit_q=100.0`、`initial_pheromone=1.0`、`random_seed=42`。新版 `summary.csv` 同时保留 `experiment_label`、`ant_count`、`iterations`、`pheromone_deposit_q`、`initial_pheromone` 等字段，便于从汇总表追溯完整参数。

---

## 5. 实测结果表

以下结果直接根据 `data/outputs/summary.csv` 回填：

| 地图 | 参数组 | 是否找到路径 | 路径长度 | 最优轮次 | 运行耗时/s | 总成功路径数 | 平均每轮成功数 |
|---|---|---|---:|---:|---:|---:|---:|
| `easy_alt.csv` | `baseline` | 是 | 9.414 | 3 | 0.254 | 1014 | 10.14 |
| `easy_alt.csv` | `high_ants` | 是 | 9.414 | 2 | 0.510 | 1918 | 19.18 |
| `easy_alt.csv` | `high_iterations` | 是 | 9.414 | 2 | 0.241 | 1089 | 10.89 |
| `medium_alt.csv` | `baseline` | 是 | 16.000 | 3 | 0.305 | 885 | 8.85 |
| `medium_alt.csv` | `high_ants` | 是 | 16.000 | 2 | 0.607 | 1744 | 17.44 |
| `medium_alt.csv` | `high_iterations` | 是 | 16.000 | 3 | 0.487 | 1418 | 8.86 |
| `medium_alt.csv` | `strong_pheromone` | 是 | 16.000 | 2 | 0.332 | 1033 | 10.33 |
| `large_sparse.csv` | `baseline` | 是 | 31.414 | 16 | 0.813 | 919 | 9.19 |
| `large_sparse.csv` | `high_ants` | 是 | 31.414 | 4 | 1.683 | 1593 | 15.93 |
| `large_sparse.csv` | `high_iterations` | 是 | 31.414 | 16 | 1.319 | 1533 | 9.58 |
| `large_sparse.csv` | `strong_pheromone` | 是 | 45.414 | 5 | 0.915 | 823 | 8.23 |
| `large_dense_alt.csv` | `baseline` | 是 | 22.000 | 3 | 0.495 | 1003 | 10.03 |
| `large_dense_alt.csv` | `high_ants` | 是 | 22.000 | 2 | 1.026 | 1858 | 18.58 |
| `large_dense_alt.csv` | `high_iterations` | 是 | 22.000 | 3 | 0.905 | 1645 | 10.28 |
| `large_dense_alt.csv` | `strong_pheromone` | 是 | 22.000 | 2 | 0.512 | 1155 | 11.55 |

---

## 6. 图片展示

下面引用本轮真实运行生成的图片。

### 6.1 `easy_alt.csv` 基准组

最终路径图：

![](../data/outputs/cli/20260604_172335_easy_alt/path_plot.png)

历史最优路径长度：

![](../data/outputs/cli/20260604_172335_easy_alt/convergence_plot.png)

本轮最优 / 本轮平均路径长度：

![](../data/outputs/cli/20260604_172335_easy_alt/iteration_length_plot.png)

每轮成功路径数：

![](../data/outputs/cli/20260604_172335_easy_alt/success_count_plot.png)

### 6.2 `medium_alt.csv` 强信息素组

最终路径图：

![](../data/outputs/cli/20260604_172341_medium_alt/path_plot.png)

历史最优路径长度：

![](../data/outputs/cli/20260604_172341_medium_alt/convergence_plot.png)

### 6.3 `large_sparse.csv` 基准组

最终路径图：

![](../data/outputs/cli/20260604_172343_large_sparse/path_plot.png)

历史最优路径长度：

![](../data/outputs/cli/20260604_172343_large_sparse/convergence_plot.png)

### 6.4 `large_dense_alt.csv` 高蚂蚁组

最终路径图：

![](../data/outputs/cli/20260604_172351_large_dense_alt/path_plot.png)

历史最优路径长度：

![](../data/outputs/cli/20260604_172351_large_dense_alt/convergence_plot.png)

---

## 7. 结果分析

### 7.1 关于“历史最优路径长度不是直线”

本轮选取的 4 张分析图都满足以下特征：

- 第一轮不会直接拿到最终全局最优
- 后续轮次至少会再次下降一次

这说明这些图更适合用来展示蚁群算法“先探索、后改进”的收敛过程。

### 7.2 蚂蚁数量的影响

观察 `high_ants` 组可以看到：

- 总成功路径数明显提升
- 平均每轮成功路径数量明显增加
- 在 `easy_alt`、`medium_alt`、`large_dense_alt` 上，最优轮次也更靠前

结论：

- 增大蚂蚁数量可以提高探索覆盖率
- 在当前项目里，更多蚂蚁通常能更快找到较优路径

### 7.3 迭代次数的影响

`high_iterations` 组在复杂地图上主要带来：

- 更充足的后续搜索机会
- 但不一定继续降低最终路径长度

例如：

- `large_sparse.csv` 的最优路径长度没有进一步下降，但总成功路径数提高了

结论：

- 增加迭代次数更有利于稳定性和统计充分性
- 不一定总能带来更短路径

### 7.4 信息素强化参数的影响

`strong_pheromone` 组表现出两类现象：

- 在 `medium_alt` 和 `large_dense_alt` 这类图上，仍能较快得到较优路径
- 在 `large_sparse.csv` 上，最终路径长度反而变差，从 `31.414` 上升到 `45.414`

这说明：

- 更强的信息素引导并不总是更好
- 在大图稀疏场景里，过强的偏向可能导致较早收敛到次优路径

### 7.5 不同类型地图的差异

- `easy_alt`：路径较短，结果最稳定，适合快速演示
- `medium_alt`：既能看到收敛过程，又不至于太慢，适合课堂展示
- `large_sparse`：最适合展示历史最优后续继续下降
- `large_dense_alt`：更能体现蚂蚁数量增加带来的成功路径提升

---

## 8. 结论

本轮实验可以得到以下结论：

1. 不是所有地图都适合展示“历史最优后续下降”，因此最终选择分析图是必要的。
2. 增加蚂蚁数量通常能提高成功路径数量，并让最优解更早出现。
3. 增加迭代次数有助于提升搜索稳定性，但不一定直接缩短最终路径。
4. 更强的信息素引导参数在部分复杂地图上可能导致过早收敛到次优路径。
5. 因此在最终课设展示中，应优先使用：
   - `easy_alt.csv`
   - `medium_alt.csv`
   - `large_sparse.csv`
   - `large_dense_alt.csv`
   作为分析与对比的代表图。

后续如果继续完善，建议优先做：

- 路径坐标合法性的更细粒度测试
- Streamlit 保存逻辑测试
- 更正式的实验对比表和答辩材料整理
