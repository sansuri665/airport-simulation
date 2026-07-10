# City Airport Market Layer Plan

## 当前定位

机场客流层不应该只是把区域客流按比例分给单个机场。

更合适的第一版对象是：

```text
城市 / 都市圈机场系统
```

一个城市机场系统可以包含单机场、双机场或多机场。双机场和多机场暂时不需要被建成复杂调度网络，而是表达这个城市或都市圈的机场供给结构、容量瓶颈和扩建路径。

推荐链条：

```text
Global macro
  -> Regional macro
  -> Regional reconciliation
  -> Regional aviation demand
  -> Regional air capacity / supply fulfillment
  -> City airport market
  -> Airport commercial business
```

## 两道瓶颈

航空客流进入机场前有两道闸。

第一道是航司供给：

```text
潜在出行需求
  -> 航司是否提供足够航班、座位和航线
  -> regional_air_capacity_supply
```

它回答：

```text
想飞的人里，有多少能被航司运力服务？
```

第二道是机场能力：

```text
航司可服务客流
  -> 城市机场系统是否有足够航站楼、跑道、时刻、安检、地服和地面交通能力
  -> city_airport_market
```

它回答：

```text
航司能承接的需求里，有多少能被这个城市机场系统吞吐？
```

这两道瓶颈不能混成一个变量。航司有座位但城市机场拥堵，客流仍会被机场侧压住；机场有大量新容量但航司供给不足，也不会凭空产生实际吞吐。

## 为什么按城市经营

机场游戏的经营主体更接近城市机场市场，而不是抽象区域。

原因：

```text
1. 机场扩建、航站楼、新机场和地面交通规划通常围绕城市或都市圈。
2. 双机场、多机场主要表达本地客流、国际门户、中转和容量分工。
3. 玩家真正决策的是某个城市机场系统是否扩建、何时扩建、扩多少。
4. 区域航空需求给增长背景，城市层负责把它转成本地机场吞吐和瓶颈。
```

第一版可以把城市机场系统作为一个合并对象。例如：

```text
beijing_tianjin_airport_system
shanghai_yangtze_delta_gateway
pearl_river_delta_airport_system
chengdu_chongqing_airport_system
new_york_metro_airport_system
london_airport_system
paris_airport_system
dubai_doha_gulf_hub
singapore_bangkok_southeast_asia_gateway
```

后续如果需要，再把城市系统内部拆成单机场。

## 输入

### 1. 区域航空需求

区域航空需求提供城市需求增长背景：

```text
regional_air_demand_index
regional_air_demand_growth_pct
business_travel_demand_index
leisure_travel_demand_index
vfr_travel_demand_index
long_haul_demand_index
transfer_demand_index
premium_passenger_share_pct
airfare_price_sensitivity_index
aviation_demand_regime
```

城市层不应该要求具体数值与区域总量完全对账。城市需求可以跟随区域增长态势，但由城市自身参数决定放大或收缩。

### 2. 区域航空供给/满足率

区域航空供给层提供航司侧约束：

```text
served_passenger_demand_index
capacity_fulfillment_pct
capacity_fare_pressure_index
business_served_index
leisure_served_index
vfr_served_index
long_haul_served_index
transfer_served_index
supply_regime
```

城市机场市场应优先读取 `served_passenger_demand_index`，而不是直接读取潜在需求。这样城市层拿到的是航司已经能服务的客流池。

### 3. 城市机场系统静态参数

每个城市机场系统需要有本地结构参数：

```text
city_airport_market_id
city_airport_market_name
region_id
base_passengers_million
airport_facility_slot_profile_id
airport_count
default_design_capacity_million
default_max_capacity_million
domestic_capture_weight
international_gateway_weight
transfer_hub_weight
business_market_weight
leisure_market_weight
vfr_market_weight
premium_market_weight
catchment_income_index
local_population_growth_bias
tourism_destination_bias
airport_capacity_flexibility
slot_constraint_base
terminal_constraint_base
ground_access_quality_index
airport_cost_base_index
```

## 设施槽位制

机场能力不应该像需求一样连续平滑增长。v0.2 采用设施槽位制，而不是复杂的扩建项目表。

中国大陆区域先统一使用槽位数量模板。玩家新建标准机场时默认使用 5 槽位，也就是 1 个主槽位、1 个次槽位和 3 个辅助槽位；3 槽位和 4 槽位主要用于既有受限机场或特殊城市机场。

后续扩建不是直接给机场加一个抽象容量，而是在空槽位里选择不同规格的航站楼、卫星厅或扩建区。

槽位里的设施有两个容量值：

```text
design_capacity_million
  设计客流。低于这个值时，机场处于舒适或正常经营状态。

max_capacity_million
  实际上限。超过设计客流但不超过上限时，机场仍能运行，但拥挤、成本、服务质量和商业效率会恶化。
```

标准设施规格先使用五档：

| 规格 | 中文名 | design_capacity_million | max_capacity_million | 用途 |
|---|---|---:|---:|---|
| small | 小型 | 8 | 12 | 小航站楼、小卫星厅、旧楼改造 |
| medium | 中型 | 16 | 24 | 普通辅助航站楼 |
| large | 大型 | 32 | 45 | 大型辅助航站楼或主力扩建区 |
| extra_large | 超大型 | 50 | 65 | T3 级主航站楼 |
| giant | 巨型 | 72 | 90 | 超级新机场一期或巨型主楼 |

槽位可选规格由槽位等级限制：

| 槽位等级 | 可选规格 |
|---|---|
| main_slot | small / medium / large / extra_large / giant |
| secondary_slot | small / medium / large / extra_large |
| auxiliary_slot | small / medium / large |

中国大陆槽位数量模板：

| 槽位数量 | 角色结构 | 用途 |
|---:|---|---|
| 3 | auxiliary_slot / auxiliary_slot / auxiliary_slot | 既有受限机场、特殊城市机场 |
| 4 | secondary_slot / auxiliary_slot / auxiliary_slot / auxiliary_slot | 非标准中型机场或受限扩建机场 |
| 5 | main_slot / secondary_slot / auxiliary_slot / auxiliary_slot / auxiliary_slot | 标准大型机场、新建机场 |

机场容量计算：

```text
airport_design_capacity_million =
  sum(active_slot.design_capacity_million)

airport_max_capacity_million =
  sum(active_slot.max_capacity_million)

city_airport_design_capacity_million =
  sum(airport_design_capacity_million)

city_airport_max_capacity_million =
  sum(airport_max_capacity_million)
```

服务状态：

```text
served <= design_capacity
  normal_operation

design_capacity < served <= max_capacity
  crowded_operation

served > max_capacity
  unmet_demand
```

### 北京首都机场槽位样板

首都机场默认设计为 5 个槽位。首都和大兴使用同一套槽位等级规则。

文档和配置保留内部 `slot_id`，玩家界面优先显示“主槽位 / 次槽位 / 辅助槽位N”。

| 内部 slot_id | 玩家显示槽位 | 槽位等级 | 默认设施 | 默认规格 | 可选规格 |
|---|---|---|---|---|---|
| PEK_SLOT_1 | 主槽位 | main_slot | 首都T3航站楼 | extra_large | small / medium / large / extra_large / giant |
| PEK_SLOT_2 | 次槽位 | secondary_slot | 首都T2航站楼 | large | small / medium / large / extra_large |
| PEK_SLOT_3 | 辅助槽位1 | auxiliary_slot | 玩家扩建槽位 | empty | small / medium / large |
| PEK_SLOT_4 | 辅助槽位2 | auxiliary_slot | 玩家扩建槽位 | empty | small / medium / large |
| PEK_SLOT_5 | 辅助槽位3 | auxiliary_slot | 玩家扩建槽位 | empty | small / medium / large |

首都机场默认容量：

```text
PEK_SLOT_1 主槽位 extra_large = 50 / 65
PEK_SLOT_2 次槽位 large       = 32 / 45

PEK default design capacity = 82m
PEK default max capacity    = 110m
```

### 北京大兴机场槽位样板

大兴机场也默认设计为 5 个槽位。

| 内部 slot_id | 玩家显示槽位 | 槽位等级 | 默认设施 | 默认规格 | 可选规格 |
|---|---|---|---|---|---|
| PKX_SLOT_1 | 主槽位 | main_slot | 大兴T1航站楼 | giant | small / medium / large / extra_large / giant |
| PKX_SLOT_2 | 次槽位 | secondary_slot | 大兴T2航站楼 | empty | small / medium / large / extra_large |
| PKX_SLOT_3 | 辅助槽位1 | auxiliary_slot | 大兴玩家扩建槽位 1 | empty | small / medium / large |
| PKX_SLOT_4 | 辅助槽位2 | auxiliary_slot | 大兴玩家扩建槽位 2 | empty | small / medium / large |
| PKX_SLOT_5 | 辅助槽位3 | auxiliary_slot | 大兴玩家扩建槽位 3 | empty | small / medium / large |

大兴机场默认容量：

```text
PKX_SLOT_1 主槽位 giant = 72 / 90

PKX default design capacity = 72m
PKX default max capacity    = 90m
```

北京双机场默认容量：

```text
PEK default design capacity = 82m
PEK default max capacity    = 110m
PKX default design capacity = 72m
PKX default max capacity    = 90m

Beijing default design capacity = 154m
Beijing default max capacity    = 200m
```

北京双机场不设置固定中期扩展容量。默认开局只表达首都T3航站楼、首都T2航站楼与大兴T1航站楼的基础承载力；后续扩建由玩家在空槽位里自由选择规格，系统按已启用槽位动态求和。

```text
city_airport_design_capacity_million =
  sum(active_slot.design_capacity_million)

city_airport_max_capacity_million =
  sum(active_slot.max_capacity_million)
```

单机场拉满容量不作为固定扩建档写入标准文档。它由主槽位、次槽位和辅助槽位的实际选择动态计算；玩家如果愿意承担拥挤、成本和空间约束，可以把同一机场推到远高于默认容量的区间。

### 城市配置重点

城市机场市场层的核心不是复刻每条航班，而是把一个城市机场系统配置成可以被 seed 和历史岔路驱动的经营对象。

一个正式城市配置至少应包含：

```text
城市算出的客流曲线
  包含 business / leisure / vfr / long_haul / transfer 五个分项控制点。

机场清单
  已有机场使用现实名称；新增机场只在有现实规划、迁建项目或明确协同机场时配置。没有明确锚点时不开放玩家自由命名新机场。

机场槽位结构
  每座机场有几个槽位，哪个是主槽位、次槽位、辅助槽位。

槽位规格限制
  每个槽位允许 small / medium / large / extra_large / giant 中的哪些等级。

初始设施配置
  当前已开放槽位使用什么规格，设计容量和实际上限是多少。

扩建空间配置
  玩家未来可以追加哪些槽位、每个槽位允许哪些规格；中间容量由玩家选择动态形成，不预设固定扩建档位。
```

标准配置文件先拆成两类：

```text
airport/config/facility_size_catalogs/standard_terminal_sizes_v1.json
  全局设施规格和槽位等级规则；城市层运行时按 `facility_size_catalog` 读取它来计算容量和校验槽位规格。

airport/config/city_airport_markets/<region_id>/<city_airport_market_id>.json
  单个城市机场系统的需求曲线、航司供给、机场名单、槽位配置和扩建空间规则。
```

北京样板把这些内容捆绑在同一个城市配置里：需求曲线由区域航空层与北京本地参数生成，槽位配置决定首都/大兴的吞吐上限，长期需求目标抬到 3 亿多到接近 4 亿，用于给双 5 槽位机场系统留下扩建压力。

v0.13 起，城市配置可以选择性加入 `demand_model.seed_potential_model`。它不是新的宏观层，而是城市潜在客流层里的轻量 seed 模板：同一个城市在不同 seed 下可以有不同长期航空体量势能，效果逐年释放，并通过区域航空需求、区域 GDP、信心、压力和票价环境做相关性约束。当前北京 v4 启用核心门户窄模板，青岛 v2 启用沿海门户挑战者宽模板，成都 v2 / 重庆 v2 启用成渝双城门户中宽模板，西安 v2 / 郑州 v2 / 武汉 v2 启用内陆枢纽竞争者中宽模板；上海 v2、杭州 v2、南京 v3、合肥 v2、宁波 v2、无锡-苏南 v2、温州 v2 启用长三角主竞争带 seed 势能模板；广州 v2、深圳 v3、珠海 v2、厦门 v2、福州 v2、泉州-晋江 v2、揭阳-潮汕 v2 启用华南沿海竞争带 seed 势能模板；天津 v2、石家庄 v2、济南 v2、烟台 v2、沈阳 v2、大连 v2 启用环渤海/北方沿海竞争带 seed 势能模板；昆明 v2、贵阳 v2、南宁 v2、桂林 v2、丽江 v2、西双版纳 v2、海口 v2、三亚 v2 启用西南山地和旅游目的地 seed 势能模板；乌鲁木齐 v2、喀什 v2、兰州 v2、呼和浩特 v2、银川 v2、西宁 v2、拉萨 v2 启用西北边疆和高原远程门户 seed 势能模板；长沙 v2、南昌 v2、太原 v2、哈尔滨 v2、长春 v2 启用收尾补全模板。至此中国大陆 47 个城市机场市场全部启用 seed 势能模板。

seed 城市势能的玩家可见解释不应继续塞进城市真实客流层。v0.14 之后应新增独立的城市潜在客流预测系统，把隐藏真实潜在客流曲线降质为玩家可见报告。预测系统可以设置初级、中级、高级和神级预测：普通等级输出区间、趋势、可信度和上行/下行标签，质量分只在 0-70 内插值；神级预测固定为 100 分，是 `future_peek_mode = true` 的未来透视 / 开挂模式，作为调试、沙盒和玩家主动开挂用途，允许接近或显示隐藏真实曲线。详细计划见：

```text
airport/docs/airport_operations/City_Airport_Potential_Passenger_Forecast_System_Plan.md
```

上海样板使用同一套结构：浦东作为 5 槽位国际门户，虹桥作为 3 槽位特殊受限高铁/商务门户。虹桥 3 个槽位都按辅助槽位处理；未来供给选项保留“南通新机场（南通市通州区二甲镇）”，并按新建标准机场使用 5 槽位。上海不设置固定中期扩建档，扩建容量同样由玩家选择槽位规格后动态形成。

广州、成都、重庆、杭州、南京、深圳、西安、武汉、昆明、郑州、厦门、长沙、青岛、天津、济南、福州、沈阳、大连、石家庄、哈尔滨、长春、太原、合肥、南昌、宁波、温州、贵阳、南宁、海口、三亚、乌鲁木齐、兰州、呼和浩特、银川、西宁、拉萨、珠海、泉州/晋江、烟台、无锡/苏州、潮汕、丽江、西双版纳、桂林、喀什样板也使用同一套规则。前两批核心城市以 5 槽位为主；中后批按城市规模和客流潜力分档。石家庄、长春、南昌、宁波、温州、三亚、银川、西宁、拉萨、珠海、泉州/晋江、烟台、无锡/苏州、潮汕、丽江、西双版纳、桂林、喀什使用 3 槽位；哈尔滨、太原、合肥、贵阳、南宁、海口、兰州使用 4 槽位；乌鲁木齐作为西北远程/战略门户保留 5 槽位；呼和浩特直接按盛乐新机场 5 槽位处理。它们都只写初始配置，不写固定中期扩建档。

`macro_run_orchestrator_sim.py` 现在会在区域航空需求和区域航空供给生成后，自动扫描城市机场 JSON 配置，并为每个有上游区域数据的城市机场系统生成：

```text
airport/output/macro_runs/<run_id>/<variant>/city_airport_market_demand/<region_id>/<city_airport_market_id>_city_airport_demand_seed_sweep.csv
airport/output/macro_runs/<run_id>/<variant>/city_airport_market_demand/<region_id>/<city_airport_market_id>_city_airport_demand_summary.json
airport/output/macro_runs/<run_id>/<variant>/city_airport_market_demand/<region_id>/<city_airport_market_id>_city_airport_demand_viewer_data.js
```

## 核心机制

### 1. 城市潜在客流

城市潜在客流可以从区域航空需求和城市结构共同生成：

```text
city_air_demand_growth =
  regional_air_demand_growth
  * city_growth_beta
  + local_population_bias
  + tourism_destination_bias
  + transfer_hub_signal
  + business_gateway_signal
```

城市潜在客流不需要与区域总量完全相加对账。它是游戏经营对象的本地需求指数。

### 2. 航司侧可服务客流

城市机场系统不能承接超过航司侧可服务的需求：

```text
airline_served_ceiling =
  city_potential_demand
  * regional_capacity_fulfillment_pct
  * city_airline_service_capture
```

如果区域航司供给紧张，城市机场即使容量充足，也会被航司侧压住。v0.17 起，城市潜在客流是长期慢变量，航司供给是更快的周期变量：它会以潜在客流对应的座位需求作为规划锚点，并随区域运力上行，但会叠加更强的航司投放周期、seed 供给冲击、宏观/利润/机队约束和上一年供给惯性。

```text
city_airline_supply_target_index
  = trend_index
  + demand_pull_from_potential_anchor
  + airline appetite/confidence adjustment
  - airline constraint drag
  + seed cycle impulse
  + seed shock impulse
  + branch/event impulse

city_airline_supply_index
  = previous_index
  + (city_airline_supply_target_index - previous_index)
    * adjustment_speed
```

供给指数上限应随潜在客流锚点动态上移，避免远期航司供给被固定上限压平成一条横线。缺口可以存在，但应主要来自航司周期、冲击、约束和滞后，而不是硬编码天花板。

v0.18 起，城市航司供给增加五类客流分项。总供给先由上面的供给指数决定，分项供给只做结构分配：

```text
component_airline_supply_weight
  = component_potential_passengers
    * component_supply_preference_multiplier

component_airline_supply_passengers
  = city_airline_supply_passengers_million
    * component_airline_supply_weight / sum(component_airline_supply_weight)
```

分项偏好主要读取航司信心、航线投放、机队扩张、利润压力、机场槽位约束、票价、汇率、宏观压力、区域开放度和投资周期。这样周期来源可以落到“哪类潜在需求冷/热”和“哪类航司座位供给不足/过剩”，而不是只剩一个总量缺口。

运营面板的客流容量图应把潜在客流、实际承接客流、航司供给、设计容量和最大容量放在同一视图里，明确区分“航司不给座位”和“机场自己装不下”。

### 3. 机场侧吞吐能力

机场年度能力由已开放的设施槽位共同决定：

```text
city_airport_design_capacity_million =
  sum(active_airport_slots.design_capacity_million)

city_airport_max_capacity_million =
  sum(active_airport_slots.max_capacity_million)
```

机场侧实际吞吐：

```text
airport_capacity_allocation_ratio =
  min(1, city_airport_max_capacity_million / city_airline_serviceable_passengers_million)

airport_allocated_airline_supply_million =
  city_airline_serviceable_passengers_million
  * airport_capacity_allocation_ratio

city_served_passengers_million =
  min(
    city_potential_passengers_million,
    airport_allocated_airline_supply_million
  )
```

设计容量和实际可运行上限之间形成拥挤区间。机场不需要改造就能超过设计容量，但服务质量、拥挤成本和商业效率会受到惩罚。

如果机场最大容量低于航司供给，不再增加一层复杂分配。第一版直接按等比例压缩：

```text
served_business =
  potential_business * city_served_passengers_million / city_potential_passengers_million

served_leisure =
  potential_leisure * city_served_passengers_million / city_potential_passengers_million

served_vfr =
  potential_vfr * city_served_passengers_million / city_potential_passengers_million

served_long_haul =
  potential_long_haul * city_served_passengers_million / city_potential_passengers_million

served_transfer =
  potential_transfer * city_served_passengers_million / city_potential_passengers_million
```

这意味着机场容量只负责总吞吐上限，不在第一版里做商务优先、休闲挤出或中转保护。

### 4. 不足

当城市机场系统吞吐不足：

```text
city_airport_utilization_pct > 95
```

会出现：

```text
city_unmet_passengers_million up
slot_pressure_index up
terminal_pressure_index up
service_quality_index down
airport_delay_pressure_index up
airport_congestion_cost_index up
```

旅客结构上，低收益和高价格敏感客流更容易被挤出：

```text
leisure
  -> transfer
  -> VFR
  -> long_haul
  -> business / premium
```

但中转枢纽城市可以给 transfer 更高保留权重。

### 5. 过剩

当机场扩建过快：

```text
city_airport_utilization_pct < 65
```

会出现：

```text
overcapacity_pressure_index up
unit_operating_cost_index up
capex_burden_index up
airline_incentive_cost_index up
commercial_area_underuse_index up
```

过剩不意味着客流自动增长。机场需要承担固定成本、折旧和融资压力，同时可能通过降费、补贴或营销吸引航司。

## 成本简化

第一版不做复杂航班调度。机场经营可以简化成客流量与对应成本。

建议保留这些成本变量：

```text
airport_fixed_cost_index
airport_variable_cost_index
airport_congestion_cost_index
airport_capex_burden_index
airport_debt_service_pressure_index
airport_maintenance_cost_index
airline_incentive_cost_index
```

成本机制：

```text
fixed_cost
  随机场容量和项目投放上升，不随客流快速下降。

variable_cost
  随实际旅客吞吐上升。

congestion_cost
  在利用率过高时非线性上升。

overcapacity_cost
  在利用率过低时上升，代表闲置航站楼、折旧和商业面积利用不足。
```

这样第一版就能形成经营权衡，而不用模拟每条跑道和每个时刻。

## 输出字段建议

第一版建议输出：

```text
city_airport_market_id
city_airport_market_name
region_id
year
seed

city_air_demand_index
city_air_demand_growth_pct
city_potential_passengers_million
city_airline_serviceable_passengers_million
city_airport_design_capacity_million
city_airport_max_capacity_million
airport_capacity_allocation_ratio_pct
airport_capacity_limited_airline_supply_million
city_served_passengers_million
city_unmet_passengers_million

city_airport_design_utilization_pct
city_airport_max_utilization_pct
city_airport_fulfillment_pct
airport_crowding_index
slot_pressure_index
terminal_pressure_index
ground_access_pressure_index
service_quality_index

domestic_passenger_index
international_passenger_index
transfer_passenger_index
business_passenger_index
leisure_passenger_index
vfr_passenger_index
premium_passenger_index
business_served_passengers_million
leisure_served_passengers_million
vfr_served_passengers_million
long_haul_served_passengers_million
transfer_served_passengers_million

airport_fixed_cost_index
airport_variable_cost_index
airport_congestion_cost_index
airport_capex_burden_index
airport_debt_service_pressure_index
airport_overcapacity_pressure_index

airport_market_regime
active_facility_slots
new_facility_slots_opened
```

## 状态分类

`airport_market_regime` 可以先使用：

```text
balanced_airport_market
airport_capacity_shortage
severe_airport_congestion
airport_overcapacity
airport_expansion_absorption
construction_disruption
airline_supply_constrained
macro_demand_shock
```

含义：

```text
airport_capacity_shortage
  机场能力是主要瓶颈。

airline_supply_constrained
  航司侧供给不足是主要瓶颈，机场有余量也吃不到客流。

airport_overcapacity
  机场容量投放超过需求和航司供给。

airport_expansion_absorption
  新容量刚开放，利用率低但仍处于爬坡期。
```

## v0.1 实现范围

建议第一版只做 8-12 个城市机场系统，不要一次铺全球所有机场。

候选样板：

```text
beijing_tianjin_airport_system
shanghai_yangtze_delta_gateway
pearl_river_delta_airport_system
chengdu_chongqing_airport_system
new_york_metro_airport_system
london_airport_system
paris_airport_system
dubai_doha_gulf_hub
singapore_bangkok_gateway
tokyo_seoul_gateway
delhi_mumbai_india_gateway
istanbul_eurasia_gateway
```

第一版脚本建议：

```text
airport/airport_layers/city_airport_market_sim.py
```

第一版先输出 CSV/JSON/JS，不急着做完整界面。

## 暂不做

第一版暂不做：

```text
逐航班排班
单航司市场份额
具体机型和机队
每条航线 slot
机场内部安检/行李/登机口逐项调度
单机场之间的实时流量再分配
```

这些可以等城市机场市场层稳定后，再拆成更细的机场经营或航线网络层。

## 后续连接

城市机场市场层稳定后，下一层可以做机场商业业务：

```text
city_served_passengers_million
passenger_mix
service_quality_index
airport_congestion_cost_index
airport_overcapacity_pressure_index
  -> duty free
  -> food and beverage
  -> general retail
  -> parking and ground transport
  -> lounge and premium services
  -> advertising
```

商业层应该读取实际吞吐和旅客结构，而不是潜在需求。这样商业收入会自然受到航司供给、机场容量、拥堵和过剩的共同影响。
