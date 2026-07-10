# Regional Air Capacity Supply Layer Design

## 当前定位

区域航空供给层位于区域航空需求层之后、机场客运分配层之前。

它不模拟具体航司公司、机队明细、航线网络或票价系统，而是把区域潜在航空需求翻译成：

```text
这个区域今年有多少航空需求可以被运力满足？
区域座位/航班供给是否紧张？
哪些旅客类型更容易被保留或挤出？
供给紧张是否会推高票价并压制实际客流？
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

## 边界

这一层是轻量的区域供给满足层，不是完整航司经营层。

它应该做：

```text
潜在航空需求
  -> 区域可供座位/运力
  -> 实际可服务客流
  -> 未满足需求
  -> 分项客群满足率
  -> 供给导致的票价压力
```

它暂时不做：

```text
单个航司财报
具体机型和机龄
航司联盟
逐条航线排班
机场收费谈判
常旅客计划
```

这些可以等机场层和航线层更成熟后再加。

## 输入

### 1. 区域航空需求层

主要读取：

```text
regional_air_demand_index
regional_air_demand_growth_pct
business_travel_demand_index
leisure_travel_demand_index
vfr_travel_demand_index
long_haul_demand_index
transfer_demand_index
business_travel_share_pct
leisure_travel_share_pct
vfr_travel_share_pct
long_haul_share_pct
transfer_share_pct
airfare_price_sensitivity_index
airfare_pressure_index
business_fare_elasticity
leisure_fare_elasticity
vfr_fare_elasticity
long_haul_fare_elasticity
transfer_fare_elasticity
premium_passenger_share_pct
airport_event_hint
airport_event_pressure_index
branch_scenario_id
branch_effect_phase
```

含义：

```text
需求层负责告诉供给层“想飞的人有多少、结构如何、对价格有多敏感”。
供给层负责判断“这些需求中有多少能变成实际客流”。
```

### 2. 区域宏观层

航司扩张或收缩供给时，应该参考区域宏观条件：

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
regional_credit_spread_bps
regional_credit_availability_index
regional_liquidity_index
regional_currency_index
regional_currency_pressure_index
regional_energy_cost_pressure_index
regional_macro_stress_index
regional_geopolitical_risk_index
regional_equity_index
regional_equity_return_pct
```

这些变量对应航司视角：

```text
GDP / 收入 / 信心
  -> 未来订票需求和载客率预期

通胀 / 油价 / 能源压力
  -> 燃油、人工、维修和机场服务成本

利率 / 信用 / 流动性
  -> 飞机融资、租赁、债务再融资和航司破产压力

货币 / 美元压力
  -> 进口燃油、飞机租赁、美元债和出境购买力

股市 / 财富效应
  -> 商务和高端客需求信心

地缘风险
  -> 绕飞、航线暂停、保险成本和中转路径变化
```

### 3. 全球层补充

如果区域字段缺失，供给层可以读取全球字段作为 fallback：

```text
brent_oil_price
oil_yoy_change_pct
global_policy_rate_pct
global_10y_yield_pct
dollar_index
global_liquidity_index
hy_spread_bps
ig_spread_bps
bank_lending_sentiment
financial_stress_index
branch_scenario_state
```

## 输出字段

### 1. 总供给与满足率

```text
regional_air_capacity_index
regional_air_capacity_growth_pct
available_seat_capacity_index
potential_passenger_demand_index
served_passenger_demand_index
unmet_passenger_demand_index
capacity_utilization_pct
load_factor_pct
capacity_fulfillment_pct
capacity_fare_pressure_index
supply_regime
```

解释：

```text
potential_passenger_demand_index
  区域潜在需求，通常来自 regional_air_demand_index。

available_seat_capacity_index
  区域可供座位/航班承载能力。

served_passenger_demand_index
  实际被供给满足、可以进入机场系统的客流需求。

unmet_passenger_demand_index
  因运力、票价、地缘或融资约束而没有被满足的需求。

capacity_utilization_pct
  潜在需求相对于可用供给的压力。

load_factor_pct
  实际载客率近似值，可作为航司盈利和票价压力的状态变量。
```

### 2. 分项供给满足率

```text
business_served_index
leisure_served_index
vfr_served_index
long_haul_served_index
transfer_served_index

business_fulfillment_pct
leisure_fulfillment_pct
vfr_fulfillment_pct
long_haul_fulfillment_pct
transfer_fulfillment_pct
```

默认分配逻辑：

```text
商务客
  保留优先级最高，票价不敏感，运力紧张时更容易被服务。

高端/长途客
  航司收益较高，但受油价、汇率和地缘风险影响较大。

VFR
  刚性中等偏高，价格敏感低于纯休闲，但高于商务。

休闲客
  最容易被票价和容量挤出。

中转客
  取决于区域枢纽属性。中东/海湾、港澳台、东南亚、欧亚桥可保留更高中转供给。
```

### 3. 航司供给状态

```text
airline_capacity_confidence_index
airline_profit_pressure_index
fleet_expansion_appetite_index
route_growth_appetite_index
capacity_cut_risk_index
aircraft_delivery_constraint_index
crew_labor_constraint_index
maintenance_cost_pressure_index
airport_slot_constraint_index
```

这些字段不一定都要在 viewer 里展示，但可以保留在数据流中，供机场层和后续调参使用。

### 4. 真实人数预留

当前区域航空需求层是指数。如果后续为每个区域加 2025 年基准客流，就可以输出真实数量：

```text
baseline_region_passenger_demand_million
potential_passengers_million
available_seats_million
served_passengers_million
unmet_passengers_million
```

真实人数换算建议：

```text
potential_passengers_million
  = baseline_region_passenger_demand_million
    * regional_air_demand_index / 100

served_passengers_million
  = potential_passengers_million
    * capacity_fulfillment_pct / 100
```

## 航司供给决策因素

### 1. 需求强弱

航司首先看需求：

```text
regional_air_demand_growth_pct
business_travel_demand_index
leisure_travel_demand_index
vfr_travel_demand_index
long_haul_demand_index
transfer_demand_index
premium_passenger_share_pct
```

如果需求强且商务/高端/中转占比高，供给扩张意愿更强。

如果需求强但主要来自高价格敏感休闲客，供给扩张会更谨慎，因为票价一涨就可能损失客流。

### 2. 盈利条件

航司并不是只看客流，还看这部分客流能不能赚钱：

```text
airfare_pressure_index
premium_passenger_share_pct
business_travel_share_pct
brent_oil_price
regional_energy_cost_pressure_index
regional_headline_inflation_pct_reconciled
regional_currency_pressure_index
```

高油价和弱货币会抬高成本。高端客、商务客和中转收益可以部分抵消成本压力。

### 3. 融资条件

航空是资本密集行业，扩张很依赖融资：

```text
regional_policy_rate_pct_reconciled
regional_10y_yield_pct_reconciled
regional_credit_spread_bps
regional_credit_availability_index
regional_liquidity_index
bank_lending_sentiment
hy_spread_bps
```

高利率、信用利差走阔、银行惜贷时，航司会推迟飞机引进、减少开新航线，甚至主动削减运力。

### 4. 运营约束

即使需求和盈利都不错，供给也可能上不去：

```text
aircraft_delivery_constraint_index
crew_labor_constraint_index
maintenance_cost_pressure_index
airport_slot_constraint_index
airport_capacity_constraint_index
regional_geopolitical_risk_index
```

这些变量更适合从区域/机场基础设施配置中来，而不是从宏观层直接生成。

### 5. 区域结构

不同区域供给反应不同：

```text
domestic_market_depth
international_exposure
transfer_hub_weight
tourism_exposure
market_maturity
airport_slot_constraint_base
fleet_delivery_dependency
```

例如：

```text
北美、中国大陆
  国内市场深，供给恢复较快。

西欧/北欧、日韩、港澳台
  成熟市场，部分机场时刻紧张，需求强时更容易转成票价压力。

中东/海湾、欧亚桥
  中转枢纽属性强，长途和中转供给更重要。

东南亚、南欧/地中海、北非、拉美/加勒比
  旅游和价格敏感客更多，供给紧张时休闲客更容易被挤出。

撒哈拉以南非洲、南亚/印度
  长期潜力强，但基础设施、融资和机队约束会让供给兑现更慢。
```

## 核心机制建议

### 1. 供给调整要滞后

运力不能像需求一样立刻变化。

```text
target_capacity_growth
  = demand_signal
    + profitability_signal
    + financing_signal
    - operational_constraint

actual_capacity_growth
  = smooth(previous_capacity_growth, target_capacity_growth, effective_adjustment_speed)
```

扩张应慢于需求上行，收缩可以略快于扩张。

### 2. 供给紧张要先影响低收益客群

如果需求超过容量：

```text
capacity_gap = potential_demand - available_capacity
```

挤出顺序建议：

```text
leisure
  -> transfer
  -> long_haul
  -> vfr
  -> business
```

但中东/海湾、欧亚桥、东南亚等枢纽区域，中转客的保留优先级可以更高。

### 3. 供给不足会反向增加票价压力

供给层应输出：

```text
capacity_fare_pressure_index
```

它后续会影响：

```text
Airport passenger allocation
Airport commercial business
```

供给紧张时，实际客流可能少于潜在需求，但高端客和客单价可能更强。

### 4. 危机后供给修复要慢

信用危机、美元挤兑、能源冲击后，需求恢复不代表供给立刻恢复。

```text
capacity_recovery_drag
  = credit_stress
    + financing_cost
    + airline_profit_pressure
    + delivery_constraint
```

这能避免模型出现“需求 V 型反弹，供给也立刻完全跟上”的不自然路径。

## 事件和分岔传导

供给层不单独抽全球事件，只承接宏观和航空需求层的状态。

典型传导：

```text
能源危机
  -> fuel cost shock
  -> long-haul and leisure capacity cut
  -> fare pressure up

美元挤兑
  -> FX and USD financing pressure
  -> emerging market airline capacity stress
  -> outbound demand served less

信用紧缩
  -> financing unavailable
  -> fleet expansion delayed
  -> capacity recovery slow

软着陆
  -> confidence and financing improve
  -> capacity growth normalizes

风险资产牛市
  -> premium/business demand strong
  -> capacity growth improves, but bubble fragility remains
```

## 与机场层的接口

机场客运分配层不应该直接读取潜在需求，而应该优先读取供给满足后的客流：

```text
served_passenger_demand_index
business_served_index
leisure_served_index
vfr_served_index
long_haul_served_index
transfer_served_index
capacity_fare_pressure_index
load_factor_pct
supply_regime
```

这样机场层拿到的是：

```text
实际能够进入机场系统的客流
```

而不是：

```text
想飞但没有座位、票价太贵或航线不足的潜在需求
```

## 与机场商业层的接口

机场商业层可以读取：

```text
served_passenger_demand_index
premium_passenger_share_pct
business_fulfillment_pct
leisure_fulfillment_pct
long_haul_fulfillment_pct
transfer_fulfillment_pct
capacity_fare_pressure_index
load_factor_pct
```

含义：

```text
高载客率和供给紧张
  可能提高票价和高端客占比，但不一定提高零售转化率。

休闲客被挤出
  可能降低餐饮、普通零售和旅游型免税消费。

商务和高端客保留
  有利于精品、奢侈品和贵宾服务。

中转客保留
  有利于免税、餐饮和精品，但取决于停留时间。
```

## 全量 v0.1 建议实现范围

全量第一版只需要：

```text
1. 为 14 区配置基础容量参数
2. 从区域航空需求读取潜在需求
3. 生成区域可用供给指数
4. 计算总满足率和分项满足率
5. 输出供给紧张造成的票价压力
6. 接入 orchestrator 归档
7. viewer 暂时只展示总供给、满足率、未满足需求和 supply_regime
```

暂时不要做具体航司、具体航线、具体机型。

## 当前实现状态

已完成 14 区区域供给 v0.1：

```text
airport/macro_layers/regional_air_capacity_supply_layer_sim.py
```

已开放区域：

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

运行命令示例：

```powershell
py -3 .\airport\macro_layers\regional_air_capacity_supply_layer_sim.py --region north_america
py -3 .\airport\macro_layers\regional_air_capacity_supply_layer_sim.py --region china_mainland
py -3 .\airport\macro_layers\regional_air_capacity_supply_layer_sim.py --region west_north_europe
py -3 .\airport\macro_layers\regional_air_capacity_supply_layer_sim.py --region japan_korea
py -3 .\airport\macro_layers\regional_air_capacity_supply_layer_sim.py --region southeast_asia
py -3 .\airport\macro_layers\regional_air_capacity_supply_layer_sim.py --region south_asia_india
py -3 .\airport\macro_layers\regional_air_capacity_supply_layer_sim.py --region hk_macao_taiwan
py -3 .\airport\macro_layers\regional_air_capacity_supply_layer_sim.py --region middle_east_gulf
py -3 .\airport\macro_layers\regional_air_capacity_supply_layer_sim.py --region oceania
py -3 .\airport\macro_layers\regional_air_capacity_supply_layer_sim.py --region south_east_europe_mediterranean
py -3 .\airport\macro_layers\regional_air_capacity_supply_layer_sim.py --region central_asia_turkey_eurasia
py -3 .\airport\macro_layers\regional_air_capacity_supply_layer_sim.py --region north_africa
py -3 .\airport\macro_layers\regional_air_capacity_supply_layer_sim.py --region latin_america_caribbean
py -3 .\airport\macro_layers\regional_air_capacity_supply_layer_sim.py --region sub_saharan_africa
```

输入来自：

```text
airport/output/regional_aviation_demand/<region>_aviation_demand_seed_sweep.csv
```

输出到：

```text
airport/output/regional_air_capacity_supply/<region>_air_capacity_supply_seed_sweep.csv
airport/output/regional_air_capacity_supply/<region>_air_capacity_supply_summary.json
airport/output/regional_air_capacity_supply/<region>_air_capacity_supply_viewer_data.js
```

当前 v0.1 使用可调的 2025 年区域客流锚点：

```text
north_america       1200.0
china_mainland       820.0
west_north_europe    900.0
japan_korea          330.0
southeast_asia       520.0
south_asia_india     390.0
hk_macao_taiwan      230.0
middle_east_gulf     310.0
oceania              165.0
south_east_europe_mediterranean 430.0
central_asia_turkey_eurasia     260.0
north_africa                    210.0
latin_america_caribbean         620.0
sub_saharan_africa              180.0
```

这些数字是模型换算锚点，不是官方统计口径。后续如果要做真实机场吞吐量，需要用更严谨的区域客运基准替换它们。

以 seed 20260630 的现有需求输出为例，14 区供给层生成的形态是：

```text
region                                demand final  capacity final  final fulfillment  min fulfillment
north_america                                202.9          193.3              95.3%            79.4%
china_mainland                               351.6          353.3             100.0%            78.1%
west_north_europe                            152.4          140.9              92.4%            77.3%
japan_korea                                  128.3          115.9              90.3%            78.6%
southeast_asia                               287.7          270.5              94.0%            73.8%
south_asia_india                             398.5          369.6              92.8%            71.4%
hk_macao_taiwan                              159.2          148.7              93.4%            78.7%
middle_east_gulf                             274.9          271.0              98.6%            83.7%
oceania                                      171.0          150.3              87.9%            75.2%
south_east_europe_mediterranean              125.0          112.2              89.7%            89.2%
central_asia_turkey_eurasia                  194.2          160.9              82.8%            69.9%
north_africa                                 184.1          138.6              75.3%            68.0%
latin_america_caribbean                      165.2          131.9              79.9%            70.6%
sub_saharan_africa                           236.4          175.0              74.0%            68.0%
```

这个版本刻意让供给慢于需求，但不会永久硬封顶：需求冲击后会出现高载客率、票价压力和休闲客挤出，随后航司通过机队、航线和班次逐步追赶。中国大陆长期扩张能力更强，西欧/北欧、日韩和港澳台保留更明显的成熟市场容量瓶颈；东南亚保留旅游和低成本航空弹性；南亚/印度保留高增长下的基础设施追赶压力；中东/海湾保留中转和高端长途枢纽弹性；大洋洲保留远距离国际线和机队约束；南欧/东欧/地中海保留旅游旺盛但休闲客更容易被票价和运力挤出的特征；中亚/土耳其/欧亚桥保留中转和地缘扰动弹性；北非、拉美/加勒比和撒哈拉以南非洲保留旅游/VFR 需求下的价格敏感、融资约束和基础设施追赶压力。

当前已接入 orchestrator 主 run。归档 run 会写到：

```text
airport/output/macro_runs/<run_id>/<variant>/regional_air_capacity_supply/<region>/
```

`--publish-viewer baseline` 或 `--publish-viewer scenario` 会同步复制到：

```text
airport/output/regional_air_capacity_supply/
```

当前已经接入 `airport/global_gdp_viewer.html` 的“航空需求”视图。14 区都会在总览卡片和年度表格中显示五类旅客供给满足率：

```text
business_fulfillment_pct
leisure_fulfillment_pct
vfr_fulfillment_pct
long_haul_fulfillment_pct
transfer_fulfillment_pct
```

## 后续扩展

供给层稳定后，可以继续接：

```text
Regional air capacity / supply fulfillment
  -> Airport passenger allocation
  -> Airport capacity and slot constraints
  -> Airport commercial business
  -> Optional airline route competition
```

也可以在更后面增加：

```text
airline_strategy_layer
route_network_layer
aircraft_fleet_layer
ticket_fare_layer
```

但这些不应该抢在机场客运分配层之前。
