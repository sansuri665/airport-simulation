# Global Credit Spread Layer Design

## 当前定位

`global_credit_spread_layer_sim.py` 是宏观模拟链条里的第六层：

```text
Global GDP -> Global Inflation -> Global Policy Rate -> Global Yield Curve -> Global Dollar / Liquidity -> Global Credit Spreads
```

当前仍然采用“世界加权信用环境口径”，不是精确复制美国 CDX、全球 IG 指数或某一个高收益债指数。它更像一个全球企业融资压力层：美元融资、全球流动性、金融条件、风险偏好、违约风险和信贷可得性都在这里集中体现。

## 主要输出

脚本默认写入：

- `output/global_macro/global_credit_spread_seed_sweep.csv`
- `output/global_macro/global_credit_spread_seed_sweep.json`
- `output/global_macro/global_credit_spread_viewer_data.js`
- `output/global_macro/global_credit_spread_curves.svg`

HTML viewer 会优先读取：

```js
window.GLOBAL_CREDIT_SPREAD_DATA
```

如果该数据不存在，才回退到美元/流动性、收益率曲线、政策利率、通胀或 GDP 数据。

## 核心字段

- `global_investment_grade_spread_bps`：全球投资级信用利差，单位 bps。
- `global_high_yield_spread_bps`：全球高收益信用利差，单位 bps。
- `global_credit_spread_index`：综合信用压力指数，0-100 区间。
- `credit_spread_change_bps`：综合信用利差年度变化。
- `default_risk_index`：违约风险指数。
- `lending_standards_index`：放贷标准收紧程度。
- `credit_availability_index`：信贷可得性。
- `corporate_refinancing_pressure_index`：企业再融资压力。
- `bank_credit_stress_index`：银行/信用中介压力。
- `bank_lending_sentiment_index`：银行信贷情绪，越高代表越愿意把流动性转化为贷款。
- `bank_balance_sheet_stress_index`：银行资产负债表压力，越高代表坏账/资本压力更高。
- `credit_convexity_pressure_index`：信用凸性压力，HY 利差进入高压力区后非线性上升。
- `credit_impairment_stock_index`：信用危机疤痕/资产负债表修复库存。它会在高 HY 利差、负产出缺口、违约风险、银行压力和利差快速走阔时累积，并按多年半衰期缓慢消退。
- `credit_regime`：信用周期状态分类。

`credit_to_gdp_drag_placeholder` 现在使用分段函数：HY 利差在低位时拖累较小，进入高压区后拖累非线性增强。这样平稳年份不会被过度压制，但危机年份仍能出现信用崩塌速度加快的尾部行为。

银行信贷情绪是隐式中间层。QE 和流动性会改善它，但如果 HY-IG 质量利差、违约风险或银行资产负债表压力很高，银行仍可能囤积资金而不是扩张贷款。

`credit_impairment_stock_index` 用来避免信用危机后过快 V 型修复。它采用“恶化快、修复慢”的库存机制：上一年的信用疤痕会抬高当年 HY/IG 软底、压低信用可得性和银行放贷意愿；当年的信用环境再决定下一年的疤痕库存。这样政策宽松可以改善流动性，但不能立刻清除坏账、再融资压力和银行资产负债表约束。

## 状态分类

目前使用的状态包括：

- `credit_goldilocks`
- `easy_credit_expansion`
- `credit_easing_repair`
- `balance_sheet_repair`
- `normal_credit_cycle`
- `late_cycle_tightening`
- `rapid_spread_widening`
- `credit_squeeze`
- `convex_credit_selloff`
- `bank_lending_freeze`
- `funding_stress_credit_shock`
- `recession_default_wave`
- `refinancing_wall`

这些状态先用于观察。通过反馈调度器运行完整栈时，信用疤痕、信用拖累、银行信贷情绪和信用凸性会进入下一轮 GDP、通胀、政策和金融压力反馈。

## 预留反馈接口

信用层已经输出以下占位字段，方便后续接股票、债券、石油和多轮宏观反馈：

- `credit_to_gdp_drag_placeholder`
- `credit_to_equity_risk_premium_impulse`
- `credit_to_policy_easing_pressure`
- `credit_to_inflation_demand_drag_placeholder`
- `credit_to_oil_demand_impulse`

单独运行本层时，这些字段只向后游模块传递信号，不回写上游。通过 `global_macro_feedback_calibration_sim.py` 运行时，信用拖累、信用疤痕、银行信贷情绪和信用凸性会进入下一轮 GDP、通胀、政策和金融压力反馈。

## 建议的下一层连接

信用利差之后，最自然的是做股票/债券资产价格层：

```text
Credit Spreads -> Equity Valuation / Earnings -> Equity Index
Credit Spreads -> Corporate Bond Total Return
```

也可以先做石油/大宗商品层，因为现在已经有 GDP、通胀、美元、流动性、信用和油价需求 impulse。
