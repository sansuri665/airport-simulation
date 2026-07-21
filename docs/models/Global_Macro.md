# 全球宏观模型

## 它解决什么问题

全球宏观模型为一次机场模拟生成共同的世界背景。它回答的不是“某家机场赚多少钱”，而是更上游的问题：世界经济增长、通胀、利率、美元流动性、信用、资产价格和能源成本在同一条时间线上如何相互影响。

同一个 `seed`（随机种子）和同一组参数会得到同一条路径。所有区域、航空和城市机场模型都沿用这条路径，因此不会各自生成互相矛盾的世界经济。

## 输入

完整运行由 [`macro_run_orchestrator_sim.py`](../../macro_layers/macro_run_orchestrator_sim.py) 组织。主要输入是：

| 输入 | 默认值 | 含义 |
| --- | ---: | --- |
| `seed` | 未指定时随机生成 | 决定本次世界中的周期和冲击；固定后可复现 |
| `start_year` | 2025 | 时间轴起点 |
| `years` | 60 | 起点之后继续模拟的年数 |
| `initial_gdp` | 100.0 | 起始全球 GDP，单位为万亿美元 |
| `volatility_scale` | 1.0 | 全球 GDP 随机波动的整体倍率 |
| `feedback_iterations` | 16 | 宏观反馈最大回跑次数（达到收敛契约后提前停止） |
| `min_feedback_iterations` | 3 | 收敛判定的最小回跑次数门槛 |
| `scenario_state` | `none` | 是否额外生成手动、反事实或概率岔路 |

`years=60` 会得到 `year_index=0..60`，即 61 个年度观测。第 0 行是起点，不是“第一年运行结束”。

## 处理过程

全球层按固定顺序运行：

```text
实际 GDP 与产出缺口
  → 通胀
  → 政策利率与 QE
  → 收益率曲线和债券
  → 美元、流动性和金融条件
  → 投资级/高收益信用利差
  → 股票、债券与 60/40 组合
  → 油价和广义商品
  → 滞后一年的反馈回到增长、通胀和政策
```

各步骤不是八条互不相干的随机曲线。前一步会把明确的“传导字段”交给下一步，例如通胀向政策利率传导、利率向信用和估值传导、油价向通胀和增长传导。完整链的实现入口是 [`global_macro_feedback_calibration_sim.py`](../../macro_layers/global_macro_feedback_calibration_sim.py)。

模型先生成一条完整路径，再根据信用、美元、资产、油价、政策和通胀结果推导下一轮滞后反馈。默认求解器使用完整、确定的反馈更新，至少回跑 3 次，最多 16 次；相同 Seed、参数和代码版本会得到相同的 Pass 序列。

收敛不能只看综合指数，也不能依靠越来越小的松弛步长制造表面稳定。求解器要求最后两个相邻 Pass 的增长、通胀、政策利率、2Y、10Y、美元、HY 和 Brent 最大绝对差分别通过版本化门槛；随后还会从候选结果重新推导完整反馈并执行一次不带松弛的影子 Pass。只有该固定点残差也通过八字段门槛，Run 才会标记为 `converged=true`。影子 Pass 只用于验证，正式输出仍是最后一个被接受的完整模型 Pass。

若达到 16 次仍未通过，Run 可以作为诊断产物保留，但不能发布为 Viewer Release。Manifest 保存完整的 `pass_diagnostics[]` 和 `fixed_point_residual_diagnostic`，发布护栏会重新核验版本、逐字段门槛、边界计数和最终残差，而不是只相信一个布尔值。

## 岔路与风险提示

每个年度结果还会根据当时数据生成风险观察名单，例如软着陆、过早收紧、信用事故、美元挤兑、能源冲击或滞胀。这里的“概率”是规则评分转换出的游戏指标，不是由真实历史样本估计的统计概率。

- 基准运行只记录风险，不自动改写已经生成的基准路径。
- `occurred` 或 `counterfactual` 会生成第二条指定岔路。
- `probabilistic` 会用固定 seed、风险评分、冷却期和事件上限选择岔路；结果仍可复现。
- 岔路先改变全球增长、通胀、政策、流动性、信用、美元和能源等冲量，随后继续传到区域和机场。

## 输出

一次完整 Run 的全球结果位于：

```text
output/macro_runs/<run_id>/<variant>/global_macro/
```

主要文件是：

- `global_macro_feedback_seed_sweep.csv`：逐年明细，是模型分析的主要事实表。
- `global_macro_feedback_seed_sweep_summary.json`：参数、汇总和反馈收敛信息。
- `global_macro_feedback_viewer_data.js`：完整产物模式下供 Viewer 使用。

`variant` 至少包含 `baseline`；启用岔路时还会有第二个情景目录。Run 级元数据写在 `output/macro_runs/<run_id>/manifest.json`，其结构由 [`macro-run-manifest.schema.json`](../../schemas/macro-run-manifest.schema.json) 约束。

### Run 的落盘顺序

完整 Run 不会一边计算一边覆盖正式目录。编排器先在临时 staging 目录生成基准路径和可选情景路径，再校验 CSV 的 seed、年份、年度索引、表头、行数以及 14 区覆盖。只有全部通过后才把 staging 目录整体切换为最终 Run；同名 Run 已存在时会拒绝覆盖。

切换成功后，编排器更新供命令和清理工具使用的 `macro_run_index.json`。如果明确要求发布 Viewer，还会把选定 variant 复制为带校验和的发布目录，再更新当前 Viewer manifest。全球页不再直接浏览 Run，也不加载 Run 索引 JS；`artifact-profile=seed-cache` 只保留 Seed Explorer/API 所需数据，不生成 Viewer 资源，也不能同时执行 Viewer 发布。

输出可分为以下几组：

| 组别 | 代表字段 | 口径 |
| --- | --- | --- |
| 经济活动 | `global_gdp_trillion_usd`、`realized_growth_pct`、`output_gap_pct` | 万亿美元、年增长率、百分点 |
| 物价 | `headline_inflation_pct`、`core_inflation_pct` | 年通胀率，百分比 |
| 利率 | `global_policy_rate_pct`、`global_2y_yield_pct`、`global_10y_yield_pct` | 年化百分比 |
| 信用 | `global_investment_grade_spread_bps`、`global_high_yield_spread_bps` | 基点，100 bps = 1 个百分点 |
| 市场 | `global_equity_index`、`bond_price_index`、`equity_total_return_pct` | 起点附近为 100 的指数、年度回报率 |
| 流动性与压力 | `global_liquidity_index`、`risk_appetite_index`、`financial_stress_index` | 模型内部指数，不是现实统计值 |
| 能源 | `brent_oil_price_usd`、`energy_cost_pressure_index` | 美元/桶、模型内部指数 |
| 反馈与岔路 | `macro_feedback_*`、`branch_risk_*`、`scenario_*` | 反馈诊断、风险观察和情景状态 |

`macro_feedback_intensity_index` 和四个 `macro_feedback_*_raw*` 字段只描述宏观反馈校准层自身；情景岔路的额外冲击不会混入这些 raw 诊断。最终 applied impulse 仍可同时包含宏观反馈与情景冲击，二者通过来源和情景字段区分。区域层读取宏观反馈强度计算政策不确定性，因此编排器必须保留这些诊断字段，不能只保留 applied impulse。

## 与其他模块的关系

全球结果是区域宏观层的唯一共同锚。区域层读取全球增长、通胀、利率、收益率、美元、信用、资产、油价以及岔路字段，生成 14 个有差异的区域路径。全球层不直接计算城市客流、机场容量、收入或估值。

```text
全球宏观
  → 14 区区域宏观与对账
  → 区域航空需求
  → 区域航司供给
  → 城市机场市场
  → 季度经营、财务和估值
```

## 真实代码位置

- GDP：[`global_gdp_annual_sim.py`](../../macro_layers/global_gdp_annual_sim.py)
- 通胀：[`global_inflation_annual_sim.py`](../../macro_layers/global_inflation_annual_sim.py)
- 政策：[`global_policy_rate_layer_sim.py`](../../macro_layers/global_policy_rate_layer_sim.py)
- 收益率曲线：[`global_yield_curve_layer_sim.py`](../../macro_layers/global_yield_curve_layer_sim.py)
- 美元与流动性：[`global_dollar_liquidity_layer_sim.py`](../../macro_layers/global_dollar_liquidity_layer_sim.py)
- 信用：[`global_credit_spread_layer_sim.py`](../../macro_layers/global_credit_spread_layer_sim.py)
- 资产价格：[`global_asset_price_layer_sim.py`](../../macro_layers/global_asset_price_layer_sim.py)
- 油价与商品：[`global_oil_commodity_layer_sim.py`](../../macro_layers/global_oil_commodity_layer_sim.py)
- 反馈和风险观察：[`global_macro_feedback_calibration_sim.py`](../../macro_layers/global_macro_feedback_calibration_sim.py)
- Run、情景和输出：[`macro_run_orchestrator_sim.py`](../../macro_layers/macro_run_orchestrator_sim.py)
- 固定 seed 数值基线：[`test_safety_baseline.py`](../../tests/test_safety_baseline.py)
- 60 年结构契约：[`test_long_horizon_contract.py`](../../tests/test_long_horizon_contract.py)

## 当前限制

- 这是用于游戏和压力测试的合成模型，不是宏观预测服务，也不读取实时经济数据。
- 时间粒度为年度；季度经营层只是把下游机场经营展开为季度，不会反向增加全球宏观的季度细节。
- “全球”是一个统一总盘，没有国家财政、国际贸易矩阵、央行博弈或多币种资产负债表。
- 风险概率来自规则评分，不能解释为现实事件发生概率。
- 固定点验证只覆盖八个公开宏观稳定字段；它保证反馈映射在这些门槛内稳定，不代表模型求得现实经济中的一般均衡。
- 各年度明细目前依靠代码字段表和测试保护，尚无逐行全球宏观 JSON Schema；正式 Schema 主要覆盖 Run manifest 和 Viewer 数据接口。
