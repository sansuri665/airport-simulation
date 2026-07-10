# Regional Branch Transmission Plan

## 当前结论

区域宏观暂时不单独抽事件。

当前实现状态：

```text
regional_macro_layer_sim.py v0.2
regional_macro_reconciliation_sim.py v0.2
```

已接入 `regional-branch-transmission-v0.1`：

- 区域层读取全球 `branch_risk_primary_*` 字段。
- 区域层输出 `branch_scenario_*` 和 `regional_branch_*` 传导字段。
- `watch` 状态只显示潜在区域相对传导，不主动改写当前主路径。
- `occurred` / `counterfactual` 状态会把区域额外冲击施加到 GDP、通胀、政策、信用、汇率、流动性、资产、信心和压力变量。
- 对账层会把这些字段带入 `regional_macro_reconciled_seed_sweep.*`。

更合适的结构是：

```text
Global branch risk
  -> global occurred / avoided path
  -> regional macro transmission
  -> regional reconciliation
  -> regional aviation demand
```

也就是说，全球宏观进入历史分岔口后，区域宏观应随全球路径变化而变化。区域层主要负责表达：

```text
同一个全球分岔，对不同区域的影响程度不同。
```

例如能源危机对西欧/北欧、日韩、南亚/印度的压力更强；美元挤兑对南亚、拉美、撒哈拉以南非洲更强；风险资产牛市对北美财富效应更强。

## 为什么不先做区域独立事件

区域独立事件会让系统过早变复杂。

当前游戏还在搭建宏观底座，全球层已经有分岔风险和情景路径。如果区域层再独立抽事件，容易出现：

- 全球是软着陆，但某几个区域随机进入危机，世界观难解释。
- 同一类事件在全球层和区域层重复计算。
- 区域静态路径已经补齐后，显式分岔传导更适合统一接入，避免单一区域参数先行固化。
- 区域航空需求还没开始，区域事件的商业含义暂时难校准。

所以当前原则是：

```text
全球负责历史分岔。
区域负责传导差异。
```

## 两种传导模式

### 1. 被动传导

如果全球分岔已经改变了全球路径，例如：

```text
global_growth down
global_hy_spread up
global_oil_price up
global_dollar_index up
global_equity_return down
```

区域宏观会自然改变，因为区域脚本已经读取全球 GDP、通胀、利率、美元、信用、股债和油价。

这是当前北美层已经具备的能力。

### 2. 显式区域暴露

被动传导只能表达“全球数值改变后，区域跟着变”。它不能充分表达：

```text
同样的油价冲击，欧洲更痛，北美中等，中东可能部分受益。
同样的美元挤兑，新兴市场更痛，北美本币压力较小。
同样的风险资产牛市，北美财富效应更强。
```

所以当前已经在区域层加了一层 `branch_transmission`。

它不是重新抽事件，而是在全球分岔已发生时，按区域暴露系数追加局部冲击。

```text
regional_branch_impulse =
  global_branch_impulse
  * (regional_branch_exposure - global_average_exposure)
  * variable_loading
  * phase_decay
```

这样做的含义是：全球路径已经承担了“世界平均冲击”，区域传导只负责表达该区域相对全球平均更痛或更受益的部分。

## 发生路径和未发生路径

界面或模拟中可以保留两条路径：

```text
current / baseline path
occurred path
```

其中：

- `current` 或 `baseline`：当前主路径，也就是风险未发生或尚未发生。
- `occurred`：全球分岔发生后的反事实路径。
- `avoided`：风险被政策或外部条件化解后的路径，可选。

区域宏观不需要决定事件是否发生。它只读取：

```text
branch_scenario_id
branch_scenario_state
global_path_variant
```

然后生成对应的区域路径。

默认 baseline 输出仍处于 `watch` 状态，因为它表示风险未发生或尚未发生。

`macro_run_orchestrator_sim.py` 已经可以持久化 `occurred` / `counterfactual` 路径：它会在全球路径中写入 `scenario_risk_id`、`scenario_state`、`scenario_trigger_year` 和 `scenario_phase`，再驱动 14 区区域宏观进入显式传导。

## 影响期和余波

全球分岔不应该在影响期结束后完全瞬间消失。

建议分成：

```text
impact_years
tail_years
```

含义：

- `impact_years`：事件主冲击期，变量变化明显。
- `tail_years`：余波期，冲击按衰减系数逐步消退。

区域层可以额外保留疤痕变量：

```text
regional_branch_tail_scarring_index
```

它用于表达信用疤痕、收入修复慢、投资意愿下降、风险偏好恢复不完全等长期痕迹。

## 当前字段

区域宏观和区域对账输出当前包含：

```text
regional_branch_transmission_version
branch_scenario_id
branch_scenario_label
branch_scenario_state
branch_source_year
branch_impact_years
branch_tail_years
branch_year_in_effect
branch_effect_phase

regional_branch_transmission_active
regional_branch_exposure_index
regional_branch_relative_exposure_index
regional_branch_strength_index
regional_branch_growth_impulse_pct
regional_branch_inflation_impulse_pct
regional_branch_policy_impulse_pct
regional_branch_credit_impulse_bps
regional_branch_fx_pressure_impulse
regional_branch_energy_impulse
regional_branch_liquidity_impulse
regional_branch_asset_impulse_pct
regional_branch_confidence_impulse
regional_branch_tail_scarring_index
```

`branch_effect_phase` 建议取值：

```text
none
watch
impact
tail
expired
```

`branch_scenario_state` 建议取值：

```text
baseline
occurred
avoided
counterfactual
```

## 初始分岔类型

第一批可以先覆盖这些全球分岔：

| branch_id | 中文含义 | 区域传导重点 |
|---|---|---|
| `false_dawn` | 虚假黎明 | 信用疤痕、复苏反复、资产回撤 |
| `policy_mistake_tightening` | 政策失误：过早收紧 | 利率、信用、资产估值和消费信心 |
| `policy_behind_curve` | 政策失误：落后曲线 | 通胀预期、政策追赶、滞胀压力 |
| `credit_accident` | 信用事故 | HY 利差、银行压力、再融资和投资拖累 |
| `bank_lending_trap` | 银行惜贷循环 | 流动性传导失效、贷款意愿和信用可得性 |
| `dollar_squeeze_escalation` | 美元挤兑升级 | 汇率压力、外债压力、EM 流动性 |
| `energy_shock_escalation` | 能源冲击升级 | 能源成本、通胀、贸易条件 |
| `bond_market_accident` | 债券市场失控 | 长端利率、金融条件、股债同跌 |
| `soft_landing_success` | 软着陆成功 | 通胀降温、信用稳定、增长不破位 |
| `liquidity_bubble` | 流动性牛市脱实向虚 | 股市、估值、财富效应和后续脆弱性 |
| `refinancing_wall` | 再融资墙 | 企业到期压力、信用拖累、投资修复慢 |
| `demand_destruction_disinflation` | 需求破坏式降通胀 | 需求转弱、低通胀、信用和收入压力 |
| `stagflation_trap` | 滞胀陷阱 | 高通胀叠加低增长，政策两难 |
| `risk_asset_bull_fragility` | 风险资产牛市脆弱化 | 资产回调、风险偏好、信用基础不稳 |

## 暴露矩阵占位

下面不是最终参数，只是 v0.1 暴露方向。

数值含义：

```text
0.50 = 低暴露
1.00 = 中性暴露
1.50 = 高暴露
```

| region_id | energy_crisis | dollar_squeeze | credit_crunch | policy_mistake | risk_asset_bull | stagflation | commodity_supercycle |
|---|---:|---:|---:|---:|---:|---:|---:|
| `china_mainland` | 1.05 | 0.85 | 0.95 | 1.10 | 0.80 | 1.00 | 0.95 |
| `hk_macao_taiwan` | 1.10 | 0.95 | 1.05 | 1.00 | 1.10 | 1.00 | 0.85 |
| `japan_korea` | 1.35 | 0.95 | 0.95 | 0.90 | 0.95 | 1.15 | 0.70 |
| `southeast_asia` | 1.10 | 1.20 | 1.05 | 1.00 | 1.05 | 1.05 | 0.95 |
| `south_asia_india` | 1.30 | 1.35 | 1.10 | 1.00 | 0.85 | 1.20 | 0.80 |
| `middle_east_gulf` | 0.65 | 0.75 | 0.90 | 0.80 | 1.00 | 0.85 | 1.45 |
| `central_asia_turkey_eurasia` | 1.05 | 1.30 | 1.15 | 1.10 | 0.75 | 1.20 | 1.15 |
| `west_north_europe` | 1.45 | 0.90 | 1.00 | 0.95 | 0.95 | 1.25 | 0.70 |
| `south_east_europe_mediterranean` | 1.35 | 1.05 | 1.10 | 1.00 | 0.85 | 1.25 | 0.75 |
| `north_america` | 0.70 | 0.55 | 1.10 | 1.15 | 1.25 | 0.95 | 0.95 |
| `latin_america_caribbean` | 0.95 | 1.35 | 1.20 | 1.10 | 0.90 | 1.15 | 1.15 |
| `oceania` | 0.90 | 0.85 | 0.90 | 0.90 | 1.00 | 0.90 | 1.25 |
| `north_africa` | 1.20 | 1.25 | 1.15 | 1.05 | 0.75 | 1.20 | 0.90 |
| `sub_saharan_africa` | 1.15 | 1.45 | 1.30 | 1.10 | 0.70 | 1.25 | 1.05 |

## 变量传导方向

每个分岔类型可以映射到几个核心变量。

| branch_id | growth | inflation | credit | fx | energy | liquidity | asset |
|---|---:|---:|---:|---:|---:|---:|---:|
| `false_dawn` | - | mixed | + | + | - | - | - |
| `policy_mistake_tightening` | - | - | + | + | - | - | - |
| `policy_behind_curve` | - | + | + | + | + | - | - |
| `credit_accident` | - | - | + | + | - | - | - |
| `bank_lending_trap` | - | - | + | + | - | mixed | - |
| `dollar_squeeze_escalation` | - | mixed | + | + | mixed | - | - |
| `energy_shock_escalation` | - | + | + | + | + | - | - |
| `bond_market_accident` | - | mixed | + | + | mixed | - | - |
| `soft_landing_success` | + | - | - | 0 | 0 | + | + |
| `liquidity_bubble` | + then - | + | - then + | - then + | mixed | + then - | + then - |
| `refinancing_wall` | - | - | + | + | - | - | - |
| `demand_destruction_disinflation` | - | - | + | + | - | mixed | - |
| `stagflation_trap` | - | + | + | + | + | - | - |
| `risk_asset_bull_fragility` | - | mixed | + | + | mixed | - | - |

符号含义：

- `+`：该压力或变量上行。
- `-`：该压力或变量下行。
- `mixed`：按区域资源属性、进口依赖或政策口径决定。
- `0`：不建议显式冲击，交给全球数值和普通区域公式传导。

## 接入顺序

已完成：

1. 保留本文档和字段命名。
2. 确认区域对账器口径。
3. 实现 `branch_transmission` 参数表。
4. 在区域宏观生成时读取全球 `branch_scenario_state`。
5. 对 `occurred` 路径追加区域暴露冲击。
6. 输出 `tail_years` 和 `regional_branch_tail_scarring_index` 字段。
7. 重新跑区域对账和 `regional_macro_regime` 分类。
8. 接入 viewer，让区域总览显示全球分岔传导块。

后续未完成：

- 在 viewer 内加入 run browser，不需要手动 `--publish-viewer` 才能切换历史 run。
- 在区域 viewer 里同时展示 baseline / occurred 两条区域曲线。
- 继续校准 `impact_years` / `tail_years` 的衰减参数和区域疤痕强度。

## 与区域对账的关系

区域分岔传导应发生在对账之前：

```text
global branch path
  -> raw regional macro
  -> regional branch transmission
  -> regional reconciliation
  -> regional regime classification
```

这样做的原因是，分岔造成的区域差异应该进入加权总量校准，而不是在对账之后又把总量打乱。

对账不能把分岔差异完全抹平。当前对账器会保留 `regional_branch_*` 字段；GDP level 仍精确对齐全球总量，非 GDP 指标维持软对账。未来对账器还可以进一步识别：

```text
branch_sensitive_field = true
```

对于能源压力、汇率压力、信用压力、风险偏好等字段，只做弱对账或不对账。

## 防止重复计算

如果全球发生路径已经把油价从 80 推到 130，区域公式会自动感受到更高油价。

区域 `branch_transmission` 不应再次完整施加同样的油价冲击。它只负责区域相对全球平均的额外差异：

```text
regional_extra_impact =
  global_branch_impact
  * (regional_exposure - global_average_exposure)
```

这样可以避免：

```text
global oil shock
  + regional oil shock
  = double counted oil shock
```

## 当前北美备注

北美当前已经能被动响应全球路径。

当前显式传导中，北美建议优先体现：

- `credit_crunch`：HY、信用可得性、消费信心。
- `policy_mistake`：利率敏感、股债估值、地产和消费压力。
- `risk_asset_bull`：股市、财富效应、风险偏好。
- `dollar_squeeze`：本币压力较低，但全球流动性和信用仍会受影响。
- `energy_crisis`：能源成本中等上行，但贸易条件不应像纯进口区域那样恶化。
