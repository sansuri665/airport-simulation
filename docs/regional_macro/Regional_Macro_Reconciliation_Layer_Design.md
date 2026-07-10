# Regional Macro Reconciliation Layer

## 定位

区域宏观对账层把 14 区 raw regional macro 转成可用于航空需求层的区域经济体量和软校准路径。

```text
Global macro feedback path
  -> 14 raw regional macro paths
  -> normalized regional weights
  -> regional GDP levels / shares / ranks
  -> weighted reconciliation diagnostics
  -> viewer regional size metrics
```

本层不覆盖原始区域输出，而是写入独立目录。

## 运行入口

```powershell
py -3 .\airport\macro_layers\regional_macro_reconciliation_sim.py
```

默认读取：

```text
airport/output/global_macro/global_macro_feedback_seed_sweep.csv
airport/output/regional_macro/*_regional_macro_seed_sweep.csv
```

默认输出：

```text
airport/output/regional_macro_reconciled/regional_macro_reconciled_seed_sweep.csv
airport/output/regional_macro_reconciled/regional_macro_reconciled_seed_sweep.json
airport/output/regional_macro_reconciled/regional_macro_reconciliation_seed_sweep.csv
airport/output/regional_macro_reconciled/regional_macro_reconciliation_seed_sweep.json
airport/output/regional_macro_reconciled/regional_macro_reconciled_viewer_data.js
```

## GDP 体量计算

`REGION_CONFIGS` 里的 `global_weight` 是区域规模权重，但当前 14 区合计不是正好 1。

因此对账层保留原始配置权重，同时计算：

```text
regional_normalized_initial_weight =
  regional_global_weight_config / sum(all regional_global_weight_config)
```

区域 raw GDP 体量：

```text
regional_raw_gdp_trillion_usd =
  initial_global_gdp_trillion_usd
  * regional_normalized_initial_weight
  * regional_gdp_index / 100
```

然后用全球 GDP 锚做年度总量缩放：

```text
gdp_level_scale_factor =
  global_gdp_anchor_trillion_usd
  / sum(regional_raw_gdp_trillion_usd)

regional_reconciled_gdp_trillion_usd =
  regional_raw_gdp_trillion_usd * gdp_level_scale_factor
```

这样每个 seed/year 的 14 区 GDP 体量会严格加总到全球 GDP，但区域相对体量仍由各区增长路径决定。

## 与区域 seed 势能的关系

v0.3 起，区域宏观层会输出 `regional-structural-seed-v0.1` 字段。对账层不会抹平这些字段，而是随区域 GDP 体量一起保留：

```text
regional_seed_momentum_label
regional_seed_effective_growth_bias_pct
regional_seed_aviation_propensity_bias_pct
regional_seed_investment_cycle_bias_pct
regional_seed_openness_bias_pct
regional_seed_demand_multiplier
```

这些字段解释为什么某个 seed 下某个区域长期变强或变弱。对账层只做总量锚定：全球 GDP 总盘仍来自全球宏观，区域 seed 势能改变的是区域之间的相对份额、排名、增长贡献和航空需求倾向。

## 区域体量字段

每个 seed/year/region 输出：

```text
regional_reconciled_gdp_trillion_usd
regional_reconciled_share_of_global_gdp_pct
regional_share_change_from_start_pct
regional_weight_drift_pp
regional_rank_by_gdp
regional_growth_contribution_pp_reconciled
```

这些字段可以直接进入机场需求层：

```text
market_size
income_capacity
route_potential
commercial_spend_base
regional_growth_contribution
```

## 对账诊断字段

每个 seed/year 输出一行 14 区加权诊断：

```text
weighted_regional_growth_reconciled_pct
global_growth_anchor_pct
growth_gap_reconciled_pp

weighted_regional_headline_inflation_reconciled_pct
global_headline_inflation_anchor_pct
headline_inflation_gap_reconciled_pp

weighted_regional_hy_reconciled_bps
global_hy_anchor_bps
hy_gap_reconciled_bps

largest_region_id
largest_region_share_pct
top3_region_ids
top3_share_pct
```

GDP level is reconciled exactly. Inflation, rates, credit, stress, equity and energy are soft-adjusted with bounded common adjustments, so regional character is preserved.

## Viewer 接入

`global_gdp_viewer.html` 读取：

```text
airport/output/regional_macro_reconciled/regional_macro_reconciled_viewer_data.js
```

区域面板现在优先显示：

```text
区域 GDP, trillion USD
全球占比
GDP 排名
增长贡献
对账误差
```

如果对账文件缺失，viewer 会回退到原始区域 GDP index。

## 边界

当前版本是 `weighted_14_region_soft_reconciliation`。

它已经解决：

- 区域 GDP 绝对体量。
- 14 区 GDP 加总到全球总量。
- 区域 GDP 占比、排名和增长贡献。
- 主要宏观变量的加权诊断。

它还没有解决：

- 按区域敏感度分配不同变量的非对称调整。
- viewer 内 baseline / occurred 两条区域分岔曲线的并行切换。
- `tail_years` 内年度衰减和路径依赖的进一步校准。
- 航空需求层的客流、航线和商业收入转化。

区域分岔传导字段已经由 `regional-branch-transmission-v0.1` 写入区域输出并被本对账层保留。baseline 中的 `watch` 状态表示潜在相对传导；`macro_run_orchestrator_sim.py` 写入 `occurred` / `counterfactual` 状态时，区域层会把额外冲击施加进主变量，并由本对账层保留到 reconciled 输出。
