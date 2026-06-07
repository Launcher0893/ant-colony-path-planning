# 实验记录模板

本文档用于记录第三阶段及后续阶段的算法实验结果，便于课设汇报、答辩和多会话协作。

---

## 1. 实验基本信息

- 实验日期：
- 实验人：
- 使用环境：
  - Python / Conda 环境：
  - 主要依赖版本：
- 代码版本：
  - commit hash：
  - 分支名：

---

## 2. 实验目标

本次实验要验证什么：

- 例如：比较精英强化开关对路径长度和收敛速度的影响
- 例如：比较局部信息素更新前后在 `maze_small.csv` 上的成功率
- 例如：比较不同地图难度下的运行耗时与成功路径数量

---

## 3. 实验配置

### 3.1 地图

- 地图名称：
- 地图路径：
- 地图尺寸：
- 场景类型：

### 3.2 参数

- `ant_count`：
- `iterations`：
- `alpha`：
- `beta`：
- `evaporation_rate`：
- `local_evaporation_rate`：
- `pheromone_deposit_q`：
- `initial_pheromone`：
- `elite_enabled`：
- `elite_weight`：
- `random_seed`：

### 3.3 运行命令

```bash
python main.py --no-plot --save-output ...
```

---

## 4. 输出结果

- 输出目录：
- 是否找到路径：
- 路径长度：
- 最优轮次：
- 总成功路径数：
- 平均每轮成功数：
- 历史最优曲线最终值：
- 本轮最优曲线最终值：
- 本轮平均曲线最终值：
- 运行耗时：
- 汇总结果目录：

### 4.1 结果文件

- `result.json`
- `path_plot.png`
- `convergence_plot.png`
- `iteration_length_plot.png`
- `success_count_plot.png`
- `path.txt`
- `experiment_label.txt`（如本次实验设置了参数组标签）

说明：无解结果中的非有限路径长度会在 `result.json` 中规范化为标准 JSON 的 `null`，避免写出非标准 `Infinity`。

### 4.2 汇总字段

新版 `scripts/summarize_results.py` 会在 `summary.csv` 中保留以下字段，手工记录实验时也建议按这些字段对齐：

- `experiment_label`
- `surface`
- `map_name`
- `found`
- `path_length`
- `best_iteration`
- `runtime_seconds`
- `total_successful_paths`
- `avg_success_count`
- `best_length_curve_final`
- `iteration_best_curve_final`
- `iteration_mean_curve_final`
- `ant_count`
- `iterations`
- `alpha`
- `beta`
- `evaporation_rate`
- `pheromone_deposit_q`
- `initial_pheromone`
- `local_evaporation_rate`
- `elite_enabled`
- `elite_weight`
- `random_seed`
- `result_dir`

---

## 5. 现象分析

记录实验观察：

- 收敛是否稳定
- 是否容易早熟
- 精英强化是否明显改善最优路径
- 局部信息素更新是否影响探索能力
- 在不同地图上的表现差异

---

## 6. 结论

本次实验结论：

- 

后续建议：

- 
