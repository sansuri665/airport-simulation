# Airport Workspace

这个目录当前承载机场游戏的全球/区域宏观基座、区域航空需求/供给层、中国大陆城市机场市场，以及北京机场经营、财务、税务、估值和有效客流预测样板。主流程已经从“逐层手动运行”整理为一键 macro run。

## 当前主入口

生成随机 seed 的完整 baseline run：

```powershell
py -3 .\macro_layers\macro_run_orchestrator_sim.py --random-seed
```

生成固定 seed，并额外生成一条历史分岔发生路径：

```powershell
py -3 .\macro_layers\macro_run_orchestrator_sim.py --seed 20260630 --scenario-state occurred --scenario-branch-id auto
```

生成发生路径，并发布到现有 HTML viewer 读取的输出目录：

```powershell
py -3 .\macro_layers\macro_run_orchestrator_sim.py --seed 20260630 --scenario-state occurred --scenario-branch-id auto --publish-viewer scenario
```

单独重算已开放区域的航空需求层：

```powershell
py -3 .\macro_layers\regional_aviation_demand_layer_sim.py --region north_america
py -3 .\macro_layers\regional_aviation_demand_layer_sim.py --region china_mainland
py -3 .\macro_layers\regional_aviation_demand_layer_sim.py --region west_north_europe
py -3 .\macro_layers\regional_aviation_demand_layer_sim.py --region japan_korea
py -3 .\macro_layers\regional_aviation_demand_layer_sim.py --region southeast_asia
py -3 .\macro_layers\regional_aviation_demand_layer_sim.py --region south_asia_india
py -3 .\macro_layers\regional_aviation_demand_layer_sim.py --region hk_macao_taiwan
py -3 .\macro_layers\regional_aviation_demand_layer_sim.py --region middle_east_gulf
py -3 .\macro_layers\regional_aviation_demand_layer_sim.py --region oceania
py -3 .\macro_layers\regional_aviation_demand_layer_sim.py --region south_east_europe_mediterranean
py -3 .\macro_layers\regional_aviation_demand_layer_sim.py --region central_asia_turkey_eurasia
py -3 .\macro_layers\regional_aviation_demand_layer_sim.py --region north_africa
py -3 .\macro_layers\regional_aviation_demand_layer_sim.py --region latin_america_caribbean
py -3 .\macro_layers\regional_aviation_demand_layer_sim.py --region sub_saharan_africa
```

单独重算已开放区域的航空供给/满足率层：

```powershell
py -3 .\macro_layers\regional_air_capacity_supply_layer_sim.py --region north_america
py -3 .\macro_layers\regional_air_capacity_supply_layer_sim.py --region china_mainland
py -3 .\macro_layers\regional_air_capacity_supply_layer_sim.py --region west_north_europe
py -3 .\macro_layers\regional_air_capacity_supply_layer_sim.py --region japan_korea
py -3 .\macro_layers\regional_air_capacity_supply_layer_sim.py --region southeast_asia
py -3 .\macro_layers\regional_air_capacity_supply_layer_sim.py --region south_asia_india
py -3 .\macro_layers\regional_air_capacity_supply_layer_sim.py --region hk_macao_taiwan
py -3 .\macro_layers\regional_air_capacity_supply_layer_sim.py --region middle_east_gulf
py -3 .\macro_layers\regional_air_capacity_supply_layer_sim.py --region oceania
py -3 .\macro_layers\regional_air_capacity_supply_layer_sim.py --region south_east_europe_mediterranean
py -3 .\macro_layers\regional_air_capacity_supply_layer_sim.py --region central_asia_turkey_eurasia
py -3 .\macro_layers\regional_air_capacity_supply_layer_sim.py --region north_africa
py -3 .\macro_layers\regional_air_capacity_supply_layer_sim.py --region latin_america_caribbean
py -3 .\macro_layers\regional_air_capacity_supply_layer_sim.py --region sub_saharan_africa
```

如果本机 `python` 可直接使用，也可以把 `py -3` 换成 `python`。

## 查看界面

```text
global_gdp_viewer.html
```

北京机场经营面板：

```text
beijing_airport_operations_viewer.html
```

城市 seed 动态测试页：

```text
dynamic_tests/seed_explorer/start_seed_explorer.bat
```

页面读取 canonical 输出：

```text
output/global_macro/
output/regional_macro/
output/regional_macro_reconciled/
output/regional_aviation_demand/
output/regional_air_capacity_supply/
output/city_airport_market_demand/
output/city_airport_potential_passenger_forecast/
output/city_airport_quarterly_operations/
output/city_airport_financial_state/
output/city_airport_valuation/
```

主 viewer 已在“航空需求”视图下读取 14 区航空供给/满足率输出，并显示分项旅客供给满足率。

北京机场经营面板当前读取北京季度经营、财务、估值和有效客流预测输出。建议通过 orchestrator 重算并发布 canonical viewer 数据：

```powershell
py -3 .\macro_layers\macro_run_orchestrator_sim.py --seed 20261324 --scenario-state none --publish-viewer baseline
```

orchestrator 默认只归档 run，不覆盖页面数据。需要更新页面数据时加：

```powershell
--publish-viewer baseline
--publish-viewer scenario
```

## 输出结构

归档 run：

```text
output/macro_runs/<run_id>/
```

每个 run 通常包含：

```text
baseline/
occurred_<branch_id>_<trigger_year>/
manifest.json
```

每个变体内部都有全球宏观、14 区区域宏观、区域对账、区域航空需求和区域航空供给输出。

已配置的航空需求和航空供给区域会随 run 归档，目前包括：

```text
regional_aviation_demand/north_america/
regional_aviation_demand/china_mainland/
regional_aviation_demand/west_north_europe/
regional_aviation_demand/japan_korea/
regional_aviation_demand/southeast_asia/
regional_aviation_demand/south_asia_india/
regional_aviation_demand/hk_macao_taiwan/
regional_aviation_demand/middle_east_gulf/
regional_aviation_demand/oceania/
regional_aviation_demand/south_east_europe_mediterranean/
regional_aviation_demand/central_asia_turkey_eurasia/
regional_aviation_demand/north_africa/
regional_aviation_demand/latin_america_caribbean/
regional_aviation_demand/sub_saharan_africa/
regional_air_capacity_supply/north_america/
regional_air_capacity_supply/china_mainland/
regional_air_capacity_supply/west_north_europe/
regional_air_capacity_supply/japan_korea/
regional_air_capacity_supply/southeast_asia/
regional_air_capacity_supply/south_asia_india/
regional_air_capacity_supply/hk_macao_taiwan/
regional_air_capacity_supply/middle_east_gulf/
regional_air_capacity_supply/oceania/
regional_air_capacity_supply/south_east_europe_mediterranean/
regional_air_capacity_supply/central_asia_turkey_eurasia/
regional_air_capacity_supply/north_africa/
regional_air_capacity_supply/latin_america_caribbean/
regional_air_capacity_supply/sub_saharan_africa/
```

## 文档入口

文档已按层级收拢到 `docs/`：

1. `docs/Game_Overview.md`
2. `docs/README.md`
3. `docs/macro/README.md`
4. `docs/regional_macro/README.md`
5. `docs/regional_aviation/README.md`
6. `docs/airport_operations/README.md`

建议阅读顺序：

1. `docs/Game_Overview.md`
2. `docs/macro/Macro_Run_Orchestration.md`
3. `docs/macro/Global_Macro_Layer_Index.md`
4. `docs/regional_macro/Regional_Macro_Roadmap.md`
5. `docs/regional_macro/Regional_Branch_Transmission_Plan.md`
6. `docs/regional_macro/Regional_Macro_Reconciliation_Layer_Design.md`
7. `docs/regional_aviation/Regional_Aviation_Demand_Layer_Overview.md`
8. `docs/regional_aviation/Regional_Air_Capacity_Supply_Layer_Design.md`
9. `docs/airport_operations/City_Airport_Market_Layer_Plan.md`
10. `docs/airport_operations/City_Airport_Potential_Passenger_Forecast_System_Plan.md`

底层单层脚本仍保留在 `macro_layers/`，用于调试单独的全球层、区域层或对账层。
