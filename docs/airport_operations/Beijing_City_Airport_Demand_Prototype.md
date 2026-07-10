# 北京城市机场需求层原型

本文记录 `beijing_airport_system` 如何从区域航空宏观层推导出城市机场市场需求。

这是机场经营层的北京样板，不是正式客流预测。它的目的，是把三件事先接起来：

```text
city airport registry
  -> market tier / market type
  -> regional-aligned passenger components
  -> city airline supply bottleneck
  -> city airport capacity bottleneck
```

## 运行入口

```powershell
py -3 .\airport\macro_layers\city_airport_market_demand_layer_sim.py --market beijing_airport_system
```

默认读取：

```text
airport/output/regional_aviation_demand/china_mainland_aviation_demand_seed_sweep.csv
airport/output/regional_air_capacity_supply/china_mainland_air_capacity_supply_seed_sweep.csv
```

默认输出：

```text
airport/output/city_airport_market_demand/china_mainland/beijing_airport_system_city_airport_demand_seed_sweep.csv
airport/output/city_airport_market_demand/china_mainland/beijing_airport_system_city_airport_demand_summary.json
airport/output/city_airport_market_demand/china_mainland/beijing_airport_system_city_airport_demand_viewer_data.js
```

默认配置读取：

```text
airport/config/facility_size_catalogs/standard_terminal_sizes_v1.json
airport/config/city_airport_markets/china_mainland/beijing_airport_system.json
```

## 北京 registry 样板

```text
city_airport_market_id = beijing_airport_system
city_name = 北京
region_id = china_mainland
region_name = 中国大陆
market_tier = global_hub
market_type = dual_airport_capital_gateway
airport_system = 首都 + 大兴
```

第一版校准参数：

```text
baseline_region_demand_share_pct = 14.5
baseline_city_potential_passengers_million = 118.9
airport_facility_slot_profile_id = beijing_dual_airport_5_slot_v1
facility_size_catalog_id = standard_terminal_sizes_v1
city_airport_design_capacity_million = 154.0
city_airport_max_capacity_million = 200.0
annual_long_term_city_growth_bias_pct = 0.70
max_long_term_city_growth_bias_pct = 42.0
target_long_term_potential_range_million = 320.0 / 400.0
seed_potential_model = china_core_gateway_seed_potential_v1
seed annual growth bias range = -0.24% / +0.28%
seed max growth bias range = -12.0% / +15.0%
seed release = year_index 5 -> 25
seed regional correlation weight = 0.28
base_airline_supply_passengers_million = 122.0
regional_airline_capacity_growth_capture = 0.40
annual_local_airline_supply_growth_pct = 0.28
max_local_airline_supply_growth_pct = 22.0
business_base_share_pct = 32.0
leisure_base_share_pct = 38.0
vfr_base_share_pct = 13.0
long_haul_base_share_pct = 10.0
transfer_base_share_pct = 7.0
```

含义：

- 北京不是简单跟随全国增长，而是按区域航空层同一套旅客分项分别计算，再合成总需求。
- 北京可以有城市权重和敏感度，但分项字段必须对应区域层的 `business / leisure / vfr / long_haul / transfer`。
- v4 开始北京启用 seed 城市航空势能模板：不同 seed 会逐步改变长期北京航空体量，但效果较窄，并会被中国大陆区域航空/宏观环境放大或压低。
- 航司供给是机场容量之外的第二道瓶颈，表达“机场够大，但航司不一定投放足够座位”。
- 北京机场容量来自首都和大兴的设施槽位，不再随区域供给曲线平滑增长。
- 航站楼规格和槽位等级规则来自 `standard_terminal_sizes_v1.json`，代码只保留兜底默认值。
- 北京长期需求曲线被适度抬高，目标是让远期需求进入 3 亿多到接近 4 亿的区间，从而消耗双机场扩建空间。
- 低于设计容量是正常运行，超过设计容量但低于实际上限是拥挤运行，超过实际上限才形成机场侧未满足需求。

## 从区域层到北京五类需求

区域航空需求层先给出中国大陆航空需求指数和客群结构：

```text
regional_air_demand_index
business_travel_share_pct
leisure_travel_share_pct
vfr_travel_share_pct
long_haul_share_pct
transfer_share_pct
premium_passenger_propensity_index
airport_event_hint
branch_scenario_state
```

区域航空供给层提供绝对量和供给状态：

```text
potential_passengers_million
served_passengers_million
regional_air_capacity_index
available_seat_capacity_index
capacity_fulfillment_pct
supply_regime
airline_capacity_confidence_index
fleet_expansion_appetite_index
route_growth_appetite_index
capacity_cut_risk_index
aircraft_delivery_constraint_index
crew_labor_constraint_index
maintenance_cost_pressure_index
airport_slot_constraint_index
```

北京 v0.11 不再先用区域份额直接放大总量，而是先算和区域航空需求层一致的五个旅客分项：

```text
business
leisure
vfr
long_haul
transfer
```

每个分项有自己的基准占比和宏观敏感度：

```text
component_passengers =
  baseline_city_potential_passengers_million
  * long_term_growth_multiplier
  * seed_city_potential_multiplier
  * component_base_share_pct
  * component_demand_index
```

北京总潜在需求由分项合成：

```text
city_potential_passengers_million =
  sum(component_passengers)

city_demand_share_pct =
  city_potential_passengers_million
  / regional_potential_passengers_million
  * 100
```

这意味着北京可以参考中国大陆区域航空需求，但不会被迫和区域总盘子同速增长。

## Seed 航空势能实验

北京 v4 额外读取：

```text
demand_model.seed_potential_model
```

这个模板只影响城市潜在客流，不直接改机场容量、航司供给、季度经营、财务或估值。它的作用是让不同 seed 下的北京长期航空体量不完全按同一条现实锚定曲线走。

第一版规则：

```text
stable hash(seed, beijing_airport_system, template_id)
  -> seed_city_structural_momentum_score
  -> seed_city_annual_growth_bias_pct / seed_city_max_growth_bias_pct
  -> year_index 5 后逐步释放，year_index 25 左右完整释放
  -> 乘以区域航空/宏观对齐修正
  -> seed_city_potential_multiplier
```

北京是核心门户城市，因此模板范围较窄。它可以让某些世界里的北京长期更强或更弱，但不应让北京脱离一线航空基本盘。更大的随机分化应留给成渝、杭州、武汉、西安、青岛、天津、旅游城市和边疆门户等后续模板。

北京分项对区域指标的读取方向：

| 分项 | 主要驱动 |
|---|---|
| business | 区域商务需求、高端客倾向、区域总需求、消费者信心、宏观压力 |
| leisure | 区域休闲需求、区域总需求、信心、票价和汇率压力 |
| vfr | 区域 VFR/探亲需求、区域总需求、票价和汇率压力 |
| long_haul | 区域长途需求、商务需求、高端客倾向、票价和汇率压力 |
| transfer | 区域中转需求、区域供给增长、长途需求、时刻/槽位压力 |

北京本地机场容量由设施槽位汇总：

```text
PEK_SLOT_1 主槽位   首都T3航站楼   extra_large = 50 / 65
PEK_SLOT_2 次槽位   首都T2航站楼   large       = 32 / 45

PKX_SLOT_1 主槽位     大兴T1航站楼     giant = 72 / 90
PKX_SLOT_2 次槽位     大兴T2航站楼     empty = 0 / 0
PKX_SLOT_3 辅助槽位1  大兴扩建槽位 1  empty = 0 / 0
PKX_SLOT_4 辅助槽位2  大兴扩建槽位 2  empty = 0 / 0
PKX_SLOT_5 辅助槽位3  大兴扩建槽位 3  empty = 0 / 0

city_airport_design_capacity_million = 154
city_airport_max_capacity_million    = 200
```

后续扩建不设置固定中期容量。玩家在首都/大兴的空槽位中自由选择允许规格，系统按已启用槽位动态求和。

北京航司供给先独立计算。v0.17 起，城市潜在客流仍是长期主轴；航司供给作为更快变量，会以潜在客流对应的座位需求作为规划锚点，但叠加更强的航司投放周期、供给冲击、事件压力和上一年供给惯性：

```text
city_airline_supply_target_index =
  trend_index
  + demand_pull_from_potential_anchor
  + airline confidence / fleet appetite / route appetite
  - aircraft delivery / crew / maintenance / profit / slot constraints
  + cycle impulse
  + shock impulse
  + event impulse

city_airline_supply_index =
  previous_city_airline_supply_index
  + (city_airline_supply_target_index - previous_city_airline_supply_index)
    * adjustment_speed

city_airline_supply_passengers_million =
  base_airline_supply_passengers_million
  * city_airline_supply_index / 100
```

供给上限不再是固定指数，而是随 `city_airline_supply_potential_anchor_index` 动态上移。输出会保留 `city_airline_supply_potential_anchor_index`、`city_airline_supply_trend_index`、`city_airline_supply_demand_pull_pct`、`city_airline_supply_cycle_impulse_pct`、`city_airline_supply_shock_impulse_pct`、`city_airline_supply_lag_adjustment_pct`、`city_airline_supply_ceiling_index` 和 `city_airline_supply_volatility_regime`，用于解释某年是需求拉动、航司周期、约束冲击还是恢复滞后导致供给变化。

v0.18 起，航司供给也会拆成五个分项。总航司供给仍由上面的城市供给模型决定，分项供给则以潜在分项客流为基础，再叠加航司偏好和约束：

```text
component_airline_supply_weight =
  component_potential_passengers
  * component_supply_preference_multiplier

component_airline_supply_passengers =
  city_airline_supply_passengers
  * component_airline_supply_weight / sum(component_airline_supply_weight)
```

其中商务更受航司信心、宏观压力和利润压力影响；休闲/探亲更受票价和汇率压力影响；长途更受开放度、汇率和宏观压力影响；中转更受航线投放、机队扩张和槽位约束影响。这一层用于解释“哪类需求缺座位”，不直接把承接分项复杂化。

北京最终可服务需求由需求、航司供给、机场容量三者共同决定：

```text
airport_capacity_allocation_ratio =
  min(1, city_airport_max_capacity_million / city_airline_supply_passengers_million)

airport_capacity_limited_airline_supply_million =
  max(0, city_airline_supply_passengers_million - city_airport_max_capacity_million)

city_effective_service_capacity_million =
  city_airline_supply_passengers_million
  * airport_capacity_allocation_ratio

city_served_passengers_million =
  min(
    city_potential_passengers_million,
    city_effective_service_capacity_million
  )

city_unmet_passengers_million =
  city_potential_passengers_million - city_served_passengers_million
```

如果机场最大容量达不到航司供给，不再新增优先级分配层，而是等比例压缩五类客群：

```text
final_passenger_service_ratio =
  city_served_passengers_million / city_potential_passengers_million

business_served_passengers_million =
  business_passengers_million * final_passenger_service_ratio

leisure_served_passengers_million =
  leisure_passengers_million * final_passenger_service_ratio

vfr_served_passengers_million =
  vfr_passengers_million * final_passenger_service_ratio

long_haul_served_passengers_million =
  long_haul_passengers_million * final_passenger_service_ratio

transfer_served_passengers_million =
  transfer_passengers_million * final_passenger_service_ratio
```

这一步就是机场经营层的核心：区域航空需求只是背景环境，城市分项需求决定本地潜在客流，航司供给和机场本地容量共同决定实际可服务客流。

## 样板输出

基于当前 `seed = 20260630` 的区域层输出，北京样板结果为：

| year | potential | airline_supply | design_capacity | max_capacity | airport_allocation | total_fulfillment | served | unmet | crowding | bottleneck |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|
| 2025 | 117.7751 | 122.5878 | 154.0000 | 200.0000 | 100.0000 | 100.0000 | 117.7751 | 0.0000 | 0.0000 | demand_limited |
| 2035 | 130.3978 | 115.7838 | 154.0000 | 200.0000 | 100.0000 | 88.7928 | 115.7838 | 14.6140 | 0.0000 | airline_bottleneck |
| 2050 | 160.0446 | 124.4635 | 154.0000 | 200.0000 | 100.0000 | 77.7680 | 124.4635 | 35.5811 | 0.0000 | airline_bottleneck |
| 2065 | 220.0999 | 152.4639 | 154.0000 | 200.0000 | 100.0000 | 69.2703 | 152.4639 | 67.6360 | 0.0000 | airline_bottleneck |
| 2085 | 360.0298 | 264.1222 | 154.0000 | 200.0000 | 75.7225 | 55.5510 | 200.0000 | 160.0298 | 100.0000 | airport_bottleneck |

潜在分项需求结果：

| year | business | leisure | vfr | long_haul | transfer |
|---|---:|---:|---:|---:|---:|
| 2025 | 37.7665 | 44.4215 | 15.4258 | 11.8384 | 8.3230 |
| 2035 | 47.2565 | 44.5130 | 17.4237 | 12.5078 | 8.6969 |
| 2050 | 67.0881 | 48.7902 | 21.6644 | 13.5408 | 8.9610 |
| 2065 | 105.1442 | 58.9883 | 29.0505 | 16.5059 | 10.4109 |
| 2085 | 132.3690 | 127.2660 | 49.3851 | 33.4260 | 17.5836 |

最终服务分项结果：

| year | business_served | leisure_served | vfr_served | long_haul_served | transfer_served |
|---|---:|---:|---:|---:|---:|
| 2025 | 37.7665 | 44.4215 | 15.4258 | 11.8384 | 8.3230 |
| 2035 | 41.9603 | 39.5243 | 15.4710 | 11.1060 | 7.7222 |
| 2050 | 52.1731 | 37.9432 | 16.8480 | 10.5304 | 6.9688 |
| 2065 | 72.8337 | 40.8614 | 20.1234 | 11.4337 | 7.2117 |
| 2085 | 73.5323 | 70.6975 | 27.4339 | 18.5685 | 9.7679 |

## 当前解释

北京样板传达的是：

- 区域层给出“中国大陆航空需求环境”，不是直接决定北京客流。
- 北京先拆成和区域航空层一致的五类旅客需求，不另起本地分项口径。
- 远期北京需求被抬到 3 亿多，既能制造双机场扩建压力，又不会像 v0.1 那样被全国总盘子机械推到 5 亿以上。
- 北京商务占比提高，但休闲、VFR、长途和中转需求仍保留独立空间。
- 2035、2050 和 2065 的机场最大容量仍然足够，但航司可投放供给不足，因此出现 `airline_bottleneck`。
- 2085 当前初始槽位无法覆盖潜在需求和航司供给，进入 `airport_bottleneck`，这会推动玩家启用大兴T2航站楼、辅助槽位，或规划第三机场。

## 种子和历史岔路

城市机场需求层逐行保留区域层的：

```text
seed
branch_scenario_id
branch_scenario_state
branch_effect_phase
airport_event_hint
```

因此只要输入换成某个 seed 或某条历史岔路 run 下的区域航空需求/供给 CSV，北京输出会跟着同一条路径生成。默认输出按 `region_id` 分目录保存，后续多城市不会混在一个目录里。

v0.11 初始槽位容量抽查：

| path | seed / branch | peak_potential | design_capacity | max_capacity | max_airport_gap | airport_bottleneck_rows |
|---|---|---:|---:|---:|---:|---:|
| baseline | 20260630 | 360.0298 | 154.0000 | 200.0000 | 160.0298 | 9 |

这说明当前 PEK + PKX 初始槽位可以承接早期客流，但远期会形成稳定的机场扩建压力。部分中期未满足客流来自航司供给不足；远期则会转为机场最大容量不足。

## 后续推广

推广到 341 个机场市场时，可以先把每个城市补成类似配置：

```text
city_airport_market_id
region_id
market_tier
market_type
baseline_region_demand_share_pct
airport_facility_slot_profile_id
facility_slots
default_design_capacity_million
default_max_capacity_million
annual_long_term_city_growth_bias_pct
max_long_term_city_growth_bias_pct
base_airline_supply_passengers_million
regional_airline_capacity_growth_capture
annual_local_airline_supply_growth_pct
airline_supply_demand_pull_capture
airline_supply_cycle_amplitude_pct
airline_supply_shock_amplitude_pct
airline_supply_adjustment_speed
airline_supply_volatility_bias
commercial_biases
future_supply_events
regional_aligned_component_base_shares
regional_aligned_component_sensitivity_params
```

第一版不需要真实精确客流完全对上，只需要让区域总需求、城市分摊、客群结构和机场容量瓶颈的方向关系稳定。
