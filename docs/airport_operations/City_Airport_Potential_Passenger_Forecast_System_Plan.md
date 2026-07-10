# City Airport Effective Passenger Forecast System Plan

这份文档记录城市机场有效客流预测系统。它不是估值模型，也不是新的真实客流层；它是玩家在游戏内购买、查看和使用的市场研究报告。

## 当前实现状态

北京 v0.2 已经落地为独立预测层。文件名和输出目录暂时沿用 `potential_passenger_forecast`，以减少 orchestrator 和 viewer 路径迁移成本，但主口径已经改为市场有效客流：

```text
airport/macro_layers/city_airport_potential_passenger_forecast_layer_sim.py
airport/config/city_airport_potential_passenger_forecast/beijing_airport_system_potential_passenger_forecast_v1.json
airport/output/city_airport_potential_passenger_forecast/china_mainland/
airport/output/macro_runs/<run_id>/<variant>/city_airport_potential_passenger_forecast/china_mainland/
```

`macro_run_orchestrator_sim.py` 在城市机场客流层之后自动运行已配置城市的预测层。当前只有北京配置，因此全链路 run 里只有北京会生成这一层；其它城市仍只生成真实城市客流层。

北京 v0.2 输出：

- 初级预测：6 年窗口，当前有公开共识、地方简报、热门叙事三份样例。
- 中级预测：8 年窗口，当前有基础研究、平衡小组、增长组三份样例。
- 高级预测：10 年窗口，当前有咨询基准、数据模型、保守情景三份样例。
- 专业级预测：12 年窗口，当前有顶级机构、宏观航研、逆向研究三份样例。
- `god_future_peek`：神级未来透视，`future_peek_mode = true`，固定 100 分，直接显示真实有效客流曲线。

## 主预测对象

预测系统的主对象从“城市潜在客流”改为“市场有效客流”：

```text
market_effective_passengers =
  min(city_potential_passengers, city_airline_supply_passengers)
```

原因是有效客流更接近玩家真正要下注的市场机会：

```text
城市潜在客流
  决定这个城市想飞多少，是长期慢变量。

航司供给
  决定市场给多少座位，是更强的周期变量。

市场有效客流
  是不考虑玩家机场容量前，机场可以争取的市场客流机会。

机场承接客流
  再由玩家容量、施工、翻新、最大容量实现率决定。
```

因此，机场容量不足时不应让预测系统背锅。玩家自己能看到槽位、设计容量、最大容量和施工状态，这部分更像明牌经营计算；预测真正有价值的地方，是看清潜在需求与航司供给之间谁在约束市场。

## 分项预测边界

有效客流的五类分项不再像总量那样单独生成五条漂移区间曲线。第一版采用：

```text
forecast_component_effective_passengers =
  forecast_effective_passengers
  * forecast_component_effective_share
```

这样五类分项永远加总回总有效客流，避免出现总数和分项互相打架。

真实分项有效客流按瓶颈状态拆解：

```text
if city_potential_passengers <= city_airline_supply_passengers:
  component_effective_share = component_potential_passengers / city_potential_passengers

if city_airline_supply_passengers < city_potential_passengers:
  component_effective_share = component_airline_supply_passengers / city_airline_supply_passengers
```

预测分项占比由预测瓶颈基准、当前公开结构、滞后的隐藏真实结构、预测质量分和稳定偏差共同生成：

- 如果报告判断为潜在需求瓶颈，分项结构更接近潜在客流结构。
- 如果报告判断为航司供给瓶颈，分项结构更接近航司供给结构。
- 质量越高，越能读取滞后的 seed 结构信号，结构偏差越小。
- 质量越低，仍可能出现过度乐观、过度悲观或错判结构，但偏差会受到绝对百分点和相对占比的双重限幅。
- 中转、长途保留更高不确定性；商务、休闲相对稳定；小占比分项不会因为固定百分点噪声被轻易打到数倍。

它不是神秘的五条独立预测曲线，而是对总有效客流的结构拆分。经营上更重要的商务、长途、中转在审计分里权重略高；探亲访友权重略低。

## 与真实路径的边界

真实城市机场层回答：

```text
这条 seed 下实际会发生什么？
```

有效客流预测层回答：

```text
玩家在当前年份通过某种质量的市场研究，能看到多少未来市场有效客流机会？
```

边界：

- 普通预测可以读取隐藏真实潜在客流、航司供给和有效客流曲线，然后按预测等级降质输出。
- 普通预测不能直接输出隐藏真实曲线的精确单点值，应输出区间、等级、趋势、瓶颈判断和风险标签。
- 经营预测、商业合同、财务预测和估值不能直接读取隐藏真实未来；它们只能读取玩家可见预测结果。
- 机场承接客流不能直接用真实未来曲线。承接客流必须根据玩家当时和计划中的机场容量、施工、槽位配置和容量实现率重新计算。
- 神级预测不是更准的普通预测，而是明确的未来透视 / 开挂模式。它可以读取或显示隐藏真实有效客流曲线，但必须被单独标记，不进入普通平衡。

## 预测等级

普通预测内部使用连续分数插值，但神级预测与普通预测之间必须有断层。

```text
普通预测：
  forecast_quality_score = 0 - 70

神级预测：
  forecast_quality_score = 100
  future_peek_mode = true

保留断层：
  71 - 99 不作为普通预测插值空间
```

| 等级 | 分数区间 | 连续数字窗口 | 玩家理解 |
|---|---:|---:|---|
| 初级预测 | 0 - 25 | 1-6 年 | 粗略行业报告，可能自信但错 |
| 中级预测 | 25 - 50 | 1-8 年 | 基础研究 / 内部研究 |
| 高级预测 | 50 - 65 | 1-10 年 | 高质量研究报告 |
| 专业级预测 | 65 - 70 | 1-12 年 | 普通模型上限 |
| 神级预测 | 100 | 调试可到全周期 | 未来透视 / 开挂 |

`public_consensus` 是报告来源，不是固定低分。公开共识的有效 `forecast_quality_score` 可以在 18-50 分之间随 seed、as-of 年份和预测年限变化；它有时愚蠢，有时也可能达到普通咨询报告的低端水平。

## 基本公式

预测层先分别生成潜在客流预测和航司供给预测：

```text
visible_forecast_potential =
  naive_public_potential_curve * (1 - seed_signal_capture)
  + hidden_true_potential_curve_lagged * seed_signal_capture

visible_forecast_airline_supply =
  naive_public_airline_supply_curve * (1 - seed_signal_capture)
  + hidden_true_airline_supply_curve_lagged * seed_signal_capture
```

再得到主预测：

```text
forecast_effective_passengers_mid =
  min(
    forecast_potential_passengers_mid,
    forecast_airline_supply_passengers_mid
  )

forecast_market_bottleneck =
  demand_limited if forecast_potential <= forecast_airline_supply
  else airline_supply_limited
```

区间带围绕有效客流中值展开：

```text
forecast_effective_passengers_low =
  forecast_effective_passengers_mid * (1 - forecast_downside_band)

forecast_effective_passengers_high =
  forecast_effective_passengers_mid * (1 + forecast_upside_band)
```

重要边界：

```text
不要用 hidden_true_curve +/- error_band 来生成普通预测区间。
不要让 hidden_true_curve 默认等于 (forecast_low + forecast_high) / 2。
不要让 forecast_mid 成为真实值的伪装。
```

低质量报告可以“自信地错”。可见区间宽度不应直接等于真实预测质量；真实质量更多体现在中心值、seed 捕捉、滞后、瓶颈判断和分项结构上。

神级预测走单独分支：

```text
if future_peek_mode:
  forecast_effective_passengers_mid = hidden_true_effective_passengers
  forecast_effective_passengers_low = hidden_true_effective_passengers
  forecast_effective_passengers_high = hidden_true_effective_passengers
  forecast_component_effective_share = hidden_true_component_effective_share
  forecast_error_band = 0
  forecast_lag_years = 0
  forecast_method_note = future_peek_god_mode
```

## 事后审计分

报告等级和评分需要拆开：

```text
forecast_report_tier
  初级 / 中级 / 高级 / 专业级 / 神级。

realized_report_quality_score
  报告输出之后，再拿隐藏真实 seed 曲线审计出来的 0-100 分。
```

当前审计分按一份 as-of 报告整条曲线评分。每个目标年先计算年度分：

```text
point_score =
  50% 有效客流中值准确度
+ 18% 有效客流趋势 / 增长率方向
+ 10% 曲线节奏 / 拐点形状
+ 10% 分项结构准确度
+ 7% 区间校准
+ 5% 瓶颈判断准确度
```

然后按年份加权平均：

```text
year_weight = 1 + 0.08 * forecast_horizon_years
```

这个评分设计让总有效客流仍然是大头，但不会完全忽略分项。玩家如果只看对了总数，却把商务/长途/休闲结构看错，仍会在分项结构分里被扣分；但分项不会反客为主。

## 输出内容

有效客流预测报告第一版输出：

```text
forecast_model_version
forecast_report_id
forecast_report_tier
forecast_report_source
reported_confidence_style
forecast_bias_direction
configured_forecast_quality_score
forecast_quality_score
future_peek_mode
city_airport_market_id
city_name
region_id
seed
as_of_year
as_of_quarter
data_cutoff_year
data_cutoff_quarter

forecast_year
forecast_horizon_years
current_effective_passengers_million
current_potential_passengers_million
current_airline_supply_passengers_million
forecast_effective_passengers_mid_million
forecast_effective_passengers_low_million
forecast_effective_passengers_high_million
forecast_potential_passengers_mid_million
forecast_airline_supply_passengers_mid_million
forecast_market_bottleneck
forecast_error_band_pct
forecast_downside_band_pct
forecast_upside_band_pct
forecast_confidence_pct

realized_score_method_version
realized_report_quality_score
realized_point_quality_score
realized_midpoint_accuracy_score
realized_trend_accuracy_score
realized_shape_accuracy_score
realized_component_structure_score
realized_bottleneck_accuracy_score
realized_interval_calibration_score
realized_report_weighted_abs_error_pct
realized_report_interval_hit_rate_pct
realized_report_bias_pct
realized_report_bias_label

business/leisure/vfr/long_haul/transfer_forecast_effective_passengers_mid_million
business/leisure/vfr/long_haul/transfer_forecast_effective_share_pct
```

开发调试字段包括：

```text
debug_hidden_true_effective_passengers_million
debug_hidden_true_potential_passengers_million
debug_hidden_true_airline_supply_passengers_million
debug_hidden_true_market_bottleneck
business/leisure/vfr/long_haul/transfer_debug_hidden_true_effective_passengers_million
business/leisure/vfr/long_haul/transfer_debug_hidden_true_effective_share_pct
business/leisure/vfr/long_haul/transfer_debug_hidden_true_potential_passengers_million
business/leisure/vfr/long_haul/transfer_debug_hidden_true_airline_supply_passengers_million
```

## 界面表达

当前北京测试页展示：

- 有效客流预测曲线：中位数 + 区间带 + 隐藏真实有效客流。
- 当前报告摘要：审计分、分项分、瓶颈分、加权误差、区间命中率。
- 分项预测面板：按目标年展示商务、休闲、探亲访友、长途、中转的预测有效客流、真实有效客流、预测占比、真实占比、真实潜在和真实供给。
- 报告明细表：有效预测、潜在/供给拆解、真实有效、真实潜在/供给、预测/真实瓶颈和区间命中。

这是测试界面，因此会显示真实值和审计分。正式游戏界面应根据玩家权限隐藏 debug 真值，只保留可见报告和事后复盘所需字段。

## 与承接客流预测的关系

有效客流预测回答：

```text
如果先不考虑我自己的机场容量，这个市场未来有多少可争取客流？
```

承接客流预测回答：

```text
玩家当前和计划中的机场系统能吞吐多少？
```

第一版承接口径：

```text
forecast_served_passengers =
  min(
    forecast_effective_passengers,
    forecast_airport_effective_capacity
  )
```

机场容量、翻新、重建、施工期容量损失和最大容量实现率是玩家侧明牌或半明牌经营变量，不应混入市场预测主评分。这样玩家能提前发现某个城市值得押注，却不能免费得到“我扩不扩都会自动赢”的结论。

## 与商业合同和估值的关系

商业销售预测读取的是玩家可见的预测客流，而不是隐藏真实客流。

```text
visible_effective_passenger_forecast
  -> served_passenger_forecast under player plan
  -> commercial_sales_forecast
  -> contract_offer_model
  -> financial_forecast
  -> valuation observation
```

估值系统当前仍以净资产为主。未来若恢复 Forward EV 或 Market EV，也应读取玩家可见有效客流预测和合同质量，而不是直接读取隐藏真实未来。

## 实现顺序建议

1. 当前已完成北京有效客流预测原型：总有效客流、潜在/供给拆解、分项结构、评分和测试界面。
2. 下一步可把同一预测配置模板扩展到中国大陆其它城市。
3. 再做城市预测报表：Top 上行城市、Top 下行城市、有效客流缺口、航司供给瓶颈观察。
4. 再做玩家容量计划下的承接预测，把当前/计划槽位容量接入预测结果。
5. 最后让商业销售预测、合同报价和估值观察读取这套预测输出。

第一版不要做复杂机构市场、竞价购买报告、AI 研究员或多机构观点分歧。先把一个稳定、可解释、可接下游的预测报告跑通。
