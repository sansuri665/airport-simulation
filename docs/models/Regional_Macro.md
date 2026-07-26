# 区域宏观模型

## 它解决什么问题

全球宏观只有一条世界总盘，无法直接解释中国大陆、北美或东南亚为什么表现不同。区域宏观模型把同一条全球路径传导到 14 个区域，并保留各区在增长、收入、通胀、利率、汇率、信用、资产、能源和风险暴露上的差异。

区域结果随后经过对账：全球 GDP 是总量锚，各区域既保留相对强弱，又不能在体量上组成另一个与全球路径冲突的世界。

## 区域覆盖与当前差异

区域 ID、顺序和参数都来自代码，而不是旧文档。`global_weight` 是相对初始权重；当前 14 项合计为 1.127，对账层会先归一化为 100%，因此不能把原始配置值直接当作最终 GDP 占比。

| 区域 ID | 覆盖名称 | 归一化初始份额 | 趋势增长 | 潜在增长边界 |
| --- | --- | ---: | ---: | ---: |
| `north_america` | 北美 | 25.29% | 1.85% | 0.45%–3.35% |
| `china_mainland` | 中国大陆 | 16.42% | 3.85% | 1.20%–5.25% |
| `west_north_europe` | 西欧/北欧 | 14.64% | 1.38% | 0.10%–2.70% |
| `japan_korea` | 日韩 | 6.39% | 1.05% | -0.10%–2.40% |
| `southeast_asia` | 东南亚 | 4.61% | 4.20% | 1.40%–6.20% |
| `south_asia_india` | 南亚/印度 | 5.32% | 5.25% | 2.20%–7.20% |
| `hk_macao_taiwan` | 港澳台 | 3.11% | 1.82% | 0.05%–3.25% |
| `middle_east_gulf` | 中东/海湾 | 3.99% | 3.25% | 0.95%–5.50% |
| `oceania` | 大洋洲 | 2.48% | 2.18% | 0.45%–3.75% |
| `south_east_europe_mediterranean` | 南欧/东欧/地中海 | 3.55% | 2.05% | 0.25%–4.10% |
| `central_asia_turkey_eurasia` | 中亚/土耳其/欧亚桥 | 2.66% | 3.05% | 0.70%–5.80% |
| `north_africa` | 北非 | 1.95% | 3.65% | 0.90%–6.40% |
| `latin_america_caribbean` | 拉美/加勒比 | 6.21% | 2.65% | 0.55%–5.30% |
| `sub_saharan_africa` | 撒哈拉以南非洲 | 3.37% | 4.35% | 1.20%–7.30% |

差异不只来自表中的增长率。每个区域还拥有收入水平、市场成熟度、国内需求、国际连接、旅游和商务暴露，以及对油价、美元、信用、资产、政策和地缘风险的敏感度。真实配置集中在 [`regional_macro_layer_sim.py`](../../macro_layers/regional_macro_layer_sim.py) 的 `REGION_CONFIGS`，表中数值也是从该结构读取的当前值。

这些区域是模型分区，不等于逐国统计口径。例如“西欧/北欧”或“中亚/土耳其/欧亚桥”内部不会再拆分国家。

## 输入

每个区域读取同一个 seed 下、同一个年度的全球结果，包括：

- 全球实际和潜在增长、产出缺口、金融压力；
- 总体和核心通胀、能源与进口通胀；
- 政策利率、实际利率、10 年期收益率和期限利差；
- 美元、流动性、金融条件和风险偏好；
- 投资级/高收益信用利差、信贷可得性；
- 全球股票价格回报、总回报、PE、主权债总回报、油价和能源成本；
- 已激活的全球岔路及其阶段。

区域还使用自身参数和 seed 结构势能。14 个区域都配置了结构势能模板；它通过稳定哈希为该 seed 生成长期增长、航空倾向、投资周期、开放度和需求乘数偏移。影响从 `year_index=4` 开始释放，到 `year_index=34` 达到完整强度，避免开局立即推翻初始世界结构。

## 处理过程

### 1. 生成区域原始路径

区域模型把全球变量按本区敏感度转换为本地增长、通胀、利率、汇率、信用、收入、消费信心、能源和压力指数。每个变量带有惯性和边界，区域不会机械复制全球曲线。

### 2. 区域股票、本币债券与居民财富桥

区域宏观基础路径之后，资产会计 v0.4 单独生成区域 EPS、PE、股票价格/股息/总回报和本币主权债总回报。区域股票价格恒等于 EPS 与 PE 的会计组合，不再由无盈利锚的混合指数独立漂移。区域资产软对账只发布全球—区域加权差异诊断，不强行改写本地资产结果。

居民财富桥按 `market_based`、`balanced` 或 `bank_centered` 持仓模板，把股票价格回报、股息、本币债券和现金回报转换为实际金融财富增长。它发布三条不同信号：

- `regional_asset_market_impulse_index`：当期市场风险/信心；
- `regional_household_wealth_consumption_impulse`：带滞后并逐年衰减的居民财富消费冲量；
- `regional_real_disposable_income_growth_pct`：实际收入与可消费股息现金信号。

财富存量保留在 `regional_household_financial_wealth_index`，下游不能反复读取“存量减 100”制造永久增长。

### 3. 传导全球岔路

全球岔路不会给 14 个区域施加完全相同的数值。代码依据岔路类型选择主要暴露维度，再结合区域的国际、能源、美元、信用、旅游、商务和地缘敏感度，形成区域增长、通胀、政策、信用、汇率、能源、流动性、资产和信心冲量。

`regional_branch_transmission_active` 表示当年是否处于冲击或尾部阶段；`regional_branch_exposure_index` 表示区域暴露，`regional_branch_strength_index` 表示本次实际传导强度。冲击结束后仍可留下 `regional_branch_tail_scarring_index`，但它不是永久更改区域基础参数。

### 4. 与全球总量对账

[`regional_macro_reconciliation_sim.py`](../../macro_layers/regional_macro_reconciliation_sim.py) 按每个 seed、每个年度同时收齐 14 区后执行：

1. 将 14 个配置权重归一化。
2. 用起始全球 GDP、区域初始权重和区域 GDP 指数得到原始区域 GDP。
3. 用同一个缩放因子调整所有区域 GDP，使 14 区对账后 GDP **精确合计为当年全球 GDP**。
4. 根据前一年对账后体量重新计算区域增长和增长贡献。
5. 对通胀、政策利率、10 年期收益率、信用利差、压力和能源成本做有上限的共同偏移，使加权结果向全球锚靠近；正式资产字段不在这里二次改写。
6. 按区域原始层的同一套公开边界重新裁剪各区结果，再用最终值计算加权残差和质量标签。

第 5、6 步是“软对账”，不保证每个加权指标与全球值完全相等。这样可以保留区域差异，同时避免用对账层掩盖不合理的区域配置。诊断字段会记录请求调整量、裁剪后的加权缺口、各字段裁剪区域数、总裁剪次数，以及 `low_gap`、`medium_gap` 或 `high_gap` 质量标签。GDP 体量仍然使用第 3 步的硬对账，不受软指标裁剪影响。

## 输出

原始区域路径位于：

```text
output/macro_runs/<run_id>/<variant>/regional_macro/<region_id>/
```

每区包含逐年 CSV、摘要 JSON；完整产物模式还包含 Viewer 数据。对账结果位于：

```text
output/macro_runs/<run_id>/<variant>/regional_macro_reconciled/
```

其中：

- `regional_macro_reconciled_seed_sweep.csv`：14 区逐年对账结果；
- `regional_macro_reconciliation_seed_sweep.csv`：每年一行的全球—区域对账诊断；
- 两份 JSON：行数、质量和最终区域排名摘要。

默认 60 年运行中，每个区域有 61 行原始数据；对账明细共有 `14 × 61 = 854` 行，对账诊断共有 61 行。

## 关键口径和单位

| 字段族 | 口径 |
| --- | --- |
| `regional_gdp_index` | 区域实际 GDP 指数，起点为 100 |
| `regional_*_gdp_trillion_usd` | 区域 GDP 体量，万亿美元 |
| `*_growth_pct`、`*_inflation_pct`、`*_rate_pct` | 年率百分比 |
| `*_adjustment_pp`、`regional_weight_drift_pp` | 百分点差，不是百分比变化率 |
| `regional_ig_spread_bps`、`regional_hy_spread_bps` | 基点 |
| `currency_index`、`liquidity_index`、`stress_index` 等 | 模型内部指数；通常 100 或 50 附近是各自基准，不能横向当成同一统计量 |
| `regional_equity_price_index` / `regional_equity_total_return_index` | 区域股票价格 / 含股息再投资总回报，二者不可混用 |
| `regional_sovereign_bond_total_return_index` | 区域本币主权债累计名义总回报 |
| `regional_household_financial_wealth_index` | 按区域持仓模板计算的居民实际金融财富存量 |
| `regional_asset_market_impulse_index` | 当期资产市场冲量，50 为中性附近 |
| `regional_reconciled_share_of_global_gdp_pct` | 对账后区域占全球 GDP 的比例 |
| `regional_growth_contribution_pp_reconciled` | 该区域对全球式加权增长的贡献，百分点 |

读取下游模型时，增长、通胀、利率、信用、压力和能源应优先使用带 `_reconciled` 的字段；资产与居民财富使用上述 v0.4 正式字段，不存在 `_reconciled` fallback。

## 与其他模块的关系

- 上游：全球宏观提供共同世界、风险观察和已激活岔路。
- 同层：对账将 14 条区域路径约束回全球总量。
- 下游：区域航空需求读取对账宏观字段，并分别读取资产市场、居民财富和现金购买力三条唯一信号。
- 城市层也会读取区域原始宏观字段，用于解释城市客流和航司供给，而不是重新生成一套宏观经济。

## 真实代码和验证位置

- 区域参数、seed 势能、岔路传导和年度模拟：[`regional_macro_layer_sim.py`](../../macro_layers/regional_macro_layer_sim.py)
- 区域股票与本币债券：[`regional_asset_accounting_v04.py`](../../macro_layers/regional_asset_accounting_v04.py)
- 居民财富桥：[`regional_wealth_bridge_v04.py`](../../macro_layers/regional_wealth_bridge_v04.py)
- 区域顺序、权重归一化和对账：[`regional_macro_reconciliation_sim.py`](../../macro_layers/regional_macro_reconciliation_sim.py)
- 一键运行次序与输出：[`macro_run_orchestrator_sim.py`](../../macro_layers/macro_run_orchestrator_sim.py)
- 14 区、61 年和行数契约：[`test_long_horizon_contract.py`](../../tests/test_long_horizon_contract.py)
- 固定 seed 数值基线：[`test_safety_baseline.py`](../../tests/test_safety_baseline.py)

## 当前限制

- 14 区参数和结构势能都内嵌在 Python 中，尚未迁移为独立配置文件。
- 区域是大区合成体，没有国家、城市以外的省级经济、双边贸易、人口迁移或跨区航线矩阵。
- GDP 总量会精确对账；其他宏观指标只做有上限的共同偏移，因此仍可能显示 `high_gap`。
- 对账是年度结果的协调层，不会反向重新求解全球模型，也不会改变全球路径。
- 区域结构势能是游戏中的 seed 分化机制，不是对现实区域潜力的预测。
- 区域资产与财富必需字段由 [`asset-accounting-v04-fields.schema.json`](../../schemas/asset-accounting-v04-fields.schema.json) 约束；其余区域宏观逐年字段仍主要由字段表、Run 校验和固定 Seed 测试保护。
