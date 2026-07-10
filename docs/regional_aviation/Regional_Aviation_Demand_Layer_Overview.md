# Regional Aviation Demand Layer Overview

## 当前定位

区域航空需求层位于区域宏观层之后、机场层之前。

它不直接模拟具体机场、航线、航司运力或机场商业收入，而是把 14 个区域的宏观路径翻译成：

```text
这个区域今年航空需求强不强？
是哪类出行需求强？
旅客对价格有多敏感？
旅客的高端消费和免税消费倾向如何？
```

推荐链条：

```text
Global macro
  -> Regional macro
  -> Regional reconciliation
  -> Regional aviation demand
  -> Regional air capacity / supply fulfillment
  -> Airport passenger allocation
  -> Airport commercial business
```

## 当前实现状态

v0.2 已实现 14 个区域：

```text
north_america
china_mainland
west_north_europe
japan_korea
southeast_asia
south_asia_india
hk_macao_taiwan
middle_east_gulf
oceania
south_east_europe_mediterranean
central_asia_turkey_eurasia
north_africa
latin_america_caribbean
sub_saharan_africa
```

脚本入口：

```text
airport/macro_layers/regional_aviation_demand_layer_sim.py
```

单独运行：

```powershell
py -3 .\airport\macro_layers\regional_aviation_demand_layer_sim.py --region north_america
py -3 .\airport\macro_layers\regional_aviation_demand_layer_sim.py --region china_mainland
py -3 .\airport\macro_layers\regional_aviation_demand_layer_sim.py --region west_north_europe
py -3 .\airport\macro_layers\regional_aviation_demand_layer_sim.py --region japan_korea
py -3 .\airport\macro_layers\regional_aviation_demand_layer_sim.py --region southeast_asia
py -3 .\airport\macro_layers\regional_aviation_demand_layer_sim.py --region south_asia_india
py -3 .\airport\macro_layers\regional_aviation_demand_layer_sim.py --region hk_macao_taiwan
py -3 .\airport\macro_layers\regional_aviation_demand_layer_sim.py --region middle_east_gulf
py -3 .\airport\macro_layers\regional_aviation_demand_layer_sim.py --region oceania
py -3 .\airport\macro_layers\regional_aviation_demand_layer_sim.py --region south_east_europe_mediterranean
py -3 .\airport\macro_layers\regional_aviation_demand_layer_sim.py --region central_asia_turkey_eurasia
py -3 .\airport\macro_layers\regional_aviation_demand_layer_sim.py --region north_africa
py -3 .\airport\macro_layers\regional_aviation_demand_layer_sim.py --region latin_america_caribbean
py -3 .\airport\macro_layers\regional_aviation_demand_layer_sim.py --region sub_saharan_africa
```

当前输出：

```text
airport/output/regional_aviation_demand/north_america_aviation_demand_seed_sweep.csv
airport/output/regional_aviation_demand/north_america_aviation_demand_summary.json
airport/output/regional_aviation_demand/north_america_aviation_demand_viewer_data.js
airport/output/regional_aviation_demand/<region>_aviation_demand_seed_sweep.csv
airport/output/regional_aviation_demand/<region>_aviation_demand_summary.json
airport/output/regional_aviation_demand/<region>_aviation_demand_viewer_data.js
```

一键 orchestrator 已经接入已配置的航空需求区域。归档 run 内部会写到：

```text
airport/output/macro_runs/<run_id>/<variant>/regional_aviation_demand/north_america/
airport/output/macro_runs/<run_id>/<variant>/regional_aviation_demand/china_mainland/
airport/output/macro_runs/<run_id>/<variant>/regional_aviation_demand/west_north_europe/
airport/output/macro_runs/<run_id>/<variant>/regional_aviation_demand/japan_korea/
airport/output/macro_runs/<run_id>/<variant>/regional_aviation_demand/southeast_asia/
airport/output/macro_runs/<run_id>/<variant>/regional_aviation_demand/south_asia_india/
airport/output/macro_runs/<run_id>/<variant>/regional_aviation_demand/hk_macao_taiwan/
airport/output/macro_runs/<run_id>/<variant>/regional_aviation_demand/middle_east_gulf/
airport/output/macro_runs/<run_id>/<variant>/regional_aviation_demand/oceania/
airport/output/macro_runs/<run_id>/<variant>/regional_aviation_demand/south_east_europe_mediterranean/
airport/output/macro_runs/<run_id>/<variant>/regional_aviation_demand/central_asia_turkey_eurasia/
airport/output/macro_runs/<run_id>/<variant>/regional_aviation_demand/north_africa/
airport/output/macro_runs/<run_id>/<variant>/regional_aviation_demand/latin_america_caribbean/
airport/output/macro_runs/<run_id>/<variant>/regional_aviation_demand/sub_saharan_africa/
```

发布到 viewer 时会复制到：

```text
airport/output/regional_aviation_demand/
```

当前 `AVIATION_REGION_CONFIGS` 已开放 14 区。后续调参时，优先补区域参数，而不是复制脚本。

## 输入数据

主要读取区域宏观和区域对账输出：

```text
regional_gdp_growth_pct_reconciled
regional_reconciled_gdp_trillion_usd
regional_income_index
real_income_growth_pct
household_consumption_power_index
consumer_confidence_index
regional_headline_inflation_pct_reconciled
regional_policy_rate_pct_reconciled
regional_10y_yield_pct_reconciled
regional_currency_index
currency_pressure_index
regional_financial_conditions_index
regional_hy_spread_bps_reconciled
regional_credit_availability_index
regional_equity_index
regional_equity_return_pct_reconciled
regional_wealth_effect_index
regional_energy_cost_pressure_index_reconciled
regional_macro_stress_index_reconciled
regional_geopolitical_risk_index
branch_scenario_state
branch_scenario_id
regional_branch_transmission_active
regional_seed_momentum_label
regional_seed_effective_growth_bias_pct
regional_seed_aviation_propensity_bias_pct
regional_seed_investment_cycle_bias_pct
regional_seed_openness_bias_pct
regional_seed_demand_multiplier
```

后续机场层不应该直接用 GDP 判断客流。区域航空需求层就是中间翻译器。

## 区域 seed 对航空需求的影响

区域 seed 势能会先改变区域宏观，再在本层继续影响航空偏好：

- `regional_seed_aviation_propensity_bias_pct`：影响休闲、商务、VFR、长航线和转机需求。
- `regional_seed_openness_bias_pct`：更强地影响长航线、转机和国际旅游。
- `regional_seed_investment_cycle_bias_pct`：更强地影响商务出行和后续供给扩张。
- `regional_seed_demand_multiplier`：作为温和倍率，避免只靠 GDP 增长解释所有航空需求。

因此，两个 seed 里 GDP 增长相近的区域，也可能因为开放度、航空渗透率和投资周期不同，形成不同的航空需求曲线。

## 输出总览

v0.2 建议每个区域、每个 seed、每一年输出以下字段。

### 1. 总需求

```text
regional_air_demand_index
```

含义：区域总航空需求指数，初始年为 100。

它综合商务、旅游休闲、探亲访友、国际长途和中转需求。这个字段不是旅客人数，主要用于先看方向和周期弹性。

### 2. 增长率

```text
regional_air_demand_growth_pct
```

含义：区域航空需求指数的年度增长率。

它可以比 GDP 更有弹性：经济复苏时航空需求通常更快修复，危机、油价冲击或信用压力上行时也可能更快下滑。

### 3. 出行分类型需求

商务出行：

```text
business_travel_demand_index
business_travel_growth_pct
business_travel_share_pct
```

主要受 GDP 增长、企业信心、信用可得性、金融压力、股市财富效应和区域商务权重影响。

旅游/休闲：

```text
leisure_travel_demand_index
leisure_travel_growth_pct
leisure_travel_share_pct
```

主要受真实收入、消费信心、通胀压力、油价/票价压力、汇率压力和区域旅游暴露度影响。

探亲访友 / VFR：

```text
vfr_travel_demand_index
vfr_travel_growth_pct
vfr_travel_share_pct
```

主要受收入、价格敏感度、移民/侨民连接、家庭团聚需求和宏观压力影响。它应比商务和旅游更稳定，不宜大幅上蹿下跳。

国际长途：

```text
long_haul_demand_index
long_haul_growth_pct
long_haul_share_pct
```

主要受高收入人群、国际开放度、汇率、油价、全球金融压力和区域长途市场权重影响。

中转需求：

```text
transfer_demand_index
transfer_growth_pct
transfer_share_pct
```

主要受区域枢纽属性、地理连接性、全球长途需求、油价、地缘压力和航空网络稳定性影响。

## 价格敏感度

价格敏感度是单独的压力指标，不属于某一种出行需求。

```text
airfare_price_sensitivity_index
```

建议范围：0-100。

含义：

- 数值高：旅客更容易因为票价、汇率、通胀或收入压力减少出行。
- 数值低：旅客更稳定，高收入、商务、高端长途或刚性 VFR 占比更高。

主要输入：

```text
real_income_growth_pct
regional_headline_inflation_pct
regional_currency_index
currency_pressure_index
regional_energy_cost_pressure_index
consumer_confidence_index
regional_macro_stress_index
```

价格敏感度会影响旅游、VFR 和低端长途需求，也会影响后续机场商业消费转化。

## 价格弹性矩阵

`airfare_price_sensitivity_index` 是总体压力指标，但后续机场层还需要知道不同客群对票价的反应差异。因此 v0.1 应把价格弹性矩阵保留在数据流中。

建议字段：

```text
business_fare_elasticity
leisure_fare_elasticity
vfr_fare_elasticity
long_haul_fare_elasticity
transfer_fare_elasticity
premium_fare_elasticity
```

口径：使用弹性绝对值，数值越高表示越容易因票价上涨而减少出行。

建议范围：

| segment | typical range | 说明 |
|---|---:|---|
| `business` | 0.15-0.35 | 商务刚性强，对票价不敏感 |
| `premium` | 0.10-0.30 | 高端客更看重时间、服务和航线便利性 |
| `vfr` | 0.50-0.90 | 探亲访友有刚性，但仍受收入和票价影响 |
| `long_haul` | 0.70-1.10 | 长途票价高，受油价和汇率影响明显 |
| `transfer` | 0.80-1.30 | 中转客对票价、绕行和连接效率敏感 |
| `leisure` | 1.10-1.80 | 休闲旅游最容易被票价和收入压力压制 |

这组字段不一定进入 viewer，但应该进入 CSV/JSON。后续机场层可以用它模拟：

```text
油价上涨 -> 票价压力上升
  -> 休闲客流失更明显
  -> 商务和高端客留存更高
  -> 客流增速下降，但客单价和高端占比可能上升
```

## 消费倾向

消费倾向用于后续机场商业层，不直接等于收入。

消费倾向类指数使用软限制，不在某个高位突然封顶；年度增长率、占比和票价弹性仍保留合理边界，避免极端 seed 把下游机场层打穿。

### 1. 高端客倾向

```text
premium_passenger_propensity_index
premium_passenger_share_pct
```

主要受高收入水平、商务出行、国际长途、股市财富效应、金融压力和区域高端旅客结构影响。

### 2. 免税消费倾向

```text
duty_free_propensity_index
```

主要受国际长途、旅游需求、汇率、收入、免税机场属性和区域跨境购物习惯影响。

### 3. 奢侈品 / 精品消费倾向

```text
luxury_retail_propensity_index
```

主要受高端客倾向、股市财富效应、消费信心、汇率和国际客流影响。

### 4. 电子产品消费倾向

```text
electronics_retail_propensity_index
```

主要受收入、汇率、价格优势、亚洲跨境购物习惯、商务客和中转客结构影响。

### 5. 餐饮零售倾向

```text
food_beverage_propensity_index
general_retail_propensity_index
```

这两个可以作为后续机场商业层的普通消费底座。它们比奢侈品更稳定，更多受旅客量、候机时间、价格敏感度和消费信心影响。

## 区域差异参数

每个区域需要一组航空需求参数，不建议用同一套弹性硬套 14 区。

建议区域参数包括：

```text
business_travel_weight
leisure_travel_weight
vfr_travel_weight
long_haul_weight
transfer_hub_weight
domestic_market_depth
international_exposure
tourism_exposure
income_sensitivity
price_sensitivity_base
business_fare_elasticity_base
leisure_fare_elasticity_base
vfr_fare_elasticity_base
long_haul_fare_elasticity_base
transfer_fare_elasticity_base
premium_fare_elasticity_base
oil_fare_sensitivity
currency_travel_sensitivity
premium_mix_base
duty_free_culture_index
luxury_retail_affinity
electronics_retail_affinity
premium_business_pass_through
demand_adjustment_speed
```

`premium_business_pass_through` 用来控制商务和长途需求增长有多少会转化为高端客倾向。发展中区域可以低于 1.0，避免长期增长自动变成过高的高端客占比。`demand_adjustment_speed` 用来表达航空需求兑现速度，基础设施、航线覆盖和支付能力约束较强的区域可以更慢。

例如：

- 北美：商务、国内市场、财富效应更强。
- 中国大陆：国内需求、收入信心、政策周期和出境游弹性重要。
- 港澳台：国际、高端、免税、短途跨境和金融商务更强。
- 东南亚：旅游、低成本航空、价格敏感度和区域中转更强。
- 中东/海湾：长途联程、中转、高端客和油价相关性更强。
- 西欧/北欧：成熟商务、高收入、长途国际和价格压力并存。
- 南亚/印度：长期增长强，但价格敏感度高。

## v0.1 建模方式

v0.1 不建议直接做真实客流人数，先做指数层：

```text
macro drivers
  -> demand component growth
  -> component indices
  -> weighted total demand
  -> price sensitivity
  -> fare elasticity by segment
  -> consumption propensity
```

基本形式可以是：

```text
component_growth =
  trend_growth
  + gdp_beta * regional_growth_surprise
  + income_beta * real_income_growth
  + confidence_beta * confidence_gap
  - inflation_beta * inflation_pressure
  - fare_beta * energy_cost_pressure
  - stress_beta * macro_stress
  + wealth_beta * wealth_effect
  + branch_adjustment
```

然后进行平滑：

```text
smoothed_growth =
  previous_growth * persistence
  + raw_growth * adjustment_speed
```

这样可以避免航空需求增长率一年内跳得过快。

## 承接区域宏观分岔

区域航空需求层不单独抽全球历史事件。

区域宏观层已经负责表达“同一个全球分岔，对不同区域影响不同”。区域航空需求层只承接这些结果，并把它们翻译成航空需求结构和机场层事件提示。

主要读取：

```text
branch_scenario_state
branch_scenario_id
regional_branch_transmission_active
regional_branch_exposure_index
regional_branch_growth_impulse_pct
regional_branch_inflation_impulse_pct
regional_branch_credit_impulse_bps
regional_branch_fx_pressure_impulse
regional_branch_energy_impulse
regional_branch_asset_impulse_pct
regional_branch_confidence_impulse
regional_macro_stress_index
regional_energy_cost_pressure_index
regional_credit_stress_index
consumer_confidence_index
```

如果全球路径进入 `occurred` / `counterfactual`，航空需求会先通过区域宏观自然变化，再由本层生成航空语义：

```text
aviation_demand_regime
airport_event_hint
airport_event_pressure_index
```

建议事件提示：

| regional macro signal | airport_event_hint | 航空含义 |
|---|---|---|
| `energy_shock_escalation` + 高能源暴露 | `fare_shock_leisure_drag` | 票价压力上升，休闲和长途需求更弱 |
| `dollar_squeeze_escalation` + 高 FX 压力 | `outbound_fx_squeeze` | 出境游和长途需求受压，VFR 更稳 |
| `credit_accident` / `bank_lending_trap` | `business_travel_credit_drag` | 商务、高端和会展需求下调 |
| `false_dawn` | `recovery_reversal_warning` | 复苏初期改善，但后续需求可能回落 |
| `soft_landing_success` | `broad_travel_recovery` | 商务和休闲同步温和修复 |
| `liquidity_bubble` / `risk_asset_bull_fragility` | `premium_mix_volatility` | 高端客和免税倾向上升，但脆弱性更高 |

这些字段不是机场层的最终事件系统，只是把区域宏观分岔转译成机场层容易消费的标签。

## 边界

这一层暂时不做：

- 不分具体机场。
- 不分具体航线。
- 不模拟航司运力、机队、票价收益管理。
- 不模拟机场容量、跑道、航站楼瓶颈。
- 不输出供给侧容量约束，机场 slot、跑道和航站楼瓶颈留给后续机场供给层处理。
- 不直接计算机场收入。
- 不做国家级签证、边境政策、战争空域关闭等航空专项事件。
- 不让航空需求反向影响 GDP 或区域宏观。

这一层只负责把区域宏观翻译成区域航空需求和旅客结构。

## 后续连接

区域航空需求稳定后，先交给区域航空供给/满足率层判断有多少潜在需求能被运力满足，再进入机场层：

```text
regional_air_demand_index
business_travel_demand_index
leisure_travel_demand_index
vfr_travel_demand_index
long_haul_demand_index
transfer_demand_index
airfare_price_sensitivity_index
business_fare_elasticity
leisure_fare_elasticity
vfr_fare_elasticity
long_haul_fare_elasticity
transfer_fare_elasticity
premium_fare_elasticity
premium_passenger_propensity_index
duty_free_propensity_index
luxury_retail_propensity_index
electronics_retail_propensity_index
airport_event_hint
airport_event_pressure_index
```

供给层会优先读取这些需求字段，输出实际可服务客流、未满足需求和分项满足率。机场层再根据机场类型分配：

```text
hub_airport
capital_business_airport
tourism_destination_airport
low_cost_airport
long_haul_gateway_airport
transfer_airport
```

等指数层稳定后，再追加真实规模字段：

```text
regional_passenger_volume_million
domestic_passenger_million
international_passenger_million
transfer_passenger_million
premium_passenger_million
```
