# Airport Operations Docs

机场经营层从城市/都市圈机场系统开始，而不是直接把区域客流分给单个机场。

## 入口

1. `City_Airport_Market_Layer_Plan.md`
2. `City_Airport_Market_List_v0.1.md`
3. `City_Airport_Potential_Passenger_Forecast_System_Plan.md`（有效客流预测，文件名暂未迁移）
4. `City_Airport_Quarterly_Demand_Distribution_Draft.md`
5. `Quarterly_Operations_Config_Template.md`
6. `../../web/pages/beijing_airport_operations_viewer.html`

## 当前定位

这一层承接区域航空需求、区域航司供给和城市机场 seed 势能，生成城市潜在客流、航司供给、市场有效客流和机场真实承接客流；再叠加设施槽位、设计/实际上限容量、拥堵、过剩、商业收入、税务、财务和估值压力。

## 后续文档建议

- Airport facility slot model
- Airport commercial business plan
- Airport cost model

## 代码位置

计划位置：

```text
airport_layers/city_airport_market_sim.py
```

已落地的北京有效客流预测、季度经营、财务和估值试算：

```text
macro_layers/city_airport_potential_passenger_forecast_layer_sim.py
config/city_airport_potential_passenger_forecast/beijing_airport_system_potential_passenger_forecast_v1.json
macro_layers/city_airport_quarterly_operations_layer_sim.py
config/city_airport_operations/templates/city_airport_quarterly_operations_parameter_schema_v1.json
config/city_airport_operations/reference_defaults/china_mainland_quarterly_operations_reference_defaults_v1.json
config/city_airport_operations/beijing_airport_system_quarterly_operations_v1.json
macro_layers/city_airport_financial_state_layer_sim.py
config/city_airport_finance/beijing_airport_group_financial_state_v1.json
macro_layers/city_airport_valuation_forecast_layer_sim.py
config/city_airport_valuation/beijing_airport_group_valuation_forecast_v1.json
web/pages/beijing_airport_operations_viewer.html
```
