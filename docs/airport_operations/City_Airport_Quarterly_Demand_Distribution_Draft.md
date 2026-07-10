# City Airport Quarterly Demand Distribution Draft

本文记录城市机场客流层如何从年度客流拆到季度。第一版不做单机场拆分；v0.19 起，季度层会把年度潜在分项和航司供给分项拆到季度，再根据当季真实容量和容量实现率重新裁剪实际承接客流。

## 定位

季度拆分的单位是：

```text
city_airport_market_id
```

也就是一个城市或都市圈机场系统整体。例如：

```text
beijing_airport_system = 首都 + 大兴整体
shanghai_airport_system = 浦东 + 虹桥整体
chengdu_airport_system = 天府 + 双流整体
```

第一版不把北京客流继续拆到首都机场和大兴机场。单机场分配应放在机场经营账本或机场资产层里，等城市机场系统的季度客流稳定后再做。

## 输入

季度拆分读取城市机场市场层的年度输出：

```text
city_served_passengers_million
business_served_passengers_million
leisure_served_passengers_million
vfr_served_passengers_million
long_haul_served_passengers_million
transfer_served_passengers_million
city_unmet_passengers_million
city_binding_bottleneck
city_airport_design_capacity_million
city_airport_max_capacity_million
```

季度运营账本应该优先使用当季重新裁剪后的 `quarter_served_passengers_million`，而不是直接照搬年度 `served` 客流。潜在客流和未满足客流用于判断扩建压力、航司供给缺口和机场容量缺口。

## 基本公式

对每个年度、每个城市机场系统：

```text
quarter_component_potential_passengers =
  annual_component_potential_passengers
  * quarter_component_weight

quarter_component_airline_supply_passengers =
  annual_component_airline_supply_passengers
  * quarter_component_weight

quarter_city_potential_passengers =
  sum(quarter_component_potential_passengers)

quarter_airline_supply_passengers =
  sum(quarter_component_airline_supply_passengers)

quarter_serviceable_demand =
  min(quarter_city_potential_passengers, quarter_airline_supply_passengers)

quarter_served_passengers =
  min(
    quarter_serviceable_demand,
    quarter_max_capacity * quarter_capacity_realization_factor
  )

quarter_component_served_passengers =
  quarter_component_potential_passengers
  * quarter_served_passengers / quarter_city_potential_passengers
```

四个季度的同一客群权重必须合计为 100%：

```text
Q1 + Q2 + Q3 + Q4 = 1.0
```

v0.19 之后，季度权重仍提供季节性和客群结构，但拆分对象改为潜在分项和航司供给分项。季度客流加总不必严格回到上游年度实际服务客流，原因是季度经营层会再叠加当季真实容量、翻新/重建/新建状态和容量实现率，得到最终经营用承接客流。

## 权重草案

第一版使用固定权重。后续可以让权重受区域、城市类型、节假日、旅游暴露度和宏观事件影响。

| 客群 | Q1 | Q2 | Q3 | Q4 | 说明 |
|---|---:|---:|---:|---:|---|
| business | 23.5% | 25.5% | 24.5% | 26.5% | Q4 商务略强，Q1 受春节工作日影响略弱 |
| leisure | 27.0% | 22.0% | 30.0% | 21.0% | 春节和暑运偏强 |
| vfr | 30.0% | 21.0% | 27.0% | 22.0% | 春运探亲最强，暑期次强 |
| long_haul | 24.5% | 24.0% | 27.5% | 24.0% | 暑期远程和国际需求略强 |
| transfer | 24.5% | 25.0% | 26.5% | 24.0% | 暑运带动中转略强 |

## 北京样例

以下样例使用 `beijing_airport_system` 的年度城市机场层输出。注意，这里是北京机场系统整体，不拆首都和大兴。

年度实际服务客流：

| 年份 | 年度实际服务客流 | 主要瓶颈 |
|---:|---:|---|
| 2025 | 1.178 亿 | demand_limited |
| 2035 | 1.158 亿 | airline_bottleneck |
| 2050 | 1.245 亿 | airline_bottleneck |
| 2085 | 2.000 亿 | airport_bottleneck |

季度拆分结果：

| 年份 | Q1 | Q2 | Q3 | Q4 |
|---:|---:|---:|---:|---:|
| 2025 | 3044 万 | 2757 万 | 3221 万 | 2757 万 |
| 2035 | 2979 万 | 2724 万 | 3142 万 | 2734 万 |
| 2050 | 3185 万 | 2946 万 | 3346 万 | 2970 万 |
| 2085 | 5154 万 | 4696 万 | 5433 万 | 4717 万 |

2035 年低于 2025 年不是季节模型造成的，而是当前 seed 下北京城市机场系统在年度层被航司供给约束。

## 输出字段建议

季度层可以输出：

```text
city_airport_market_id
city_name
region_id
year
quarter
seed

quarter_served_passengers_million
quarter_city_potential_passengers_million
quarter_airline_supply_passengers_million
business_quarter_potential_passengers_million
leisure_quarter_potential_passengers_million
vfr_quarter_potential_passengers_million
long_haul_quarter_potential_passengers_million
transfer_quarter_potential_passengers_million
business_quarter_airline_supply_passengers_million
leisure_quarter_airline_supply_passengers_million
vfr_quarter_airline_supply_passengers_million
long_haul_quarter_airline_supply_passengers_million
transfer_quarter_airline_supply_passengers_million
business_quarter_served_passengers_million
leisure_quarter_served_passengers_million
vfr_quarter_served_passengers_million
long_haul_quarter_served_passengers_million
transfer_quarter_served_passengers_million

annual_served_passengers_million
quarter_share_of_annual_served_pct
city_airport_design_capacity_million
city_airport_max_capacity_million
quarter_design_capacity_million
quarter_max_capacity_million
quarter_design_utilization_pct
quarter_max_utilization_pct
quarter_crowding_index

annual_city_binding_bottleneck
quarter_event_hint
branch_scenario_id
branch_scenario_state
active_facility_slots

quarter_slot_fixed_operating_cost_index
quarter_passenger_variable_cost_index
quarter_congestion_cost_index
aeronautical_revenue_index
food_retail_operation_mode
food_retail_revenue_index
duty_free_revenue_index
luxury_retail_revenue_index
commercial_revenue_index
total_operating_revenue_index
quarter_operating_profit_index

duty_free_contract_type
duty_free_revenue_share_pct
duty_free_minimum_guarantee_ratio_pct
luxury_contract_type
luxury_revenue_share_pct
luxury_minimum_guarantee_ratio_pct
```

季度容量可以先简单按年度容量除以 4：

```text
quarter_design_capacity_million =
  city_airport_design_capacity_million / 4

quarter_max_capacity_million =
  city_airport_max_capacity_million / 4
```

这会让 Q1/Q3 的旺季更容易出现拥挤，而不是被年度均值抹平。

## 季度经营账本口径

季度层后续可以直接承接一个轻量机场经营账本。第一版不需要真实数值，只先明确成本和收入结构。

经营账本仍然以城市机场系统为单位：

```text
city_airport_market_id
```

不拆到单机场，也不拆到航司或航班。

### 1. 槽位固定经营成本

每一个设施槽位只要启用，就产生固定经营成本。这个成本由槽位中的设施规格决定，不直接随当季客流变化。

```text
empty
  不产生固定经营成本

small / medium / large / extra_large / giant
  按规格产生固定经营成本
```

也就是说，玩家启用了更大的航站楼、卫星厅或扩建区，即使客流还没有填满，也需要承担对应的季度固定经营成本。这部分用于表达过度建设、闲置设施、人员与维护基本盘。

结构上可以先写成：

```text
quarter_slot_fixed_operating_cost_index =
  sum(active_slot.fixed_operating_cost_index_by_size) / 4
```

如果后续要让部分成本按季度波动，可以再叠加季节系数；第一版先平均到四个季度即可。

### 2. 客流挂钩收入

季度实际服务客流产生经营收入。第一版可以先按城市机场系统整体计算：

```text
quarter_passenger_revenue_index =
  quarter_served_passengers_million
  * passenger_revenue_per_million_index
  * passenger_mix_revenue_adjustment
```

`passenger_mix_revenue_adjustment` 后续可以由商务、远程、休闲、探亲和中转结构决定：

```text
business / long_haul / premium
  单客收入倾向更高

leisure / vfr
  单客收入倾向更低

transfer
  航空性收入和商业收入之间需要单独校准
```

收入可以先分为：

```text
aeronautical_revenue_index
commercial_revenue_index
total_operating_revenue_index
```

其中商业收入后续再接免税、精品、电子、餐饮和普通零售倾向。

#### 商业收入分层

商业收入第一版拆成三类：

```text
food_retail_revenue_index
duty_free_revenue_index
luxury_retail_revenue_index
```

餐饮零售采用机场自营模式，不设玩家合同操作。它用于表达餐饮、便利、普通零售、伴手礼和一部分电子旅行消费。电子产品暂时不单列，先并入餐饮零售里的高弹性零售部分。

```text
food_retail_revenue_index =
  quarter_served_passengers_million
  * blended_food_retail_propensity_index
  * airport_self_operated_commercial_efficiency
  * crowding_experience_adjustment
```

`blended_food_retail_propensity_index` 可以由以下字段合成：

```text
food_beverage_propensity_index
general_retail_propensity_index
electronics_retail_propensity_index
```

免税和奢侈品 / 精品分开签约，由免税集团或商业运营商承接。玩家不管理具体门店，只在合同期选择合同类型、分成比例和保底比例。

```text
duty_free_sales_index =
  weighted_duty_free_passengers
  * duty_free_propensity_index
  * international_exposure_adjustment
  * operator_commercial_capture_rate

luxury_sales_index =
  weighted_luxury_passengers
  * luxury_retail_propensity_index
  * premium_passenger_propensity_index
  * premium_passenger_share_adjustment
  * operator_commercial_capture_rate
```

免税更依赖长途、中转、休闲和跨境属性；奢侈品更依赖商务、长途、高端客倾向和高端客占比。五种旅客分项仍然有意义，但它们不直接变成店铺，而是决定商业收入弹性。

```text
weighted_duty_free_passengers =
  long_haul_quarter_served_passengers_million * long_haul_duty_free_weight
  + transfer_quarter_served_passengers_million * transfer_duty_free_weight
  + leisure_quarter_served_passengers_million * leisure_duty_free_weight

weighted_luxury_passengers =
  business_quarter_served_passengers_million * business_luxury_weight
  + long_haul_quarter_served_passengers_million * long_haul_luxury_weight
  + transfer_quarter_served_passengers_million * transfer_luxury_weight
```

#### 免税合同

免税合同第一版允许两种类型：

| 合同类型 | 分成范围 | 保底范围 | 说明 |
|---|---:|---:|---|
| `revenue_share` | 20%-42% | 0 | 纯流水分成，上行弹性最大，下行没有保护 |
| `minimum_guarantee_plus_share` | 12%-34% | 基准季度合同收入指数的 40%-120% | 有保底，下行更稳，但分成通常更低 |

```text
if duty_free_contract_type == "revenue_share":
  duty_free_revenue_index =
    duty_free_sales_index
    * duty_free_revenue_share_pct

if duty_free_contract_type == "minimum_guarantee_plus_share":
  duty_free_revenue_index =
    max(
      baseline_duty_free_contract_revenue_index * duty_free_minimum_guarantee_ratio_pct,
      duty_free_sales_index * duty_free_revenue_share_pct
    )
```

免税推荐组合：

| 风格 | 分成 | 保底 |
|---|---:|---:|
| 激进上行 | 38%-42% | 0 |
| 平衡流水 | 28%-34% | 0 |
| 稳健保底 | 18%-26% | 70%-90% |
| 强保底 | 12%-18% | 90%-120% |

#### 奢侈品 / 精品合同

奢侈品 / 精品合同也允许两种类型：

| 合同类型 | 分成范围 | 保底范围 | 说明 |
|---|---:|---:|---|
| `revenue_share` | 12%-30% | 0 | 适合看好商务、高端客和长途客增长的机场 |
| `minimum_guarantee_plus_share` | 8%-24% | 基准季度合同收入指数的 35%-110% | 更稳健，但高景气时弹性较低 |

```text
if luxury_contract_type == "revenue_share":
  luxury_revenue_index =
    luxury_sales_index
    * luxury_revenue_share_pct

if luxury_contract_type == "minimum_guarantee_plus_share":
  luxury_revenue_index =
    max(
      baseline_luxury_contract_revenue_index * luxury_minimum_guarantee_ratio_pct,
      luxury_sales_index * luxury_revenue_share_pct
    )
```

奢侈品推荐组合：

| 风格 | 分成 | 保底 |
|---|---:|---:|
| 激进上行 | 26%-30% | 0 |
| 平衡流水 | 18%-24% | 0 |
| 稳健保底 | 12%-18% | 65%-85% |
| 强保底 | 8%-12% | 85%-110% |

分成和保底都可以在范围内调整，但高分成叠加强保底不应无条件成立。后续可以加入 `commercial_contract_acceptance_score`，由机场规模、国际客强度、高端客强度、运营商品牌匹配、预期增长和需求波动共同决定合同是否能签下。

#### 北京默认商业合同草案

北京机场系统可以作为第一版模板。它的餐饮零售不需要玩家操作，免税和奢侈品采用稳健的保底 + 分成合同：

```text
city_airport_market_id = beijing_airport_system

food_retail_operation_mode = self_operated_auto

duty_free_contract_type = minimum_guarantee_plus_share
duty_free_revenue_share_pct = 24
duty_free_minimum_guarantee_ratio_pct = 80

luxury_contract_type = minimum_guarantee_plus_share
luxury_revenue_share_pct = 16
luxury_minimum_guarantee_ratio_pct = 75
```

这个默认方案不追求最高上行，而是让北京在国际客、商务客和高端客波动时有较稳定的商业收入底盘。玩家如果明确看好长途和高端消费，可以把免税切到较高分成的 `revenue_share`，或者把奢侈品分成提高到平衡流水区间。

2025-2029 开局历史期不让玩家操作合同。北京样板中这段历史合同采用 `pricing_mode = future_sales_average`：系统先按完整经营模型读取历史期实际模拟销售额，再用“平均季度销售额 * 分成比例”反推基准季度合同收入，最后按保底比例计算季度保底。配置中的 `baseline_quarter_contract_revenue_million_cny` 仍保留为兜底值。这个处理相当于开局前合同已经基于当时能预见的历史期销售盘子完成定价，比直接固定一个基准收入更自然。

#### 北京游戏人民币参数 v1

北京可以先使用一套游戏校准人民币参数。这里的金额只服务玩法平衡，不等于现实机场财报。

配置文件：

```text
airport/config/city_airport_operations/beijing_airport_system_quarterly_operations_v1.json
```

核心参数：

| 项目 | 参数 |
|---|---:|
| 航空性收入 | 78 元 / 实际服务旅客，按商务、休闲、探亲、长途和中转结构修正 |
| 旅客变动成本 | 44 元 / 实际服务旅客，按服务复杂度修正 |
| 餐饮零售自营收入 | 54 元 / 实际服务旅客，按餐饮、普通零售和电子消费倾向修正 |
| 餐饮零售自营固定成本 | 按启用槽位规格累加，当前北京初始为 8.4 亿元 / 年 |
| 餐饮零售自营客流服务成本 | 6.5 元 / 实际服务旅客 |
| 拥挤成本 | 满拥挤时 24 元 / 实际服务旅客，超季度极限另加 36 元 / 超额旅客 |
| large 槽位固定成本 | 12.0 亿元 / 年 |
| extra_large 槽位固定成本 | 21.0 亿元 / 年 |
| giant 槽位固定成本 | 30.0 亿元 / 年 |
| 北京初始启用槽位固定成本 | 63.0 亿元 / 年 |
| 免税销售基准 | 430 元 / 加权免税旅客 |
| 免税合同 | 保底 + 分成，分成 24%，季度保底基准 3.6 亿元的 80% |
| 奢侈品销售基准 | 360 元 / 加权精品旅客 |
| 奢侈品合同 | 保底 + 分成，分成 16%，季度保底基准 2.6 亿元的 75% |

2026-07-03 试算输出：

```text
airport/output/city_airport_quarterly_operations/china_mainland/beijing_airport_system_quarterly_operations_seed_sweep.csv
airport/output/city_airport_quarterly_operations/china_mainland/beijing_airport_system_quarterly_operations_summary.json
```

节点年度结果：

| 年份 | 年度实际服务客流 | 经营收入 | 经营成本 | 经营利润 | 利润率 | 主要瓶颈 |
|---:|---:|---:|---:|---:|---:|---|
| 2025 | 1.178 亿 | 177.3 亿元 | 132.6 亿元 | 44.7 亿元 | 25.2% | demand_limited |
| 2035 | 1.158 亿 | 181.7 亿元 | 131.6 亿元 | 50.1 亿元 | 27.6% | airline_bottleneck |
| 2050 | 1.245 亿 | 208.1 亿元 | 136.1 亿元 | 72.0 亿元 | 34.6% | airline_bottleneck |
| 2085 | 2.000 亿 | 441.8 亿元 | 218.2 亿元 | 223.6 亿元 | 50.6% | airport_bottleneck |

这组结果说明：在当前参数下，北京初期仍是盈利机场系统，但餐饮零售自营盘不再是零成本收入；中期即使航司供给限制客流，商业倾向和高端客结构仍能推高利润；远期如果机场容量不扩，实际服务客流被卡在 2 亿，但旺季季度会明显拥挤，商业和航空性收入仍随高端化上升。

商业收入汇总为：

```text
commercial_revenue_index =
  food_retail_revenue_index
  + duty_free_revenue_index
  + luxury_retail_revenue_index

self_operated_food_retail_cost_index =
  self_operated_food_retail_fixed_cost_index
  + quarter_served_passengers_million * self_operated_food_retail_service_cost_per_passenger

commercial_operating_profit_index =
  commercial_revenue_index
  - self_operated_food_retail_cost_index
```

### 3. 客流挂钩变动成本

季度实际服务客流同时产生变动经营成本：

```text
quarter_passenger_variable_cost_index =
  quarter_served_passengers_million
  * passenger_variable_cost_per_million_index
  * service_complexity_adjustment
```

这部分表达安检、行李、保洁、能源、地服、现场秩序和旅客服务等随客流变化的成本。

### 4. 拥挤成本

季度客流超过季度设计容量后，可以出现额外拥挤成本：

```text
if quarter_served_passengers <= quarter_design_capacity:
  quarter_congestion_cost_index = 0

if quarter_design_capacity < quarter_served_passengers <= quarter_max_capacity:
  quarter_congestion_cost_index rises with utilization
```

拥挤成本用于表达服务质量下降、排队、延误、临时人员、地面交通压力和商业效率损失。

### 5. 季度经营利润

第一版总公式可以保持简单：

```text
quarter_operating_profit_index =
  total_operating_revenue_index
  - quarter_slot_fixed_operating_cost_index
  - quarter_passenger_variable_cost_index
  - quarter_congestion_cost_index
  - self_operated_food_retail_cost_index
```

这个公式的重点不是精确财务报表，而是形成经营权衡：

```text
客流增长
  收入增加
  变动成本增加
  高峰季度可能拥挤

提前扩建
  固定成本增加
  拥挤下降
  如果客流不足，会出现闲置压力
```

## 后续扩展

第一版只做固定季节权重。后续可以加入：

```text
tourism_seasonality_bias
business_calendar_bias
spring_festival_shift
summer_peak_strength
weather_disruption_risk
school_holiday_sensitivity
branch_event_quarter_phase
```

不同城市可在 JSON 中覆盖默认权重。例如：

```text
旅游城市
  Q1 / Q3 休闲更强

商务城市
  Q2 / Q4 商务更强

高原或边疆机场
  天气和季节可用性影响更大

南方海岛机场
  冬季和春节休闲权重更高
```

## 暂不做

第一版暂不做：

```text
单机场分配
单航司份额
逐航班排班
具体节假日日期移动
航班时刻和跑道容量
```

这些应放在机场资产层、航司网络层或更细的运营调度层里。
