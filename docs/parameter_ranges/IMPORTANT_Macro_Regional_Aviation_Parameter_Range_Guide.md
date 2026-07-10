# IMPORTANT: Macro / Regional / Aviation Parameter Range Guide

这份文档是前四层的调参记忆索引：全球宏观层、区域宏观层、区域航空需求层、区域航空供给层。它的作用是防止后续忘记哪些参数会牵动整条链路，以及哪些数值范围容易把模型推得太离谱。

真实 source of truth 仍然是代码。本文件记录的是当前游戏模型的推荐范围、危险信号和应优先查看的代码位置。

## 当前状态

- 全球宏观层：已接入一键 run，并支持 seed 与历史岔路。
- 区域宏观层：14/14 区配置完成，并带区域对账。
- 区域航空需求层：14/14 区配置完成，分项仍沿用商务、休闲、探亲访友、长航程、中转五类。
- 区域航空供给层：14/14 区配置完成，会把潜在需求压缩为航司可承接客流与满足率。
- 城市机场和季度经营层不在本文范围内，应另建参数文档。

## 1. 全球宏观层参数范围

先看这些代码：

- `airport/macro_layers/macro_run_orchestrator_sim.py`
- `airport/macro_layers/global_gdp_annual_sim.py`
- `airport/macro_layers/global_inflation_annual_sim.py`
- `airport/macro_layers/global_policy_rate_layer_sim.py`
- `airport/macro_layers/global_yield_curve_layer_sim.py`
- `airport/macro_layers/global_dollar_liquidity_layer_sim.py`
- `airport/macro_layers/global_credit_spread_layer_sim.py`
- `airport/macro_layers/global_asset_price_layer_sim.py`
- `airport/macro_layers/global_oil_commodity_layer_sim.py`
- `airport/macro_layers/global_macro_feedback_calibration_sim.py`

主要参数族：

- GDP 长期趋势：`base_trend_growth_pct`、`terminal_trend_growth_pct`、`trend_slowdown_half_life_years`。
  - 正常：长期实际增长约 `1.5% - 3.5%`。
  - 可接受：`0.5% - 5.0%`。
  - 危险：长期低于 `0%` 或高于 `6%`，除非是短期危机或追赶型世界。
- GDP 周期和冲击：`volatility_scale`、`output_gap_*`、`shock_*`、`crisis_*`、`boom_*`。
  - 正常年度增长大致在 `-3% - 5%` 内摆动。
  - 严重危机可以到 `-6% - -9%`，但不能长期停留。
  - `output_gap_cap_pct` 当前是硬边界类参数，过大容易让后续通胀、利率和航空需求全线震荡。
- 通胀锚：`headline_anchor_pct`、`core_anchor_pct`、`expectation_anchor_pct`、`max_headline_pct`。
  - 正常：`1.5% - 4.0%`。
  - 可接受：`0% - 8%`。
  - 危险：长期高于 `8%` 或长期低于 `0%`，会显著扭曲利率、消费与航司成本。
- 政策利率：`base_real_neutral_rate_pct`、`min_policy_rate_pct`、`max_policy_rate_pct`、`policy_adjustment_speed`。
  - 正常政策利率：`0% - 7%`。
  - 可接受：`-1% - 10%`，但负利率和双位数利率应作为特殊环境。
  - 单年加息/降息上限不要过大，否则信用、汇率、资产价格会出现阶跃。
- 信用利差：`min_ig_spread_bps`、`max_ig_spread_bps`、`min_hy_spread_bps`、`max_hy_spread_bps`、各 beta。
  - 高收益利差正常：`250 - 700 bps`。
  - 压力期：`700 - 1200 bps`。
  - 危机：`1200 bps+`，不宜常态化。
- 美元流动性、金融条件、风险偏好类指数。
  - 这些多数按 `0 - 100` 指数理解。
  - 正常区间大约 `35 - 70`。
  - `75+` 通常应被视为压力或过热。
- 油价与商品：`global_oil_commodity_layer_sim.py` 中的油价、能源通胀和供需压力参数。
  - Brent 常态可按 `40 - 140 USD/bbl` 理解。
  - `20 - 220` 可作为极端测试范围。
  - 超出此范围应绑定历史岔路或事件，而不是普通随机波动。

调参提醒：

- 先改全球趋势，再改冲击概率，最后才改反馈 beta。
- 如果航空需求在所有区域同时爆炸，优先查 GDP 趋势、通胀/利率反馈和油价路径。
- 如果所有区域同时塌陷，优先查信用利差、美元流动性、危机概率和反馈校准。

## 2. 区域宏观层参数范围

先看这些代码和文档：

- `airport/macro_layers/regional_macro_layer_sim.py`
- `airport/macro_layers/regional_macro_reconciliation_sim.py`
- `airport/docs/regional_macro/README.md`
- `airport/docs/regional_macro/regions/`

当前 14 区：

- `north_america`
- `china_mainland`
- `west_north_europe`
- `japan_korea`
- `southeast_asia`
- `south_asia_india`
- `middle_east_gulf`
- `hk_macao_taiwan`
- `oceania`
- `south_east_europe_mediterranean`
- `central_asia_turkey_eurasia`
- `north_africa`
- `latin_america_caribbean`
- `sub_saharan_africa`

主要参数族：

- 区域权重：`global_weight`。
  - 用于区域 GDP 体量和对账。
  - 14 区权重应整体保持可对账，不要单独把某区调大后忘记总盘。
- 区域增长骨架：`trend_growth_pct`、`potential_growth_floor_pct`、`potential_growth_ceiling_pct`、`growth_floor_pct`、`growth_ceiling_pct`。
  - 成熟经济体正常趋势：`0.8% - 3.0%`。
  - 新兴/追赶经济体正常趋势：`2.5% - 6.0%`。
  - 高追赶或资源周期可以短期到 `7% - 8.5%`。
  - 长期 `8%+` 很容易把后续航空需求推爆。
- 区域结构指数：`income_level_index`、`market_maturity`、`domestic_demand_weight`、`international_exposure`、`tourism_exposure`、`business_exposure`。
  - 多数按 `0 - 1` 或 `0 - 100` 语义理解。
  - `market_maturity`、`domestic_demand_weight`、`international_exposure` 等通常不要超过 `1.5`。
  - `income_level_index` 一般按 `20 - 110` 使用。
- 全球传导敏感度：`oil_sensitivity`、`dollar_sensitivity`、`credit_sensitivity`、`equity_wealth_sensitivity`、`policy_rate_sensitivity`、`geopolitical_sensitivity`。
  - 正常：`0.3 - 1.4`。
  - 高敏感区域：`1.4 - 1.7`。
  - `1.8+` 要谨慎，容易让区域路径比全球路径更剧烈。
  - `dollar_sensitivity` 可以为负，代表美元走强未必伤害该区域。
- 通胀和政策锚：`inflation_anchor_pct`、`core_inflation_anchor_pct`、`policy_neutral_rate_pct`、`policy_floor_pct`、`policy_ceiling_pct`。
  - 成熟区域通胀锚大多 `1.5% - 2.8%`。
  - 新兴区域通胀锚大多 `2.5% - 4.5%`。
  - 政策上限过低会压不住通胀，过高会把信用和航空需求打穿。
- 分岔传导：`regional_branch_*` 输出来自 `BRANCH_TRANSMISSION_PROFILES` 和区域 loadings。
  - `regional_branch_exposure_index`、`regional_branch_strength_index` 可按 `0 - 100` 理解。
  - `50` 近似中性，`80+` 是强冲击。
- 区域结构性 seed 势能：`REGIONAL_SEED_POTENTIALS` 输出 `regional_seed_*` 字段。
  - `regional_seed_effective_growth_bias_pct` 是释放后的长期潜在增长偏移，不是短期事件冲击。
  - 成熟区域建议大致在 `-1.0pp - +1.2pp`，新兴/追赶区域可到 `-1.7pp - +1.9pp`。
  - `regional_seed_aviation_propensity_bias_pct`、`regional_seed_investment_cycle_bias_pct`、`regional_seed_openness_bias_pct` 一般应在 `-20% - +25%` 内。
  - 这些字段应逐年释放，不应在开局年份直接满额生效。

调参提醒：

- 区域宏观是城市机场需求和区域航空需求的共同上游。
- 如果某一区航空需求不合理，先查该区的 `trend_growth_pct`、收入、旅游/商务暴露、能源/美元/信用敏感度。
- 区域对账层用于保持全球与区域总量一致，不应用它来掩盖某个区域配置本身的问题。
- 如果不同 seed 下区域排名仍然过于固定，优先看 `REGIONAL_SEED_POTENTIALS` 的增长偏移范围和释放速度。
- 如果区域排名过于混乱，优先降低 `annual_growth_bias_*`，不要直接改 `global_weight`。

## 3. 区域航空需求层参数范围

先看这些代码和文档：

- `airport/macro_layers/regional_aviation_demand_layer_sim.py`
- `airport/docs/regional_aviation/Regional_Aviation_Demand_Layer_Overview.md`

核心输入来自区域宏观层：

- `regional_gdp_growth_pct`
- `real_income_growth_pct`
- `consumer_confidence_index`
- `regional_macro_stress_index`
- `regional_energy_cost_pressure_index`
- `currency_pressure_index`
- `regional_hy_spread_bps`
- `regional_equity_return_pct`
- 历史岔路相关字段
- 区域 seed 字段：`source_regional_seed_*`

主要参数族：

- 五类客群权重：`business_travel_weight`、`leisure_travel_weight`、`vfr_travel_weight`、`long_haul_weight`、`transfer_hub_weight`。
  - 五项应接近合计 `1.0`。
  - 单项常规范围：`0.05 - 0.45`。
  - 旅游强区休闲可到 `0.55 - 0.70`。
  - 枢纽强区中转可到 `0.15 - 0.30`。
- 市场暴露：`domestic_market_depth`、`international_exposure`、`tourism_exposure`。
  - 正常：`0 - 1.0`。
  - 特殊增强可到 `1.2`，但应有明确原因。
- 收入与价格敏感度：`income_sensitivity`、`price_sensitivity_base`。
  - `income_sensitivity` 正常 `0.6 - 1.1`；`1.2+` 会让需求随宏观增长快速放大。
  - `price_sensitivity_base` 正常 `35 - 65`；`70+` 会让油价、汇率、票价压力非常伤需求。
- 票价弹性基准：
  - 商务：`0.12 - 0.42`。
  - 休闲：`0.90 - 2.10`。
  - 探亲访友：`0.40 - 1.10`。
  - 长航程：`0.55 - 1.35`。
  - 中转：`0.65 - 1.55`。
  - 高端：`0.08 - 0.32`。
- 油价和汇率敏感度：`oil_fare_sensitivity`、`currency_travel_sensitivity`。
  - 正常：`0.2 - 0.9`。
  - `1.0+` 应只用于高度进口燃油压力或外汇压力区域。
- 高端与商业消费倾向：`premium_mix_base`、`duty_free_culture_index`、`luxury_retail_affinity`、`electronics_retail_affinity`。
  - `premium_mix_base` 正常 `5% - 22%`，枢纽/高收入区可更高。
  - 消费亲和参数通常 `0.3 - 1.2`。
  - 输出的消费倾向指数通常看 `70 - 140`；`50 - 170` 是可接受测试范围；`180+` 需要检查。
- 需求惯性：`demand_growth_persistence`、`demand_adjustment_speed`。
  - `persistence` 建议 `0.35 - 0.70`。
  - `adjustment_speed` 建议 `0.30 - 0.60`。
  - 两者同时偏高会放大周期追涨杀跌。

输出含义：

- 这一层产出的是区域航空潜在需求，不是最终承接客流。
- 五类客群分项是后续城市机场需求、商业和合同模型的控制点，不应另起一套客群分类。
- `duty_free_propensity_index`、`luxury_retail_propensity_index` 等是消费倾向，不等于真实销售额。

调参提醒：

- 如果旅游需求太惨，先看休闲权重、旅游暴露、价格敏感度、油价/汇率传导。
- 如果商务需求过强，先看商务权重、收入敏感度、消费者信心与宏观压力的 beta。
- 如果商业倾向指数剧烈波动，先看区域宏观波动，再看本层亲和参数。
- 如果某个 seed 下航空需求强于 GDP 解释，检查 `source_regional_seed_aviation_propensity_bias_pct` 和 `source_regional_seed_openness_bias_pct`。

## 4. 区域航空供给层参数范围

先看这些代码和文档：

- `airport/macro_layers/regional_air_capacity_supply_layer_sim.py`
- `airport/docs/regional_aviation/Regional_Air_Capacity_Supply_Layer_Design.md`

核心输入来自区域航空需求层：

- `regional_air_demand_index`
- 五类客群需求指数与份额
- `airfare_pressure_index`
- `airfare_price_sensitivity_index`
- `input_macro_stress_index`
- `input_energy_cost_pressure_index`
- `input_currency_pressure_index`
- `input_hy_spread_bps`
- `input_consumer_confidence_index`
- 历史岔路相关字段
- 区域 seed 字段：`source_regional_seed_*`

主要参数族：

- 区域客流基准：`baseline_region_passenger_demand_million`。
  - 这是把需求指数转换为旅客量的规模锚。
  - 修改它会直接改变区域 served/unmet passenger scale。
  - 应与区域航空需求层基准和现实级别口径大致一致。
- 初始载客率与容量指数：`baseline_load_factor_pct`、`base_air_capacity_index`。
  - `baseline_load_factor_pct` 正常 `78% - 86%`。
  - `<75%` 代表供给宽松，`>88%` 代表开局就偏紧。
  - `base_air_capacity_index` 通常保持 `100`。
- 供给结构：`domestic_supply_depth`、`international_supply_flexibility`、`transfer_hub_priority`。
  - 正常：`0 - 1.0`。
  - 国内深度高会让本土需求更容易被承接。
  - 国际灵活度和中转优先级会影响长航程、中转承接能力。
- 约束基准：`airport_slot_constraint_base`、`aircraft_delivery_constraint_base`、`crew_labor_constraint_base`、`maintenance_cost_pressure_base`。
  - 正常：`10 - 45`。
  - `45 - 60` 是明显约束。
  - `60+` 应视作结构性瓶颈或危机，不宜常态化。
- 供给调整速度：`supply_growth_persistence`、`supply_adjustment_speed`。
  - `persistence` 建议 `0.30 - 0.55`。
  - `adjustment_speed` 建议 `0.40 - 0.65`。
  - 太高会让运力像需求一样剧烈跳动，太低会让长期短缺持续过久。
- 容量年度变化上限：`max_capacity_growth_pct`、`max_capacity_contraction_pct`。
  - 成熟区域增长上限常见 `3% - 5.5%`。
  - 成长区域可到 `5% - 7%`。
  - `8%+` 需要谨慎，会快速消灭瓶颈。
  - 收缩上限通常 `4% - 7%`；过低太僵硬，过高会造成断崖。
- 客群挤出权重：`business_displacement_weight`、`leisure_displacement_weight`、`vfr_displacement_weight`、`long_haul_displacement_weight`、`transfer_displacement_weight`。
  - 商务通常 `0.3 - 0.6`，代表较不容易被挤出。
  - 休闲通常 `1.1 - 1.6`，代表价格/容量紧张时更容易被挤出。
  - 探亲访友通常 `0.6 - 0.9`。
  - 长航程通常 `0.8 - 1.2`。
  - 中转通常 `0.9 - 1.4`。

输出含义：

- `potential_passengers_million` 是需求层想要的客流。
- `served_passengers_million` 是航司供给承接后的客流。
- `unmet_passengers_million` 是航司瓶颈或运营约束下未满足需求。
- `capacity_fulfillment_pct` 是区域供给满足率。
- 分项 `business_fulfillment_pct`、`leisure_fulfillment_pct` 等会告诉后续城市层哪些客群被压缩更多。

调参提醒：

- 如果所有区域满足率都很低，不要先改城市机场容量；先看本层 `max_capacity_growth_pct`、约束基准和基准载客率。
- 如果供给几乎永远 100% 满足，瓶颈层就失去意义；应提高槽位、机队、维修或人员约束，或降低运力增长上限。
- 机场经营层的机场容量是第二道瓶颈；本层代表航司供给瓶颈。两者不应混成同一层。

## 调参顺序建议

1. 改全球宏观趋势、波动和事件概率。
2. 改区域宏观的结构参数和传导敏感度。
3. 改区域航空需求的客群权重、收入/价格敏感度和消费倾向。
4. 改区域航空供给的容量增长、约束和客群挤出。
5. 重新跑一键链路，检查同一 seed 与历史岔路下是否仍能贯穿。
6. 最后再看城市机场、机场容量、季度经营和商业合同。

## 不要混淆的几件事

- 区域航空需求层是潜在需求，不是机场实际客流。
- 区域航空供给层是航司供给瓶颈，不是机场航站楼容量。
- 城市机场需求层可以沿用区域航空分项，但不应重新发明客群分类。
- 商业层可以使用消费倾向指数，但真实销售额还必须绑定客流、客群和合同结构。
- 参数范围文档是重要备忘，不是“永远不能改”的锁。
