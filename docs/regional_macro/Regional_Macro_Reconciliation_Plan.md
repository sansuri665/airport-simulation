# Regional Macro Reconciliation Plan

## 为什么需要对账

14 个区域各自生成宏观路径后，直接加总很容易和全球宏观主路径不一致。

例如：

```text
全球 GDP 增长 = +2.4%
14 区加权 GDP 增长 = +3.3%
```

这会让游戏世界观不一致。区域宏观层后面需要一个软校准步骤：

```text
Global macro path
  -> raw regional macro
  -> weighted aggregate
  -> compare with global anchor
  -> soft adjustment
  -> reconciled regional macro
```

## 对账原则

对账不是把所有区域强行拉成全球平均。

目标是：

- 加权总量接近全球宏观。
- 保留区域差异。
- 大区域吸收更多总量误差，小区域吸收更少。
- 高敏感区域对相应变量调整更多。
- 不能把油价、美元、利率等全球变量误当成本地完全独立变量。

## 需要对账的变量

第一优先级：

```text
regional_gdp_growth_pct
regional_headline_inflation_pct
regional_core_inflation_pct
regional_policy_rate_pct
regional_10y_yield_pct
regional_hy_spread_bps
regional_equity_return_pct
regional_macro_stress_index
```

第二优先级：

```text
regional_currency_index
regional_liquidity_index
regional_financial_conditions_index
regional_energy_cost_pressure_index
regional_income_index
consumer_confidence_index
```

## 软对账公式

可以用统一框架：

```text
regional_value_final =
  regional_value_raw
  + global_gap
    * region_global_weight
    * reconciliation_sensitivity
    * variable_absorption_factor
```

其中：

```text
global_gap =
  global_anchor_value
  - weighted_average(regional_value_raw)
```

示例：

- 中国大陆、北美、欧洲权重大，吸收更多 GDP 总量误差。
- 中东对油价/能源压力吸收更高。
- 东南亚、南亚、拉美对美元和信用压力更敏感。
- 西欧/北欧、北美对利率和股债资产更敏感。

## 对账轮次

v0.1 建议做 2 轮：

```text
Pass 1: raw regional macro
Pass 2: reconciliation adjustment
Pass 3: diagnostic check
```

如果误差仍然较大，可以做第 3 次调整，但不要无限迭代。

## 当前实现

14 区静态路径和 v0.1 对账层已经先落地。

区域生成脚本仍保留：

```text
regional_reconciliation_scope = single_region_soft_anchor
```

独立对账脚本使用：

```text
regional_macro_reconciliation_sim.py
reconciliation_scope = weighted_14_region_soft_reconciliation
```

含义是：

- 每个区域变量先按区域敏感度生成 raw value。
- 区域 GDP 体量用归一化初始权重和区域 GDP index 得到。
- 区域 GDP 体量按年度全球 GDP 锚缩放，14 区加总严格等于全球 GDP。
- 通胀、利率、信用、压力、资产和能源做有上限的软校准。
- 输出区域 GDP 占比、排名和增长贡献。

输出目录：

```text
airport/output/regional_macro_reconciled/
```

## 诊断字段

建议输出：

```text
regional_reconciled_gdp_trillion_usd
regional_reconciled_share_of_global_gdp_pct
regional_rank_by_gdp
regional_growth_contribution_pp_reconciled

growth_gap_reconciled_pp
headline_inflation_gap_reconciled_pp
policy_rate_gap_reconciled_pp
hy_gap_reconciled_bps
macro_stress_gap_reconciled_index
```

也可以给每个区域输出：

```text
growth_reconciliation_adjustment_pct
inflation_reconciliation_adjustment_pct
rate_reconciliation_adjustment_pct
credit_reconciliation_adjustment_bps
equity_reconciliation_adjustment_pct
```

## 哪些不能硬对账

不要机械对账这些：

- `regional_currency_index`：区域货币本来就应该分化。
- `regional_energy_cost_pressure_index`：油价全球一致，但区域贸易条件不同。
- `regional_policy_uncertainty_index`：本地政治和政策差异应保留。
- `regional_geopolitical_risk_index`：不应被全球平均抹平。
- `regional_macro_regime`：由对账后变量重新分类，不直接平均。

## 与航空需求层的关系

航空需求层应读取对账后的区域宏观，而不是 raw 区域宏观。

推荐链条：

```text
Global macro
  -> Regional macro raw
  -> Regional macro reconciled
  -> Regional aviation demand
  -> Airport passenger allocation
```

这样后续机场客运的全球加总也更容易和区域/全球背景保持一致。
