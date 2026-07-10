# IMPORTANT: City Airport Market Parameter Range Guide

这份文档记录城市机场客流层的设计边界。它的重点不是把每个城市数值一次性定死，而是防止后续扩展全球机场时忘记：哪些参数应按区域变化，哪些参数应按城市变化，哪些机场必须特殊覆盖。

真实 source of truth 仍然是代码和城市 JSON。本文件是重要调参记忆。

## 当前代码和配置入口

先看这些位置：

- `airport/macro_layers/city_airport_market_demand_layer_sim.py`
- `airport/config/city_airport_markets/`
- `airport/config/facility_size_catalogs/standard_terminal_sizes_v1.json`
- `airport/docs/airport_operations/City_Airport_Market_Layer_Plan.md`

当前状态：

- 中国大陆已有 47 个城市机场市场配置。
- 城市层接入区域航空需求和区域航空供给，seed 与历史岔路应继承上游路径。
- 城市层继续沿用区域航空需求层的五类客群：商务、休闲、探亲访友、长航程、中转。
- 当前默认航站楼规格表是 `standard_terminal_sizes_v1`，后续可以拆出区域化 catalog。
- v0.13 开始支持可选的 `seed_potential_model`：它让同一城市在不同 seed 下出现长期航空体量分化，但仍通过区域航空和区域宏观对齐分数约束，不应变成脱离上游的独立随机数。

## 核心设计结论

城市机场客流层应采用：

```text
区域模板
  -> 城市配置
  -> 特殊机场覆盖
```

不要把所有差异都塞进城市单点参数，也不要让每个区域重新发明机场槽位规则。

## 哪些参数应按区域变化

这些属于区域或区域模板层面的差异，未来不同区域应有不同默认值：

- 消费能力：影响免税、奢侈品、餐饮零售、普通零售的销售潜力。
- 客群比例倾向：商务、休闲、探亲访友、长航程、中转在不同区域的基础结构不同。
- 商业倾向：免税文化、奢侈品偏好、电子产品偏好、餐饮零售偏好不应全球一致。
- 长航程和国际暴露：欧洲、中东、港澳台、新加坡、北美门户城市与内陆城市差异很大。
- 航司供给承接偏好：区域航司体系、枢纽组织方式、国际航权环境会影响城市供给。
- 航站楼规格容量：同样叫 `large` 或 `giant`，不同区域不一定代表完全相同的容量。
- 允许规格上限：土地紧约束、噪音约束、政治约束或岛屿机场，应限制可选规格。

## 哪些参数应按城市变化

这些应继续放在每个城市机场市场 JSON 中：

- `city_airport_market_id`、`city_name`、`region_id`、`market_tier`、`market_type`。
- `baseline_region_demand_share_pct`：城市占区域航空需求的基准份额。
- `baseline_city_potential_passengers_million`：城市开局潜在客流规模。
- `annual_long_term_city_growth_bias_pct`：城市长期增长偏置。
- `max_long_term_city_growth_bias_pct`：城市长期额外增长上限。
- `seed_potential_model`：可选 seed 城市航空势能模板。用于让长期城市航空体量在不同世界中分化；未配置时保持旧公式。
- `base_airline_supply_passengers_million`：本地航司可承接供给基准。
- `regional_airline_capacity_growth_capture`：城市捕获区域运力增长的比例。
- `airline_supply_demand_pull_capture`：航司供给对城市潜在客流上行的追随强度。
- `airline_supply_cycle_amplitude_pct`：航司供给中短周期波动幅度。
- `airline_supply_shock_amplitude_pct`：seed 供给冲击的幅度。
- `airline_supply_adjustment_speed`：航司从上一年供给追向目标供给的速度。
- `airline_supply_volatility_bias`：城市级供给波动放大/压低系数。
- 五类客群基础份额和 bias。
- 商业 bias：高端、免税、奢侈品、电子、餐饮、普通零售。
- 机场名单、槽位数量、槽位角色、初始航站楼规格、开放年份。
- 确定名称的新机场或规划机场。

## 哪些规则应尽量保持统一

机场槽位是游戏结构，不需要每个区域都重新设计一套。

建议继续保持：

- 3 槽位机场：`3 辅助槽位`。
- 4 槽位机场：`1 次槽位 + 3 辅助槽位`。
- 5 槽位机场：`1 主槽位 + 1 次槽位 + 3 辅助槽位`。
- 新建大型规划机场默认可以是 5 槽位，除非城市规模或地理条件明显不支持。
- 容量不足时仍使用 `proportional_compression`，避免再做额外复杂调度层。

这套槽位规则可以跨区域复用。真正应区域化的是规格容量、允许规格和城市配置。

## 航站楼规格 catalog 的区域化

当前默认规格表：

- `empty`：设计 0m，极限 0m。
- `small`：设计 8m，极限 12m。
- `medium`：设计 16m，极限 24m。
- `large`：设计 32m，极限 45m。
- `extra_large`：设计 50m，极限 65m。
- `giant`：设计 72m，极限 90m。

后续扩展全球时，可以保留槽位角色，但拆出区域或机场类型 catalog：

- `china_mainland_terminal_sizes_v1`：大型新建机场能力偏强，可以接近当前默认表或略偏大。
- `land_constrained_terminal_sizes_v1`：土地紧约束城市使用，单槽容量较低，允许规格更保守。
- `middle_east_gulf_terminal_sizes_v1`：超级枢纽区域可让 `extra_large`、`giant` 更强。
- `north_america_distributed_terminal_sizes_v1`：单槽不一定极大，但多航站楼、多卫星厅组合能力强。
- `island_tourism_terminal_sizes_v1`：旅游岛屿或土地受限机场，容量较小但休闲和商业倾向可更高。

注意：catalog 区域化不等于槽位规则区域化。槽位角色仍可统一，容量表和允许规格可以不同。

## 特殊机场必须单独覆盖

以下机场类型不要完全套区域默认值：

- 土地极度受限：香港、澳门、新加坡、东京羽田、伦敦希思罗等。
- 单机场替换城市：如厦门翔安这类旧机场逐步退出、新机场接管。
- 多机场结构特殊：伦敦、纽约、东京、大阪、巴黎、首尔等，不一定能用简单双机场理解。
- 超级中转枢纽：迪拜、多哈、伊斯坦布尔、新加坡等，中转权重和主槽位规格要特别看。
- 旅游目的地机场：大型海岛、朝圣、滑雪、度假城市，休闲占比和季节性可能极端。
- 高原、高温、岛屿、军民合用、夜航限制机场：容量与供给能力应打折。
- 冲突或长期不稳定地区：即便城市重要，也应谨慎纳入或降低可运营性。

## 建议参数范围

这些是调参起点，不是最终标定：

- `baseline_region_demand_share_pct`
  - 超级门户城市：`8% - 16%`。
  - 国家级/区域级枢纽：`2% - 8%`。
  - 普通大城市：`0.8% - 3%`。
  - 旅游或边境节点：`0.2% - 1.5%`。
- `baseline_city_potential_passengers_million`
  - 全球级双机场城市：`80 - 140m`。
  - 大型枢纽城市：`40 - 90m`。
  - 省会/区域中心：`15 - 50m`。
  - 旅游或边境重点城市：`5 - 30m`。
- `annual_long_term_city_growth_bias_pct`
  - 成熟大城市：`-0.2% - 0.5%`。
  - 成长型大城市：`0.3% - 1.0%`。
  - 高追赶城市：`0.8% - 1.5%`，但应配上上限。
- `max_long_term_city_growth_bias_pct`
  - 成熟城市：`10% - 25%`。
  - 成长城市：`20% - 45%`。
  - 游戏样板或强政策城市：`40% - 60%`。
- `seed_potential_model.annual_growth_bias_range_pct`
  - 一线/核心门户：`-0.3% - 0.35%`。
  - 新一线/强省会：`-0.5% - 0.65%`。
  - 旅游、边疆、邻近压制城市：`-0.8% - 0.9%`。
- `seed_potential_model.max_growth_bias_range_pct`
  - 一线/核心门户：`-15% - 18%`。
  - 新一线/强省会：`-25% - 30%`。
  - 旅游、边疆、邻近压制城市：`-35% - 45%`。
- `seed_potential_model.regional_correlation_weight`
  - 建议 `0.20 - 0.40`。越高，seed 城市势能越受区域航空需求、区域 GDP、信心、压力和票价环境约束。
- 当前模板实例
  - 北京 v4：`china_core_gateway_seed_potential_v1`，核心门户窄模板，`max_growth_bias_range_pct = -12% / +15%`。
  - 青岛 v2：`china_coastal_gateway_challenger_seed_potential_v1`，沿海门户挑战者宽模板，`max_growth_bias_range_pct = -24% / +38%`。
  - 成都 v2 / 重庆 v2：`china_western_twin_hub_seed_potential_v1`，成渝双城门户中宽模板，`max_growth_bias_range_pct = -18% / +28%`。两城在代码里仍按各自 `city_airport_market_id` 独立抽样，不做显式互斥。
  - 西安 v2 / 郑州 v2 / 武汉 v2：`china_inland_hub_competitor_seed_potential_v1`，内陆枢纽竞争者中宽模板，`max_growth_bias_range_pct = -20% / +32%`。三城独立抽样，用于让西北门户、中原枢纽和中部中心在不同 seed 中自然分化。
  - 上海 v2：`china_yangtze_delta_core_gateway_seed_potential_v1`，长三角核心门户窄模板，`max_growth_bias_range_pct = -10% / +12%`，用于保留上海核心地位但允许长期强弱微调。
  - 杭州 v2 / 南京 v3：`china_yangtze_delta_secondary_gateway_seed_potential_v1`，长三角次级门户中宽模板，`max_growth_bias_range_pct = -16% / +26%`。
  - 合肥 v2：`china_yangtze_delta_inner_growth_challenger_seed_potential_v1`，长三角内陆增长挑战者模板，`max_growth_bias_range_pct = -18% / +35%`。
  - 宁波 v2 / 无锡-苏南 v2 / 温州 v2：`china_yangtze_delta_port_manufacturing_challenger_seed_potential_v1`，长三角港口制造和卫星挑战者宽模板，`max_growth_bias_range_pct = -23% / +38%`。
  - 广州 v2：`china_south_coast_core_gateway_seed_potential_v1`，华南传统核心门户窄中模板，`max_growth_bias_range_pct = -13% / +18%`。
  - 深圳 v3：`china_greater_bay_growth_gateway_seed_potential_v1`，大湾区高商务增长门户窄中偏上模板，`max_growth_bias_range_pct = -14% / +22%`。
  - 珠海 v2：`china_greater_bay_west_bank_challenger_seed_potential_v1`，大湾区西岸外溢挑战者宽模板，`max_growth_bias_range_pct = -30% / +45%`。
  - 厦门 v2 / 福州 v2：`china_fujian_dual_core_seed_potential_v1`，福建双核心中宽模板，`max_growth_bias_range_pct = -18% / +32%`。
  - 泉州-晋江 v2 / 揭阳-潮汕 v2：`china_south_coast_private_vfr_challenger_seed_potential_v1`，华南沿海民营经济和侨乡挑战者宽模板，`max_growth_bias_range_pct = -25% / +42%`。
  - 天津 v2：`china_bohai_near_capital_overflow_seed_potential_v1`，京津冀近首都外溢/压制模板，`max_growth_bias_range_pct = -24% / +36%`。
  - 石家庄 v2：`china_bohai_capital_hinterland_challenger_seed_potential_v1`，京津冀腹地低成本和外溢挑战者宽模板，`max_growth_bias_range_pct = -30% / +44%`。
  - 济南 v2：`china_shandong_inland_gateway_seed_potential_v1`，山东内陆省会门户中宽模板，`max_growth_bias_range_pct = -17% / +30%`。
  - 烟台 v2：`china_bohai_coastal_secondary_challenger_seed_potential_v1`，环渤海沿海副门户宽模板，`max_growth_bias_range_pct = -25% / +40%`。
  - 沈阳 v2 / 大连 v2：`china_northeast_recovery_gateway_seed_potential_v1`，东北恢复/承压双态门户模板，`max_growth_bias_range_pct = -24% / +38%`。
  - 昆明 v2：`china_southwest_gateway_seed_potential_v1`，西南门户和东南亚连接中宽模板，`max_growth_bias_range_pct = -16% / +28%`。
  - 贵阳 v2 / 南宁 v2：`china_southwest_mountain_regional_gateway_seed_potential_v1`，西南山地/面向东盟区域门户中宽模板，`max_growth_bias_range_pct = -20% / +34%`。
  - 桂林 v2：`china_classic_tourism_lifecycle_seed_potential_v1`，老牌旅游目的地生命周期宽模板，`max_growth_bias_range_pct = -35% / +42%`。
  - 丽江 v2 / 西双版纳 v2：`china_high_beta_tourism_destination_seed_potential_v1`，高弹性旅游目的地宽模板，`max_growth_bias_range_pct = -38% / +50%`。
  - 海口 v2：`china_hainan_island_primary_gateway_seed_potential_v1`，海南北部门户和免税入口中宽模板，`max_growth_bias_range_pct = -18% / +32%`。
  - 三亚 v2：`china_hainan_premium_tourism_destination_seed_potential_v1`，海南高端旅游目的地宽模板，`max_growth_bias_range_pct = -32% / +48%`。
  - 乌鲁木齐 v2：`china_northwest_strategic_gateway_seed_potential_v1`，西北战略远程门户中宽模板，`max_growth_bias_range_pct = -18% / +32%`。
  - 喀什 v2：`china_frontier_gateway_challenger_seed_potential_v1`，边疆战略门户挑战者宽模板，`max_growth_bias_range_pct = -34% / +48%`。
  - 兰州 v2 / 呼和浩特 v2 / 银川 v2：`china_northwest_corridor_regional_gateway_seed_potential_v1`，西北通道和区域门户中宽模板，`max_growth_bias_range_pct = -22% / +36%`。
  - 西宁 v2 / 拉萨 v2：`china_plateau_gateway_constraint_seed_potential_v1`，高原门户约束模板，`max_growth_bias_range_pct = -24% / +34%`。这里只修正潜在客流，高原运营、天气和机型约束仍由后续运营/容量层体现。
  - 长沙 v2：`china_central_growth_provincial_gateway_seed_potential_v1`，中部成长省会中宽模板，`max_growth_bias_range_pct = -18% / +30%`。
  - 南昌 v2 / 太原 v2：`china_regular_provincial_catchup_seed_potential_v1`，普通省会追赶模板，`max_growth_bias_range_pct = -22% / +34%`。
  - 哈尔滨 v2 / 长春 v2：`china_northeast_recovery_secondary_seed_potential_v1`，东北恢复/承压补充模板，`max_growth_bias_range_pct = -22% / +36%`。
  - 至此中国大陆 47 个城市机场市场全部启用 seed 势能模板。
- `regional_airline_capacity_growth_capture`
  - 普通城市：`0.15 - 0.35`。
  - 主要枢纽：`0.35 - 0.55`。
  - 超级门户/政策重点：`0.50 - 0.70`。
- 商业 bias
  - 普通城市多在 `0.85 - 1.15`。
  - 高消费/国际门户可到 `1.15 - 1.35`。
  - 极端旅游、免税或奢侈品节点再特殊覆盖。

## 与上游和下游的边界

- 上游区域航空需求决定区域潜在客流和五类客群走势。
- 上游区域航空供给决定航司可承接客流和各客群满足率。
- 城市机场客流层决定城市拿到多少客流、各类客群多少、机场容量是否压缩。
- 季度机场经营层再决定收入、成本、拥挤、商业、翻新和折旧。
- seed 城市航空势能只修正城市长期潜在客流，不直接改机场容量、航司供给、收入、成本、财务或估值。下游应通过客流自然承接变化。

不要在城市机场客流层重新发明宏观经济，也不要把季度经营成本提前塞进城市客流层。

## Seed 城市航空势能模板

`seed_potential_model` 是轻量实验层，用来解决“玩家死背现实城市强弱”的问题。

公式口径：

```text
城市潜在客流
  = 基准城市潜在客流
  * 城市固定长期增长偏置
  * seed 城市航空势能乘数
  * 五类客群指数
```

其中 seed 城市航空势能乘数由三部分组成：

```text
稳定哈希(seed, city_airport_market_id, template_id)
  -> 结构性城市动量分数
  -> annual/max 长期偏置
  -> 按 release_start/full_effect 逐年释放
  -> 用区域航空/宏观对齐分数放大或压低
```

输出字段：

- `seed_city_structural_momentum_score`：同一 seed 与城市组合的长期结构分数。
- `seed_city_regional_alignment_score`：当前年份区域航空/宏观环境对齐分数。
- `seed_city_momentum_label`：`strong_upside`、`upside`、`balanced`、`downside`、`strong_downside`。
- `seed_city_effective_bias_pct`：当年已释放且经过区域环境修正后的额外偏置。
- `seed_city_potential_multiplier`：最终乘到城市潜在客流上的乘数。

设计边界：

- 初期年份不应剧烈改变现实强弱，建议 5 年后释放，20-30 年左右进入主要效果。
- 一线/核心门户使用较窄范围；新一线、强省会、旅游和边疆门户可以更宽。
- 同一 seed 的城市长期差异应进入预测层报表解释；城市层只负责输出可解释字段。

## 航司供给波动层

v0.17 起，城市潜在客流继续作为长期慢变量；航司供给作为更快变量，可以明显强于潜在客流波动，但不应脱离需求中枢。航司供给的长期规划锚点应直接来自潜在客流对应的座位需求，而不是固定指数上限。

航司供给目标值：

```text
city_airline_supply_target_index
  = trend_index
  + demand_pull_from_potential_anchor
  + macro/appetite adjustment
  - constraint drag
  + deterministic seed cycle
  + deterministic seed shock
  + branch/event impulse
```

实际供给指数再用上一年供给做惯性调整：

```text
city_airline_supply_index
  = previous_index
  + (target_index - previous_index) * airline_supply_adjustment_speed
```

供给指数上限：

```text
city_airline_supply_ceiling_index
  = max(static_floor, city_airline_supply_potential_anchor_index * ceiling_buffer)
```

这样后期缺口可以来自航司周期、机队/信用/利润约束和恢复滞后，而不是因为固定上限把供给压成横线。

默认参数建议：

- `airline_supply_demand_pull_capture`：0.75 - 1.05。大型枢纽可偏高，小型或受限机场偏低。
- `airline_supply_cycle_amplitude_pct`：8 - 14。表达 3-8 年航司投放周期；默认应足以制造普通年份的供给过剩/不足。
- `airline_supply_shock_amplitude_pct`：6 - 12。表达机队、油价、信用、航司战略调整等冲击。
- `airline_supply_adjustment_speed`：0.50 - 0.75。越高越快追向目标，越低恢复越滞后。
- `airline_supply_volatility_bias`：0.7 - 1.3。核心稳定枢纽可低于 1，旅游和竞争型城市可高于 1。

输出解释字段包括 `city_airline_supply_potential_anchor_index`、`city_airline_supply_trend_index`、`city_airline_supply_demand_pull_pct`、`city_airline_supply_cycle_impulse_pct`、`city_airline_supply_shock_impulse_pct`、`city_airline_supply_lag_adjustment_pct`、`city_airline_supply_ceiling_index` 和 `city_airline_supply_volatility_regime`。v0.18 起还输出 `business/leisure/vfr/long_haul/transfer_airline_supply_passengers_million` 等分项供给字段：总供给不重复放大，分项只按潜在分项、航司偏好和约束重新分配。运营面板的客流容量图应同时展示潜在客流、承接客流、航司供给、设计容量和最大容量，并在客流容量下展示分项潜在与分项供给。

## 城市潜在客流预测边界

城市潜在客流预测应作为独立玩家报表层，而不是继续扩写真实城市客流层。详细计划见：

```text
airport/docs/airport_operations/City_Airport_Potential_Passenger_Forecast_System_Plan.md
```

第一版允许预测层读取隐藏真实潜在客流曲线，但必须按预测等级降质后再给玩家：

```text
玩家可见预测
  = 隐藏真实潜在客流曲线的降质版本
  + 预测滞后
  + 预测误差
  + 区间带
  + 解释标签
```

普通游戏等级：

- 初级预测：粗略行业报告或市场共识，短期可用，seed 捕捉弱，容易被现实排名和近期趋势锚定，连续窗口 6 年。
- 中级预测：内部研究 / 基础研究，能部分识别城市势能，连续窗口 8 年。
- 高级预测：高质量咨询预测，中心值和方向更可靠，连续窗口 10 年。
- 专业级预测：顶级机构 / 专业研究，普通预测上限，质量分最高 70，基本看清 seed 倾向但仍给区间和误差，连续窗口 12 年。
- 神级预测：固定 100 分，预留上帝视角、调试和玩家主动开挂，是明确的未来透视，可接近或显示隐藏真值。

`71 - 99` 不作为普通预测插值空间。神级预测必须显式标记 `future_peek_mode = true`，让普通平衡、成就或排行榜逻辑能识别它不是常规市场研究报告。

公开共识预测应保留独立来源标签 `forecast_report_source = public_consensus`。它在交易、估值和对手 AI 中代表“市场大多数人以为的未来”，但它不固定等于 18 分低级报告；在某些年份、城市和 seed 下，它可以达到 40-50 分水平。它可能准确，也可能愚蠢；这种偏差本身就是资产交易和商业情报玩法的基础。

预测区间不能用隐藏真实值作为中心生成。普通预测的 `forecast_mid` 是模型估计，不是未来真值；上下界可以不对称，隐藏真实潜在客流不应默认等于区间平均值。可见区间宽度不应成为识别报告真实质量的捷径；报告可以自信地错。高级报告的优势主要体现在中心值、方向、seed 捕捉和排序可靠性。同样分数也可以因 `forecast_bias_direction` 不同而形成过度乐观或过度悲观。

普通机构报告采用短中期连续年度预测，不应默认输出 20-30 年严肃数字曲线。当前北京样板中，初级 6 年，中级 8 年，高级 10 年，专业级 12 年；全周期只属于神级未来透视、沙盒或调试模式。

报告等级和事后审计分需要分开。`forecast_report_tier` 决定报告窗口和生成权限；`realized_report_quality_score` 是报告输出后，对比隐藏真实 seed 曲线得到的 0-100 分。初级报告也可能在 6 年窗口内拿高分，专业级报告也可能在 12 年窗口内因为偏乐观、偏悲观或区间失准而低分。这个审计分适合后续接机构声誉、研究所、商业情报和市场共识误判。

边界：

- 预测层只负责玩家能看到的未来城市航空盘子，不改变真实客流。
- 下游经营、商业合同和估值只能读取玩家可见预测，不能直接读取隐藏真实未来。
- 承接客流预测必须重新叠加玩家当前和计划中的容量、航司供给和拥挤规则，不能直接拿真实未来承接客流。

## 后续扩展顺序

1. 先为每个区域建立城市客流默认模板。
2. 再决定是否需要区域化 terminal size catalog。
3. 然后批量写城市机场名单和槽位配置。
4. 最后对特殊机场做覆盖。
5. 跑同一 seed 和历史岔路路径，检查城市客流是否沿上游路径变化。

这个顺序比逐个城市手搓更稳，也方便后续回看为什么某个区域机场容量偏大或偏小。
