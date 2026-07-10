# Quarterly Operations Config Template

城市机场季度经营层采用“变量骨架 + 城市实参”的结构。季度经营层承接上游城市机场客流层已经生成的年度潜在客流、航司供给、五类客群分项、消费倾向、seed 和历史岔路结果；它保留年度需求主轴，但会根据当季真实容量、翻新/重建/新建状态和容量实现率重新裁剪实际承接客流，并计算经营收入、经营成本、商业收入和经营结果。

折旧暂不放入这套经营参数配置。北京页面里的资产折旧仍是独立样例口径。

## 文件结构

```text
airport/config/city_airport_operations/templates/city_airport_quarterly_operations_parameter_schema_v1.json
airport/config/city_airport_operations/reference_defaults/china_mainland_quarterly_operations_reference_defaults_v1.json
airport/config/city_airport_operations/beijing_airport_system_quarterly_operations_v1.json
```

`city_airport_quarterly_operations_parameter_schema_v1.json` 只说明变量、单位、形状和调参意图，不给运行值，也不被模拟器读取。

`china_mainland_quarterly_operations_reference_defaults_v1.json` 是中国大陆参考值库，只供抄写和校准参考，不会自动继承。

`beijing_airport_system_quarterly_operations_v1.json` 是北京实际运行配置，必须完整填写北京自己的参数。

## 北京当前实参

北京配置当前包含：

| 参数 | 当前含义 |
|---|---|
| `quarter_component_weights` | 五类客群的季度拆分权重 |
| `facility_fixed_operating_cost_million_cny_per_year` | 启用槽位按规格产生的年度固定经营成本 |
| `slot_fixed_operating_cost_model` | 槽位固定经营成本的建筑年龄、季度季节性、宏观成本和城市复杂度修正 |
| `aeronautical_revenue` | 航运侧旅客收入基准和客群修正 |
| `passenger_variable_cost` | 旅客接待变动成本和复杂度修正 |
| `congestion_cost` | 超过设计容量或最大容量后的拥挤成本 |
| `commercial.food_retail` | 餐饮普通零售自营收入、固定成本和客流服务成本 |
| `commercial.duty_free` | 免税加权旅客、销售基准和合同收入 |
| `commercial.luxury` | 奢侈品/精品加权旅客、销售基准和合同收入 |

槽位固定经营成本公式：

```text
quarter_slot_fixed_cost =
  size_base_annual_cost
  * building_age_multiplier
  * macro_cost_pressure_multiplier
  * city_complexity_multiplier
  * quarter_heating_cooling_multiplier
  / 4
```

这不是资产折旧，而是启用航站楼/槽位后每期必须承担的基础经营负担。北京当前的建筑年龄曲线设定为：新楼低于基准，中年快速上升，老楼高位趋缓；Q1/Q3 因暖气/空调负担略高，Q2/Q4 略低。宏观成本压力目前温和参考宏观压力、能源压力、汇率压力和消费者信心字段；如果某字段上游暂未提供，则使用中性值。

## 季度承接口径

v0.19 起，季度经营层不再机械照搬上游年度承接客流。每个季度先按季节性拆出分项潜在客流和分项航司供给：

```text
component_quarter_potential_passengers =
  annual_component_potential_passengers
  * component_quarter_weight

component_quarter_airline_supply_passengers =
  annual_component_airline_supply_passengers
  * component_quarter_weight

quarter_city_potential_passengers =
  sum(component_quarter_potential_passengers)

quarter_airline_supply_passengers =
  sum(component_quarter_airline_supply_passengers)

quarter_serviceable_demand =
  min(quarter_city_potential_passengers, quarter_airline_supply_passengers)
```

如果当季机场容量被撑爆，则按当季最大容量和容量实现率重新裁剪：

```text
quarter_served_passengers =
  min(
    quarter_serviceable_demand,
    quarter_max_capacity * quarter_capacity_realization_factor
  )
```

`quarter_capacity_realization_factor` 在未撑爆时为 100%；接近或超过最大容量时通常落在约 97%-99% 附近，重建/翻新施工期会更低一点。这样重建期不会出现长期 130% 以上的机械超载，完工后也能按新的季度容量重新承接客流。

分项承接暂时不再增加独立复杂周期，而是用当季总承接率等比例压低分项潜在客流：

```text
component_quarter_served_passengers =
  component_quarter_potential_passengers
  * quarter_served_passengers / quarter_city_potential_passengers
```

## 输出与界面

修改北京经营配置后，需要重新运行：

```text
py -3 .\airport\macro_layers\city_airport_quarterly_operations_layer_sim.py
```

脚本会更新：

```text
airport/output/city_airport_quarterly_operations/china_mainland/beijing_airport_system_quarterly_operations_seed_sweep.csv
airport/output/city_airport_quarterly_operations/china_mainland/beijing_airport_system_quarterly_operations_summary.json
airport/output/city_airport_quarterly_operations/china_mainland/beijing_airport_system_quarterly_operations_viewer_data.js
```

北京运营界面读取 `beijing_airport_system_quarterly_operations_viewer_data.js`，因此重新运行后刷新页面即可看到经营损益、航运侧、商业侧和季度口径变化。
