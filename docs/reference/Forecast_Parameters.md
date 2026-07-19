# 客流预测报告参数

## 1. 参数职责

北京客流预测由三层配置共同决定：

```text
报告等级模板
  + 研究叙事模板
  + 0～2 个行为修饰标签
  + 北京报告身份与期限
```

等级模板只规定研究能力边界；叙事模板规定怎样理解需求、供给和周期；修饰标签只做受控小幅调整。北京配置选择这些共享模板，不把完整预测行为复制到城市 JSON。

## 2. 配置位置

| 文件 | 作用 |
| --- | --- |
| [`forecast_report_tier_profiles_v1.json`](../../config/forecast_report_tier_profiles/forecast_report_tier_profiles_v1.json) | 初级、中级、高级、专业级和神级能力边界 |
| [`forecast_narrative_profiles_v2.json`](../../config/forecast_narrative_profiles/forecast_narrative_profiles_v2.json) | 8 种普通研究风格、真实路径与分类修饰标签 |
| [`beijing_airport_system_potential_passenger_forecast_v1.json`](../../config/city_airport_potential_passenger_forecast/beijing_airport_system_potential_passenger_forecast_v1.json) | 北京的 13 份报告、期限、区间和显示身份 |
| [`forecast-config.schema.json`](../../schemas/forecast-config.schema.json) | 城市预测配置允许的正式字段；拒绝旧滞后参数和未知键 |
| [`forecast-tier-catalog.schema.json`](../../schemas/forecast-tier-catalog.schema.json) | 等级目录结构和候选生成能力范围 |
| [`forecast-narrative-catalog.schema.json`](../../schemas/forecast-narrative-catalog.schema.json) | 基础风格、修饰标签和允许调整的参数 |

城市配置必须显式引用：

- `forecast_report_tier_catalog`；
- `forecast_narrative_catalog`；
- `forecast_report_tier_profile_id`；
- `forecast_narrative_profile_id`；
- `forecast_narrative_modifier_ids`。

一份报告最多使用两个修饰标签。未知模板、重复报告 ID 或超过两个标签会在配置加载时失败。

## 3. 等级模板

等级模板的关键字段：

| 字段 | 含义 |
| --- | --- |
| `signal_observation_quality` | 对模糊未来信号的基础识别能力 |
| `signal_miss_rate` | 漏掉方向或拐点信号的概率边界 |
| `signal_misclassification_rate` | 把信号强弱判断错一档的概率边界 |
| `turn_window_error_years` | 预期拐点窗口允许的年份误差 |
| `component_signal_quality` | 五类客群结构变化识别能力 |
| `max_annual_growth_change_pp` | 无额外叙事时相邻年度预测增速的最大变化 |
| `max_unexplained_inflections` | 报告允许的无依据反复转向数量 |
| `base_revision_speed` | 连续报告吸收新信息的基础速度 |
| `base_reversal_threshold` | 放弃上一期核心观点所需的证据门槛 |

普通报告的实际信号能力还会结合该期 `forecast_quality_score`。神级模板不做信号降级，仅用于开发审计。

## 4. 基础研究风格

基础风格表示“报告主要使用什么方法理解市场”，不能由乐观、悲观或快速修订等行为标签完全替代。当前普通报告共享 8 种方法：

| 基础风格 | 核心方法 | 典型盲点 |
| --- | --- | --- |
| 公开共识 | 公开资料、近期趋势与市场平均预期 | 非共识拐点反应慢 |
| 增长叙事 | 近期增长外推与城市上行故事 | 低估供给约束和成熟期回落 |
| 基本面研究 | 城市需求结构与长期增长锚 | 短期周期反应偏慢 |
| 平衡基准 | 需求、供给和长期趋势综合 | 观点折中，提前判断不足 |
| 定量周期模型 | 航司供给惯性和周期拐点 | 低估难量化事件 |
| 保守情景 | 下行尾部、约束与风险缓冲 | 容易长期低估增长 |
| 宏观航研 | 宏观周期和区域航空景气 | 忽略城市自身结构 |
| 逆向研究 | 反共识验证和拐点搜索 | 可能过早逆势 |

`真实路径` 是第 9 个目录项，只用于神级开发审计，不属于普通研究风格。

基础风格的关键字段：

| 字段 | 含义 |
| --- | --- |
| `narrative_demand_signal_weight` | 城市需求方向对路径的影响 |
| `narrative_supply_signal_weight` | 航司供给方向对路径的影响 |
| `narrative_trend_extrapolation` | 延续近期趋势的倾向 |
| `narrative_mean_reversion` | 回归长期成熟增速的倾向 |
| `narrative_turn_sensitivity` | 对供需周期转向的反应强度 |
| `narrative_thesis_persistence` | 继承上一期观点的倾向 |
| `narrative_revision_speed` | 新证据出现后修改旧路径的速度 |
| `narrative_growth_bias_pct` | 潜在需求年度增速的小幅风格偏向 |
| `narrative_supply_bias_pct` | 航司供给年度增速的小幅风格偏向 |
| `narrative_interval_multiplier` | 对基础预测区间宽度的调整 |

## 5. 修饰标签

标签只描述报告在基础方法上的倾向，每份报告最多两个。当前 15 个标签分成四组：

| 分类 | 标签 |
| --- | --- |
| 立场 | 偏乐观、偏谨慎 |
| 方法侧重 | 趋势追随、均值回归、供给敏感、宏观敏感、客群敏感、风险敏感、拐点敏感 |
| 修订行为 | 共识跟随、观点粘性、慢速修订、快速修订 |
| 不确定性 | 区间偏窄、宽幅区间 |

每个标签同时配置：

- `modifier_label`：界面中文名称；
- `modifier_group`：标签分类；
- `modifier_description`：标签怎样影响报告；
- `modifier_tradeoff`：该倾向可能付出的代价；
- `parameter_deltas` 或 `parameter_multipliers`：受控参数变化。

界面显示中文标签和分类，鼠标悬停可查看作用与代价。技术 ID 只用于配置和测试。

## 6. 北京 13 份报告

| 可见标题 | 等级 | 修饰标签 |
| --- | --- | --- |
| 公开共识 | 初级 | 共识跟随、观点粘性 |
| 公开共识 | 初级 | 偏谨慎、慢速修订 |
| 增长叙事 | 初级 | 趋势追随、区间偏窄 |
| 基本面研究 | 中级 | 均值回归、宽区间 |
| 平衡基准 | 中级 | 宽幅区间 |
| 基本面研究 | 中级 | 偏乐观、趋势追随 |
| 平衡基准 | 高级 | 宽幅区间 |
| 定量周期模型 | 高级 | 供给敏感、快速修订 |
| 保守情景 | 高级 | 风险敏感 |
| 平衡基准 | 专业级 | 供给敏感、客群敏感 |
| 宏观航研 | 专业级 | 宏观敏感、慢速修订 |
| 逆向研究 | 专业级 | 拐点敏感 |
| 真实路径 | 开发审计 | 无；开发审计专用 |

界面标题统一显示为“等级 · 研究风格”，例如“初级 · 公开共识”和“高级 · 定量周期模型”。原来的“地方简报、咨询基准、顶级机构”等报告名称不再面向玩家展示；修饰标签用于说明同一等级和风格内部的行为差异。

这里有意允许多份报告共享同一个可见标题：

- 两份“公开共识”由立场和修订标签区分；
- 两份“基本面研究”由偏乐观和趋势追随等标签区分；
- 三份“平衡基准”由等级和方法侧重区分。

前 12 份进入玩家报告索引。神级报告只进入独立开发审计索引。

## 7. 五类客群预测

总潜在需求和总航司计划投放仍是报告的权威总量路径。普通报告另外预测两组会随期限变化并继承上一期观点的结构：

- 商务、休闲、探亲访友、长途和中转的潜在需求占比；
- 航司对五类客群的相对优先权重。

每个目标年先用需求占比拆出五类潜在需求，再把潜在需求、优先权重和总计划投放交给与城市年度市场相同的封顶分配函数。五类“计划投放”是按优先权重形成的第一轮分配；若某类需求先达到上限，剩余运力会继续分给其他未满足客群，形成最终有效供给、满足率和未满足需求。因此单类有效供给可以高于该类第一轮计划投放，但不会超过其潜在需求。预测层不读取机场容量，分项城市有效客流等于该客群航司有效供给。

必须保持：

```text
五类潜在需求之和 = 总潜在需求
五类计划投放之和 = 总航司计划投放
单客群有效供给 <= 单客群潜在需求
五类有效供给之和 = min(总潜在需求, 总航司计划投放)
```

普通报告只观察被降级后的客群需求方向和航司优先权重方向，不能读取未来精确分项数值。`客群敏感` 同时改善两类结构观察，`供给敏感` 主要改善航司分配判断，趋势、均值回归、修订和区间标签继续作用于对应的分项路径。偏乐观或偏谨慎主要影响总量，不会硬编码某一客群必然受益。

分项有效客流区间同时包含总量误差和客群份额误差。它是单客群边际区间；五个客群的上限代表不同边际情景，不能直接相加。

## 8. 实际评分标准

开发审计使用 `narrative-passenger-realized-score-v1.2`。等级、标题和报告价格不直接进入实际评分；评分只比较报告输出、后续修订和隐藏真实路径。

实际评分满分 100 分：

| 部分 | 权重 | 内容 |
| --- | ---: | --- |
| 总量结果 | 70% | 中值 30%、趋势 12%、形状 8%、供需瓶颈 5%、总量区间 15% |
| 分项结果 | 15% | 潜在需求结构 4%、航司有效供给结构 5%、供给满足率差异 3%、分项区间 3% |
| 报告过程 | 15% | 拐点判断 8%、修订纪律 7% |

界面中的“结果分”只包含预测路径和区间校准。两部分合计权重为 85%，显示时重新归一化到 0～100：

```text
结果分
  =（总量结果 70 分 + 分项结果 15 分）÷ 85%

实际评分
  = 结果分 × 85%
  + 拐点判断分 × 8%
  + 修订纪律分 × 7%
```

潜在需求结构和航司供给结构比较占比误差，避免把总量误差重复处罚；满足率分专门评价报告是否识别出商务保护、休闲挤出等结构差异。修订纪律内部按总量 80%、分项结构 20% 合成。开发审计同时展示总量分、分项分和四个分项子分。

`真实路径` 直接读取隐藏未来，底层保持 100 分用于校验评分链路；界面显示“审计基准 · 不参与评分”。

## 9. 开发审计候选报告生成器

`audit-forecast-candidate-generator-v2` 只在开发审计中使用。输入绑定页面明确的 Viewer Release 或有效 Seed 缓存来源，并包含世界 Seed、年数、发布年份、一个等级模板、一个基础风格、标签模式、实际评分目标范围和生成编号。生成器最多搜索 48 个独立首次发布候选，使用同一 `narrative-passenger-realized-score-v1.2` 评分；命中目标范围时返回最接近区间中心的候选，无法命中时返回最近候选并明确标记，不会静默扩大范围。结果卡同时显示总量结果分和分项结果分。

普通基础风格固定为 8 种，每份候选只能选择其中一种。`auto` 可从该风格的 `candidate_modifier_ids` 中附加 0～2 个兼容标签，`pure` 不附加标签，`manual` 接受 0～2 个手动标签。偏乐观/偏谨慎、趋势追随/均值回归、快速/慢速修订、窄/宽区间不能成对出现。

候选等级的能力范围和自然预测期显式写在等级模板的 `candidate_generation` 中：初级 6 年、中级 8 年、高级 10 年、专业级 12 年。发布年份加自然期限超过正式数据终点时禁止生成目标分候选，不能截短期限后继续搜索。

候选是一份独立首次发布报告，因此修订原因为 `initial_report`，修订纪律分统一为 92。候选由世界 Seed、发布年份、等级、风格、标签、`generationNonce` 和配置版本共同决定；同样输入必须完全复现。“换一份”只增加生成编号。候选响应仅存在于当前页面，不写入正式 Viewer 分块、玩家报告、Run、缓存或存档。

## 10. 实现与数据协议

稳定入口仍是 [`city_airport_potential_passenger_forecast_layer_sim.py`](../../macro_layers/city_airport_potential_passenger_forecast_layer_sim.py)。为了避免单文件再次堆叠，它只保留预测路径、CSV 契约、兼容转发和命令入口；内部职责拆分为：

| 模块 | 唯一职责 |
| --- | --- |
| [`profile_config.py`](../../macro_layers/forecast_system/profile_config.py) | 加载城市配置、等级目录、风格目录和标签覆盖 |
| [`scoring.py`](../../macro_layers/forecast_system/scoring.py) | 事后评分、总量/分项权重和修订纪律 |
| [`candidate_generator.py`](../../macro_layers/forecast_system/candidate_generator.py) | 开发审计候选组合、目标分搜索和期限校验 |
| [`viewer_assets.py`](../../macro_layers/forecast_system/viewer_assets.py) | 玩家/审计字段投影、报告分块、索引和哈希 |

外部模块继续从稳定入口调用 `load_config`、`simulate_potential_passenger_forecast`、`generate_forecast_candidate` 和 `write_viewer_lazy_assets`，不直接依赖内部文件布局。

预测 Viewer 只发布轻量索引和按报告分块：

```text
<market_id>_forecast_index.js
<market_id>_forecast_chunks/r_<report_id>.json
<market_id>_forecast_audit_index.js
<market_id>_audit_forecast_chunks/r_<report_id>.json
```

玩家投影不含 `debug_*`、`realized_*` 和神级报告；审计投影在玩家字段基础上显式加入隐藏真值、信号与评分拆解。旧 `forecast_lag_years` 和 `lagged_hidden_curve_*` 只暂留在 CSV 兼容协议中，不进入任何浏览器分块。生成器、release 和 canonical 均不再创建完整预测 JS；页面缺少轻量索引时直接报发布不完整，不会退回另一套数据路径。

## 11. 调参边界

普通报告不能通过配置直接获得目标年份的真实潜在客流、真实航司供给、真实有效客流或真实客群数值。未来真实路径只会先被压缩成：

- 需求方向与强弱等级；
- 航司供给方向与强弱等级；
- 模糊拐点窗口和加速/减速类别；
- 五类潜在需求份额上升、稳定或下降；
- 五类航司优先权重增强、稳定或减弱；
- 信号可信度。

若两条隐藏路径的精确数值不同但信号分类相同，普通报告在同一 `as-of` 应得到相同预测路径。神级报告是唯一例外。

修改这些参数属于模型行为变更，应同步升级预测版本、运行固定 Seed 与 60 年测试，并重新发布 Viewer。
