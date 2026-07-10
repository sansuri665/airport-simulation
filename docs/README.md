# Airport Docs Index

这个目录按模型层级组织机场游戏文档，避免宏观、区域、航空和机场经营说明混在一起。

## 文档分区

```text
docs/
  macro/
    全球宏观、反馈校准、分岔风险和一键 run 编排
  regional_macro/
    14 区区域宏观、区域分岔传导和区域对账
  regional_aviation/
    区域航空需求、航司供给和供给满足率
  parameter_ranges/
    IMPORTANT：宏观、区域航空、城市机场客流、季度经营的参数范围和代码索引
  airport_operations/
    城市机场市场、机场名单、离散扩建和后续商业经营
```

## 推荐阅读顺序

1. `Game_Overview.md`
2. `macro/Macro_Run_Orchestration.md`
3. `macro/Global_Macro_Layer_Index.md`
4. `regional_macro/Regional_Macro_Roadmap.md`
5. `regional_macro/Regional_Branch_Transmission_Plan.md`
6. `regional_macro/Regional_Macro_Reconciliation_Layer_Design.md`
7. `parameter_ranges/IMPORTANT_Macro_Regional_Aviation_Parameter_Range_Guide.md`
8. `regional_aviation/Regional_Aviation_Demand_Layer_Overview.md`
9. `regional_aviation/Regional_Air_Capacity_Supply_Layer_Design.md`
10. `airport_operations/City_Airport_Market_Layer_Plan.md`
11. `airport_operations/City_Airport_Potential_Passenger_Forecast_System_Plan.md`
12. `parameter_ranges/IMPORTANT_City_Airport_Market_Parameter_Range_Guide.md`
13. `parameter_ranges/IMPORTANT_City_Airport_Quarterly_Operations_Parameter_Range_Guide.md`

## 当前主链条

```text
Global macro
  -> Branch risk watchlist
  -> Optional occurred / counterfactual branch path
  -> 14 regional macro paths
  -> Regional reconciliation and GDP levels
  -> Regional aviation demand
  -> Regional air capacity / supply fulfillment
  -> City airport market
  -> Effective passenger forecast
  -> Airport quarterly operations
  -> Financial state
  -> Net-asset valuation observation
```

## 当前完成度

已完成：

- 全球宏观主链条和反馈校准。
- 全球分岔风险 watchlist。
- 可选 occurred/counterfactual 分岔路径。
- 14 区区域宏观。
- 区域 GDP 体量、占比、排名、增长贡献和对账诊断。
- 全球分岔对区域宏观的显式传导。
- 14 区区域航空需求层 v0.1。
- 14 区区域航空供给/满足率层 v0.1。
- 中国大陆 47 城市机场市场真实潜在客流层。
- 中国大陆 47 城市 seed 航空势能模板。
- 北京有效客流预测层 v0.3：先预测潜在客流和航司供给，再取小值作为有效客流，并输出五类分项预测、瓶颈判断和事后审计分。
- 北京季度经营样板，包括容量裁剪、分项潜在/供给、航空收入、自营餐饮零售、免税/奢侈品合同收入、固定成本、拥挤成本和季节性。
- 北京财务状态、一般贷款、税务、亏损结转和净资产主估值样板。
- 一键生成 baseline/scenario run，并可发布到现有 viewer。
- viewer 内置 run browser。

未完成：

- 多个分岔同时发生或连续抽签。
- 其它城市的季度经营和财务配置。
- 玩家实际交互式扩建决策闭环。
- 动态测试 harness 和行动序列回放。
- 独立商业销售预测和合同签约系统。
- 商业情报中心、研究所、市场交易和并购。
- 预测报告测试页向正式游戏 UI 产品化。

## 分区入口

- `macro/README.md`
- `regional_macro/README.md`
- `regional_aviation/README.md`
- `parameter_ranges/README.md`
- `airport_operations/README.md`
