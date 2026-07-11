# Airport Docs Index

这个目录按模型层级组织机场游戏文档，避免宏观、区域、航空和机场经营说明混在一起。

## 文档分区

```text
docs/
  Current_Architecture_and_Runtime.md
    当前真实入口、前后端、Run、Viewer、缓存和存档关系
  Performance_and_Incremental_Evaluation.md
    区域/城市并行和玩家增量重算的技术评估与暂缓结论
  Project_Slimming_and_Python_Entry_Unification_Plan.md
    输出瘦身、缓存生命周期和 Python 入口统一的实施路径
  Project_Slimming_Audit_2026-07-11.md
    本轮实际删除、保护哈希、备份和固定 Seed 对照记录
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

1. `Current_Architecture_and_Runtime.md`
2. `Game_Overview.md`
3. `API_and_JSON_Schema.md`
4. `Performance_and_Incremental_Evaluation.md`
5. `Project_Slimming_and_Python_Entry_Unification_Plan.md`
6. `Forecast_Viewer_Lazy_Loading.md`
7. `Global_Viewer_Lazy_Loading.md`
8. `Operations_Viewer_Lazy_Loading.md`
9. `macro/Macro_Run_Orchestration.md`
10. `macro/Global_Macro_Layer_Index.md`
11. `regional_macro/Regional_Macro_Roadmap.md`
12. `regional_macro/Regional_Branch_Transmission_Plan.md`
13. `regional_macro/Regional_Macro_Reconciliation_Layer_Design.md`
14. `parameter_ranges/IMPORTANT_Macro_Regional_Aviation_Parameter_Range_Guide.md`
15. `regional_aviation/Regional_Aviation_Demand_Layer_Overview.md`
16. `regional_aviation/Regional_Air_Capacity_Supply_Layer_Design.md`
17. `airport_operations/City_Airport_Market_Layer_Plan.md`
18. `airport_operations/City_Airport_Potential_Passenger_Forecast_System_Plan.md`
19. `parameter_ranges/IMPORTANT_City_Airport_Market_Parameter_Range_Guide.md`
20. `parameter_ranges/IMPORTANT_City_Airport_Quarterly_Operations_Parameter_Range_Guide.md`

文档边界：`Current_Architecture_and_Runtime.md` 是当前运行事实的唯一入口；`Game_Overview.md` 解释游戏机制；`Performance_and_Incremental_Evaluation.md` 记录已完成的技术评估和暂缓实施结论；`Project_Slimming_and_Python_Entry_Unification_Plan.md` 规划输出瘦身和 Python 入口统一；`Post_Refactor_UI_Consolidation_Plan.md` 只记录整理完成后的界面合并方向，不代表已经实现。

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
       |-> Effective passenger forecast (player information)
       `-> Airport quarterly operations (real city input)
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
- 概率分岔时间线可以按 Seed 连续选择多个事件，并保留事件冷却期。
- 北京动态测试已经形成可操作的最小闭环：季度推进、存档、合同确认、翻新、新建、拆除、拆除重建和融资行动都会由 Python 服务端重算。
- 统一首页和单端口本地服务已经集中四个主要页面，并显示 Viewer、缓存和存档状态。
- 玩家存档已与临时 Run 缓存分离；清理缓存不会删除独立存档。
- 完整 Run 和 Viewer 发布均使用 staging、校验和原子切换。
- Viewer 已分别按报告、区域和估值数据块进行按需加载。
- 已建立固定 Seed 回归测试、API 快照、JSON Schema、最小 `pyproject.toml` 和跨平台 CI。
- 已建立 60 年 baseline/occurred/probabilistic 语义摘要、14 区与 47 城结构、关键 CSV 表头及融资行动回放保护。
- 已提供 `python -m airport_ui` 跨平台统一入口，Windows BAT 继续兼容。
- 本地 HTTP 服务已限制 2 MiB JSON 请求、检查 Content-Type、区分错误类型，并要求非回环启动显式授权。
- 缓存列表只计算一次当前指纹，指纹依赖字节按文件状态复用。
- 完整 Run 校验已扩展到表头、列宽、Seed、年份、`year_index` 和 14 区覆盖。
- Seed Explorer 已把 storage、progress、run locks、HTTP 和后台 jobs 搬出主服务；项目、合同、融资等领域规则仍在继续整理。
- 可选后台 Run Job 已提供提交和查询接口，旧同步 API 保持不变。
- 前端已拆出 bootstrap、state、data client 与主要 Renderer；Seed Explorer 已按九类职责拆分业务脚本。
- 统一首页和四个页面已经完成实际浏览器验收。
- 公共 `clamp`、`resolve_seeds` 和行为完全相同的最大 `round_record` 组已在不改变结果的前提下抽取。
- 区域/城市并行与玩家增量重算已完成技术评估，当前决定暂缓实现。

未完成：

- 其它城市的季度经营和财务配置。
- 合同合作方、报价选择和谈判博弈；当前只有建议条款确认与到期处理。
- 独立商业销售预测；当前合同规则已经可运行，但仍主要依赖既有经营输入和建议条款。
- 商业情报中心、研究所、市场交易和并购。
- 其它国家和地区的城市机场经营配置。
- 把经营历史、有效客流预测和玩家事务合并为正式游戏 UI。
- 正式游戏界面的未来信息隔离；当前动态测试仍会把完整季度结果发送给浏览器用于本地推进。

## 分区入口

- `macro/README.md`
- `regional_macro/README.md`
- `regional_aviation/README.md`
- `parameter_ranges/README.md`
- `airport_operations/README.md`
