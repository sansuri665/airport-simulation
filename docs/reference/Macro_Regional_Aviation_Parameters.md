# 宏观、区域、航空与城市市场参数参考

## 如何使用这份参考

本页记录当前正式 Run 真正读取的参数入口、默认值、当前配置范围和代码硬边界。它不是另一份配置文件：发生冲突时，以代码、JSON 和测试为准。

表中三种“范围”不要混淆：

- **默认值**：正式命令不传参数时实际使用的值。
- **当前配置范围**：14 区或 47 城现有配置中的最小值和最大值，不表示代码只允许这些值。
- **硬边界**：公式中的 `clamp` 或最低/最高值；超出后会被截断。

## 单位速查

| 后缀或名称 | 单位/含义 |
| --- | --- |
| `_pct` | 百分比；增长、通胀和利率通常是年率 |
| `_pp` | 百分点差。例如 2% 到 3% 是 +1 pp |
| `_bps` | 基点；100 bps = 1 个百分点 |
| `_trillion_usd` | 万亿美元 |
| `_million` | 百万人次 |
| `_index` | 模型内部无量纲指数；必须按字段自己的基准解释 |
| `_weight`、`_sensitivity`、`_beta` | 公式系数，不是概率 |
| `*_chance_per_year` | 每年随机触发概率，0.05 表示 5% |

## 1. 正式 Run 的外部参数

这些参数可直接通过 `py -3.13 -m airport_sim run` 调整，解析和默认值来自 [`macro_run_orchestrator_sim.py`](../../macro_layers/macro_run_orchestrator_sim.py)。

| 命令参数 | 默认值 | 影响 | 约束说明 |
| --- | ---: | --- | --- |
| `--seed` | 随机 | 整条全球—区域—城市路径 | 固定整数即可复现 |
| `--start-year` | 2025 | 日历标签 | 不改变公式结构 |
| `--years` | 60 | 模拟跨度 | manifest 要求至少 1；输出行数为 `years + 1` |
| `--initial-gdp` | 100.0 | 起始全球 GDP | 万亿美元；CLI 未设硬上限，应保持正值 |
| `--volatility-scale` | 1.0 | GDP 周期和冲击整体波动 | CLI 未设硬边界，过大时大量变量会撞到各层截断值 |
| `--feedback-iterations` | 3 | 滞后反馈回跑次数 | 正式 manifest 要求至少 1 |
| `--scenario-state` | `none` | 是否生成第二条岔路 | `occurred`、`counterfactual`、`probabilistic` |
| `--scenario-branch-id` | `auto` | 手动岔路类型 | 必须是当前支持的风险 ID |
| `--scenario-year` / `--scenario-year-index` | 自动 | 岔路触发时间 | 二选一即可；不能超出时间轴 |
| `--artifact-profile` | `full` | 输出 Viewer 还是仅 Seed 缓存所需数据 | `seed-cache` 不能同时发布 Viewer |

改参数前，先固定 seed；否则“参数影响”和“随机世界变化”无法区分。

## 2. 全球宏观参数

正式 Run 不是直接使用所有 dataclass 的原始默认值。它通过 `build_global_params()` 组合校准参数，因此应从 [`global_macro_feedback_calibration_sim.py`](../../macro_layers/global_macro_feedback_calibration_sim.py) 和 [`regional_macro_layer_sim.py`](../../macro_layers/regional_macro_layer_sim.py) 中的 `build_global_params()` 一起核对。

### 当前关键值和硬边界

| 参数族 | 当前正式值 | 主要硬边界 |
| --- | --- | --- |
| GDP 趋势 | 起始 2.75%，长期目标 1.75% | 实际增长 -8.5%–9.5%；产出缺口约束在 ±13.5% |
| GDP 冲击 | `volatility_scale=1.0`；危机时代年概率 4.2%；繁荣年概率 6.0% | 多个周期/冲击分量另有内部截断 |
| 通胀锚 | 总体 2.45%，核心 2.30%，预期 2.35% | 总体 -1.5%–9.5%；核心 -0.5%–7.0% |
| 政策利率 | 初始 3.25%；调整速度 0.34 | 0.05%–8.5%；普通单年最多加 1.10 pp、降 1.45 pp |
| 10 年收益率 | 初始 4.05% | 所有模型收益率 -0.35%–10.5% |
| 美元/流动性 | 美元 100、流动性 55、风险偏好 50 | 美元 82–124；流动性和风险偏好 0–100 |
| 投资级利差 | 初始 115 bps | 35–650 bps |
| 高收益利差 | 初始 420 bps | 150–2200 bps |
| 股票估值 | 初始股票指数 100；基础 P/E 21.5 | P/E 8.5–32.0 |
| Brent | 初始 82 美元/桶 | 18 美元/桶下限；代码未设固定价格上限，但回报和高价重力有限制 |
| 宏观反馈 | 滞后 1 年、3 次回跑、每次松弛 0.25 | 增长冲量 -1.15–0.85 pp；通胀 -1.00–1.35 pp；政策 -1.00–1.25 pp |

### 参数位置

- GDP：[`global_gdp_annual_sim.py`](../../macro_layers/global_gdp_annual_sim.py) 的 `GDPParams`
- 通胀：[`global_inflation_annual_sim.py`](../../macro_layers/global_inflation_annual_sim.py) 的 `InflationParams`
- 政策：[`global_policy_rate_layer_sim.py`](../../macro_layers/global_policy_rate_layer_sim.py) 的 `PolicyRateParams`
- 收益率：[`global_yield_curve_layer_sim.py`](../../macro_layers/global_yield_curve_layer_sim.py) 的 `YieldCurveParams`
- 美元流动性：[`global_dollar_liquidity_layer_sim.py`](../../macro_layers/global_dollar_liquidity_layer_sim.py) 的 `DollarLiquidityParams`
- 信用：[`global_credit_spread_layer_sim.py`](../../macro_layers/global_credit_spread_layer_sim.py) 的 `CreditSpreadParams`
- 资产：[`global_asset_price_layer_sim.py`](../../macro_layers/global_asset_price_layer_sim.py) 的 `AssetPriceParams`
- 油价：[`global_oil_commodity_layer_sim.py`](../../macro_layers/global_oil_commodity_layer_sim.py) 的 `OilCommodityParams`
- 反馈和风险评分：[`global_macro_feedback_calibration_sim.py`](../../macro_layers/global_macro_feedback_calibration_sim.py)
- 正式组合值、岔路强度：[`macro_run_orchestrator_sim.py`](../../macro_layers/macro_run_orchestrator_sim.py)

修改顺序应先从趋势、锚和总体波动开始，再碰各类 `beta` 和反馈强度。多个传导系数同时变化时，很难判断结果来自哪一层。

## 3. 区域宏观参数

14 区参数位于 [`regional_macro_layer_sim.py`](../../macro_layers/regional_macro_layer_sim.py) 的 `REGION_CONFIGS`，当前不是 JSON。以下是代码当前配置的实际范围：

| 参数 | 当前配置范围 | 含义 |
| --- | ---: | --- |
| `global_weight` | 0.022–0.285 | 初始相对体量；14 项会统一归一化 |
| `trend_growth_pct` | 1.05%–5.25% | 区域长期增长骨架 |
| `potential_growth_floor_pct` | -0.10%–2.20% | 各区潜在增长下限的跨区范围 |
| `potential_growth_ceiling_pct` | 2.40%–7.30% | 各区潜在增长上限的跨区范围 |
| `income_level_index` | 24–88 | 区域初始收入层级指数 |
| `market_maturity` | 0.32–0.93 | 市场成熟度系数 |
| `domestic_demand_weight` | 0.55–0.89 | 国内需求支撑 |
| `international_exposure` | 0.42–0.88 | 国际周期暴露 |
| `tourism_exposure` | 0.28–0.86 | 旅游暴露 |
| `business_exposure` | 0.26–0.78 | 商务活动暴露 |
| `oil_sensitivity` | 0.56–1.08 | 油价/能源传导 |
| `dollar_sensitivity` | -0.12–1.38 | 美元传导；允许负值 |
| `credit_sensitivity` | 0.88–1.34 | 信用紧缩传导 |
| `equity_wealth_sensitivity` | 0.28–1.18 | 资产财富效应 |
| `policy_rate_sensitivity` | 0.72–1.12 | 全球政策利率传导 |
| `geopolitical_sensitivity` | 0.30–0.92 | 地缘冲击传导 |
| `shock_volatility` | 0.24–0.54 | 区域随机扰动尺度 |

`REGIONAL_SEED_POTENTIALS` 为 14 区各提供一个结构势能模板。当前全部从第 4 年度索引开始释放，第 34 年度索引达到完整效果；年度增长偏移的跨区总范围为 -1.65 pp 到 +1.90 pp，航空倾向偏移的跨区总范围为 -18% 到 +25%。这些范围属于 seed 长期分化，不应当成短期事件冲击。

对账参数位于 [`regional_macro_reconciliation_sim.py`](../../macro_layers/regional_macro_reconciliation_sim.py)。GDP 体量使用共同缩放因子精确对账；其他指标的单年共同调整硬边界包括：

| 指标 | 调整上限 |
| --- | ---: |
| 总体通胀 | ±0.45 pp |
| 核心通胀 | ±0.35 pp |
| 政策利率 | ±0.35 pp |
| 10 年收益率 | ±0.45 pp |
| 高收益利差 | ±75 bps |
| 投资级利差 | ±25 bps |
| 宏观压力 | ±30 指数点 |
| 股票回报 | ±4 pp |
| 股票 P/E | ±2.5 |
| 能源成本压力 | ±8 指数点 |

共同偏移不是最终字段边界。偏移应用到每个区域后，对账层会再次使用区域原始层的同一套边界裁剪通胀、政策利率、10 年期收益率、信用利差、宏观压力、股票回报/估值和能源成本。诊断文件记录请求调整量、裁剪后的真实加权残差、各字段裁剪区域数和总裁剪次数；不会为了消除残差而把已经触及边界的区域继续向外推。

不要通过放大对账上限来修复单个区域路径；先检查该区的增长骨架和传导敏感度。

## 4. 区域航空需求参数

14 区参数位于 [`regional_aviation_demand_layer_sim.py`](../../macro_layers/regional_aviation_demand_layer_sim.py) 的 `AVIATION_REGION_CONFIGS`。

| 参数 | 当前配置范围 | 说明 |
| --- | ---: | --- |
| 商务权重 | 0.11–0.32 | 五类权重在每区都合计为 1 |
| 休闲权重 | 0.20–0.54 | 同上 |
| 探亲访友权重 | 0.10–0.36 | 同上 |
| 长航程权重 | 0.06–0.22 | 同上 |
| 中转权重 | 0.06–0.24 | 同上 |
| `domestic_market_depth` | 0.38–0.95 | 国内市场深度 |
| `international_exposure` | 0.38–0.92 | 国际需求暴露 |
| `tourism_exposure` | 0.30–0.88 | 旅游需求暴露 |
| `income_sensitivity` | 0.66–1.05 | 收入变化对旅行的放大系数 |
| `price_sensitivity_base` | 40–66 | 票价敏感基础指数 |
| `oil_fare_sensitivity` | 0.46–0.78 | 能源向票价压力传导 |
| `currency_travel_sensitivity` | 0.24–0.82 | 汇率压力对旅行的传导 |
| `premium_mix_base` | 1.5–26.0 | 高端客群基础份额口径 |
| 免税/奢侈品/电子亲和系数 | 0.26–0.92 | 三组参数合并后的跨区范围 |
| `demand_growth_persistence` | 0.55 | 上年客群增长惯性 |
| `demand_adjustment_speed` | 0.32–0.45 | 向本年目标增长靠拢速度 |

主要输出硬边界：票价敏感指数 18–88，票价压力 20–95，高端旅客份额 5%–45%。五类客群的年度原始增长也分别有上限；例如商务 -9%–10.5%，休闲 -10%–12%，长航程 -11%–12.5%。

五类权重一旦不再合计为 1，总需求指数的“100 点起点”就会改变。修改客群结构时应整体重分配，而不是只提高某一项。

## 5. 区域航司供给参数

14 区参数位于 [`regional_air_capacity_supply_layer_sim.py`](../../macro_layers/regional_air_capacity_supply_layer_sim.py) 的 `AIR_SUPPLY_REGION_CONFIGS`。

| 参数 | 当前配置范围 | 说明 |
| --- | ---: | --- |
| `baseline_region_passenger_demand_million` | 165–1200 | 区域潜在客流的百万人次体量锚 |
| `baseline_load_factor_pct` | 81.5%–84.0% | 初始载客率，也是运力指数换算计划座位的基准 |
| `base_air_capacity_index` | 100 | 初始运力指数 |
| 国内供给深度 | 0.32–0.94 | 国内航司网络承接能力 |
| 国际供给灵活度 | 0.48–0.94 | 国际运力调整能力 |
| 中转优先级 | 0.28–0.88 | 紧张时对中转的保护程度 |
| 时刻约束基础 | 22–44 | 区域层的机场时刻压力 |
| 机队交付约束基础 | 18–34 | 机队扩张压力 |
| 人员约束基础 | 20–32 | 机组人员压力 |
| 维修成本压力基础 | 20–31 | 维修与能源成本压力 |
| `supply_growth_persistence` | 0.30–0.50 | 运力增长惯性 |
| `supply_adjustment_speed` | 0.38–0.62 | 追向目标增长的速度 |
| `max_capacity_growth_pct` | 3.6%–6.7% | 各区年度扩张上限 |
| `max_capacity_contraction_pct` | 1.2%–7.0% | 各区年度收缩绝对上限 |
| 商务挤出权重 | 0.24–0.62 | 越低越受保护 |
| 休闲挤出权重 | 1.20–1.92 | 越高越容易被挤出 |

主要输出边界：`normalized_capacity_pressure_index` 为 45–145，目标载客率为 58%–97.5%，容量票价压力为 20–98。区域参考满足率由“参考承接量 ÷ 潜在量”得到，不再设置人为 68% 下限。客群满足率仍有不同下限：商务 72%、休闲 48%、探亲访友 58%、长航程和中转 52%。这些边界是当前稳定性保护，修改它们会直接改变极端短缺的形态。

区域层的计划座位、可运营座位、参考有效承接能力及参考承接/未满足量用于区域对账和解释。城市市场不会按这些百万人次数量分配客流，也不会受它们硬性封顶；城市只读取区域运力指数、信心、扩张意愿、成本和约束压力等信号。兼容字段 `served_passengers_million` 与 `unmet_passengers_million` 当前分别等于新的参考字段。

## 6. 城市机场市场参数

城市公式位于 [`city_airport_market_demand_layer_sim.py`](../../macro_layers/city_airport_market_demand_layer_sim.py)，47 个当前配置位于 [`config/city_airport_markets/china_mainland/`](../../config/city_airport_markets/china_mainland/)。以下是加载后参数的实际范围：

| 参数 | 当前配置范围 | 说明 |
| --- | ---: | --- |
| `baseline_region_demand_share_pct` | 0.9%–15.0% | 区域份额参考/诊断，不直接分配区域客流 |
| `baseline_city_potential_passengers_million` | 7.4–126.0 | 城市潜在客流起始锚 |
| `annual_long_term_city_growth_bias_pct` | 0.48%–0.76% | 每年逐步释放的固定城市增长偏置 |
| `max_long_term_city_growth_bias_pct` | 25%–46% | 固定偏置累计上限 |
| `base_airline_supply_passengers_million` | 7.8–132.0 | 城市航司供给体量锚 |
| `regional_airline_capacity_growth_capture` | 0.20–0.44 | 捕获区域运力增长的程度 |
| `annual_local_airline_supply_growth_pct` | 0.17%–0.32% | 本地运力趋势 |
| `max_local_airline_supply_growth_pct` | 11%–25% | 本地趋势累计上限 |
| `demand_pull_capture` | 0.87–0.95 | 航司供给追随城市需求目标的强度 |
| 平衡期调整速度 | 0.31–0.42 | 正常年份追向基本面的速度 |
| 扩张期调整速度 | 0.29–0.44 | 扩张通常慢于削减，旅游城市更积极 |
| 收缩期调整速度 | 0.50–0.77 | 悲观和压力下削减供给的速度 |
| 恢复期调整速度 | 0.19–0.34 | 低谷后恢复供给的速度 |
| `overexpansion_bias_pct` | 5.0%–16.0% | 乐观期允许高于正常基本面的目标偏差 |
| `overcapacity_target_pct` | 3.5%–15.5% | 过热期相对城市潜在客流的显式目标过剩率 |
| `pessimism_bias_pct` | 4.5%–15.0% | 悲观期允许低于正常基本面的目标偏差 |
| 扩张/收缩触发阈值 | 2.0%–4.0% / 1.9%–3.5% | 供需和压力信号触发阶段转换的门槛 |
| `minimum_supply_index` | 58–72 | 城市类型和特征决定的供给底线 |
| `shock_amplitude_pct` | 7.0%–15.0% | Seed 随机供给冲击振幅 |
| `phase_persistence` | 0.95–1.17 | 阶段持续时间倾向 |
| `upward_change_limit_pct` | 7.0%–15.0% | 单年供给指数最多上调多少个点 |
| `downward_change_limit_pct` | 9.0%–19.0% | 单年供给指数最多下调多少个点 |
| seed 释放开始/完全生效 | 第 4–5 年 / 第 25–30 年 | 47 城均已启用 |
| seed 区域相关权重 | 0.28–0.32 | 城市势能与区域环境的对齐强度 |
| seed 潜力乘数下限 | 0.62–0.90 | 各城市模板的下限范围 |
| seed 潜力乘数上限 | 1.12–1.50 | 各城市模板的上限范围 |

城市航司供给行为配置位于 [`china_city_airline_supply_behavior_profiles_v2.json`](../../config/airline_supply_dynamics_profiles/china_city_airline_supply_behavior_profiles_v2.json)。47 城显式选择四种基础行为：全球枢纽 2 城、国家门户 6 城、区域门户 20 城、次级门户 19 城。另有 7 城叠加旅游暴露、2 城叠加战略支撑、2 城叠加高原约束。特征与基础门户类型可以并存，避免把昆明、厦门、海口等混合型城市强行塞进单一互斥模板。

供给周期不再使用固定双正弦波。每轮依次经历平衡、扩张、过度扩张、收缩、低谷和恢复；过度扩张通常持续 2–4 年，其它阶段通常持续 1–7 年，完整周期由 Seed、供需信号和冲击共同决定。随机冲击候选数量、时点、方向、宽度和幅度也由城市 ID 与 Seed 决定，不再固定为每城三次。过剩投放只形成 `unused_capacity`，不会突破潜在客流或凭空增加机场承接量。

单城覆盖写在 `airline_supply_model.dynamics_overrides`，只允许行为模板的有效字段。应优先复用基础模板和特征，只有存在城市级证据时才覆盖；加载器会拒绝未知字段和越界数值。

五类航司供给分配另有共享模板目录 [`china_city_component_allocation_profiles_v1.json`](../../config/airline_supply_component_allocation_profiles/china_city_component_allocation_profiles_v1.json)。未配置城市默认使用 `china_balanced_city_v1`，五类静态偏置均为 1；北京使用 `china_dual_hub_v1` 并叠加单城微调，加载后的静态偏置依次为商务 1.0403、休闲 0.9702、探亲访友 1.0000、长途 1.0302、中转 1.0302。这些数还会乘每年动态航司和宏观权重，不能直接解释成固定客群份额。

所有城市当前都使用 [`standard_terminal_sizes_v1.json`](../../config/facility_size_catalogs/standard_terminal_sizes_v1.json)：

| 规格 | 设计容量 | 极限容量 |
| --- | ---: | ---: |
| `empty` | 0 | 0 |
| `small` | 8 | 12 |
| `medium` | 16 | 24 |
| `large` | 32 | 45 |
| `extra_large` | 50 | 65 |
| `giant` | 72 | 90 |

单位为百万人次/年。机场槽位角色限制了可选规格；中国大陆的 3/4/5 槽位机场还会验证固定角色模板。

城市 JSON 中的 `schema_version` 目前只用于加载筛选。`py -3.13 -m airport_sim validate-config` 只检查 JSON 语法和重复键；完整字段、规格和槽位语义要在模型加载及测试中才能验证。

## 7. 参数影响链

| 修改对象 | 首先改变 | 随后影响 |
| --- | --- | --- |
| 全球趋势/波动/反馈 | 全球增长、通胀、利率和压力 | 所有区域、航空和城市 |
| 单区增长与敏感度 | 该区宏观及对账份额 | 该区航空和区内城市 |
| 区域航空客群权重 | 区域需求结构 | 城市客群、商业倾向 |
| 区域供给调整/约束 | 区域航司满足率 | 城市航司环境和客群供给 |
| 城市潜在客流参数 | 单城需求 | 单城缺口、拥挤和下游经营 |
| 城市航司供给参数 | 单城可承接座位 | 航司瓶颈和分项满足率 |
| 航站楼规格/开放年份 | 设计和极限容量 | 机场瓶颈、拥挤、承接客流 |

区域航司供给与城市机场容量是两道不同约束。不要用扩大航站楼容量去修复区域航司运力，也不要用区域运力参数掩盖单城设施不足。

## 8. 修改后的最低验证

按同一个固定 seed 比较修改前后，并至少检查一条基准路径和一条有压力的岔路：

```powershell
py -3.13 -m airport_sim validate-config
py -3.13 -m unittest tests.test_safety_baseline
py -3.13 -m unittest tests.test_long_horizon_contract
py -3.13 -m unittest discover -s tests -p "test_*.py"
```

检查结果时不要只看程序是否完成，还要确认：

- 60 年 Run 仍是 61 个年度点，14 区和 47 城没有缺行；
- 14 区对账后 GDP 精确等于全球 GDP，软对账缺口没有持续恶化；
- 没有大量变量长期贴着硬边界；
- 航空五类份额分别合计为 100%；
- 潜在客流、航司供给、机场容量和承接客流的大小关系可解释；
- 同一个 seed 重跑结果一致；
- 修改输出字段时同步更新字段表、Run 校验、测试快照和相关 Schema。

固定 seed 数值由 [`test_safety_baseline.py`](../../tests/test_safety_baseline.py) 保护，60 年结构和数量由 [`test_long_horizon_contract.py`](../../tests/test_long_horizon_contract.py) 保护。参数变更本来就会改变数值摘要；只有确认新行为正确后，才应更新基线摘要。
