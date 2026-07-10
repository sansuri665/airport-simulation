# Global Macro Feedback Calibration Design

## 当前定位

`global_macro_feedback_calibration_sim.py` 是当前宏观链条的反馈调度器和校准入口：

```text
Pass 1:
GDP -> Inflation -> Policy -> Yield Curve -> Dollar / Liquidity -> Credit -> Assets -> Oil

Feedback extraction:
Credit / Dollar / Policy / Inflation / Assets / Oil *_impulse fields -> lagged feedback path

Pass 2..N:
GDP + feedback -> Inflation + feedback -> Policy + feedback -> ... -> Oil
```

它不是全球事件识别器，也不会给年份命名为“金融危机”“能源危机”等。全球性事件层后面单独做。

## 主要输出

默认写入：

- `output/global_macro/global_macro_feedback_seed_sweep.csv`
- `output/global_macro/global_macro_feedback_seed_sweep.json`
- `output/global_macro/global_macro_feedback_viewer_data.js`
- `output/global_macro/global_macro_feedback_curves.svg`

HTML viewer 会优先读取：

```js
window.GLOBAL_MACRO_FEEDBACK_DATA
```

如果该数据不存在，才回退到石油、资产、信用、美元、收益率、政策、通胀或 GDP 数据。

## 反馈字段

GDP 层现在可以接收以下反馈输入：

- `feedback_growth_impulse_pct`：下一年 GDP 增长率的滞后反馈。
- `feedback_output_gap_impulse_pct`：下一年产出缺口的滞后反馈。
- `feedback_financial_stress_impulse`：下一年金融压力的滞后反馈。
- `feedback_inflation_impulse_pct`：传给通胀层的滞后通胀压力。
- `feedback_policy_impulse_pct`：传给央行层的滞后政策压力。
- `feedback_source`：反馈来源说明。

反馈校准层额外输出：

- `macro_feedback_intensity_index`
- `macro_feedback_growth_raw_pct`
- `macro_feedback_stress_raw`
- `macro_feedback_inflation_raw_pct`
- `macro_feedback_policy_raw_pct`
- `macro_feedback_iterations_requested`
- `macro_feedback_converged`
- `macro_feedback_last_pass_delta_index`
- `macro_feedback_max_pass_delta_index`
- `macro_feedback_note`

## 反馈来源

当前调度器会读取已经存在的预留接口：

- `credit_to_gdp_drag_placeholder`
- `dollar_to_gdp_drag_placeholder`
- `policy_to_gdp_drag_placeholder`
- `inflation_to_gdp_drag_placeholder`
- `yield_curve_to_gdp_drag_placeholder`
- `oil_to_gdp_drag_placeholder`
- `asset_to_gdp_wealth_impulse`
- `oil_to_headline_inflation_impulse`
- `dollar_to_import_inflation_impulse`
- `policy_to_inflation_lagged_impulse`
- `credit_to_inflation_demand_drag_placeholder`
- `oil_to_policy_pressure_impulse`
- `credit_to_policy_easing_pressure`
- `dollar_to_credit_tightening_impulse`
- `liquidity_to_credit_easing_impulse`
- `asset_to_credit_risk_appetite_impulse`
- `credit_convexity_pressure_index`
- `credit_impairment_stock_index`
- `bank_lending_sentiment_index`
- `bank_balance_sheet_stress_index`

这些字段以前只是“吐出信号”。现在它们会被汇总成下一年的反馈路径。

## 多轮反馈和收敛诊断

反馈调度器默认执行 3 次 rerun。每一轮都会：

1. 读取上一轮完整宏观路径。
2. 生成下一年的滞后反馈路径。
3. 用反馈路径重新跑 GDP、通胀、政策、收益率、美元、信用、资产和石油。

为避免年度反馈来回过度修正，Pass 2 之后的反馈会使用松弛系数做阻尼，不会完全替换上一轮反馈。

收敛诊断比较相邻 pass 的这些变量：

- GDP 增长率
- headline 通胀
- 政策利率
- HY 利差
- Brent 油价

`macro_feedback_last_pass_delta_index` 越低，说明最后两轮越接近。`macro_feedback_converged` 为 `true` 时，代表路径在年度宏观尺度上已经收敛；它不是逐点完全相等，而是关键变量差异落在设定容忍范围内。

加入信用危机疤痕后，HY 利差和油价在少数危机年份会保留更强尾部惯性，因此收敛诊断对 HY、油价和政策利率的单点最大差异做了小幅放宽；整体仍由 `macro_feedback_last_pass_delta_index` 约束。

## 校准内容

这次一起做了几类校准：

- GDP 初始年不再显示 `0%` 增长，而是显示趋势增长，避免第一年柱状图跳变。
- GDP 年度调整速度降低，但危机年份仍允许约 1 个百分点级别的年变化。
- 通胀和政策层接收反馈压力，避免油价、美元、信用信号只停留在下游。
- 信用利差加入分段凸性，HY 利差进入压力区后会非线性加大 GDP 和风险溢价拖累。
- 信用层加入隐式银行信贷情绪和银行资产负债表压力，避免“QE 高 = 信用自动宽松”的过度乐观。
- 信用层加入 `credit_impairment_stock_index` 慢变量，表达信用危机后的坏账出清和银行资产负债表修复。它会持续压住 GDP 反馈、产出缺口和金融压力，减少深度危机后的机械 V 型反弹。
- 股票层增加基础盈利增长参数，反馈校准入口使用更合理的全球盈利增长基准。
- 高油价只通过需求破坏和价格重力做软约束，不使用硬上限。

## 当前边界

反馈调度器仍然是轻量的年度机制：

- 默认做 3 次反馈 rerun，可通过 `--feedback-iterations` 调整。
- 反馈是年度滞后一年的，不做季度或月度高频动态。
- 不做事件命名，不判断“这是哪类危机”。
- 不做区域结构，比如美国、欧洲、中国、新兴市场拆分。

下一步如果要提高真实感，优先做“事件识别层”，读取现在这些 regime 和反馈强度，再给宏观年份打事件标签。
