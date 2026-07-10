# Global Yield Curve Layer Design

## 当前定位

`global_yield_curve_layer_sim.py` 是宏观模拟链条里的第四层：

```text
Global GDP -> Global Inflation -> Global Policy Rate -> Global Yield Curve
```

当前仍然采用“世界加权宏观口径”，不是美国国债曲线的精确复刻。它更像一个全球主权利率环境指数：短端跟随全球政策利率，2Y 体现未来降息/加息预期，10Y 叠加通胀预期、期限溢价、QE、金融压力和危机避险。

## 主要输出

脚本默认写入：

- `output/global_macro/global_yield_curve_seed_sweep.csv`
- `output/global_macro/global_yield_curve_seed_sweep.json`
- `output/global_macro/global_yield_curve_viewer_data.js`
- `output/global_macro/global_yield_curve_curves.svg`

HTML viewer 会优先读取：

```js
window.GLOBAL_YIELD_CURVE_DATA
```

如果该数据不存在，才回退到政策利率、通胀或 GDP 数据。

## 核心字段

- `global_short_rate_pct`：短端市场利率，主要跟政策利率和 QE 变化。
- `global_2y_yield_pct`：2 年收益率，偏向政策路径预期，对加息/降息压力更敏感。
- `global_10y_yield_pct`：10 年收益率，偏向长期通胀预期、期限溢价和避险因素。
- `global_real_10y_yield_pct`：10Y 减去通胀预期后的实际长期利率。
- `term_spread_10y_2y_pct`：10Y-2Y 期限利差，用来观察倒挂、牛陡、熊陡。
- `term_premium_pct`：期限溢价，受通胀波动、金融压力、QE 和资产负债表变化影响。
- `bond_price_index`：长期债券价格/回报指数的粗略代理。
- `yield_curve_regime`：收益率曲线状态分类。

## 曲线状态

目前预留并使用的状态包括：

- `normal_upward_curve`
- `flat_curve`
- `mild_inversion`
- `inverted_tightening`
- `bear_steepening`
- `bear_flattening`
- `bull_steepening`
- `recession_bull_flattening`
- `qe_suppressed_curve`
- `risk_premium_steepening`

这些状态先用于观察，不会在 v0.1 反向改写 GDP、通胀或政策利率路径。

## 预留反馈接口

收益率层已经输出以下占位字段，方便后续接美元、股票、信用、石油和 GDP 反馈：

- `yield_curve_to_dollar_impulse`
- `yield_curve_to_equity_valuation_impulse`
- `yield_curve_to_credit_impulse`
- `yield_curve_to_gdp_drag_placeholder`

v0.1 中这些字段只向后游模块传递信号，不回写上游。后面如果做多轮联立模拟，可以把这些 impulse 作为下一年 GDP、信用条件、美元压力和资产估值的输入。

## 建议的下一层连接

比较自然的下一步是做“美元/流动性层”或“股债资产层”：

- 美元层可以读取政策利差、实际 10Y、避险压力、曲线倒挂压力。
- 股票层可以读取实际 10Y、收益率变化、QE、GDP 增长和通胀 regime。
- 信用层可以读取倒挂压力、期限溢价、金融压力和政策紧缩 impulse。

当前代码已经把这些接口留好，后续只需要新增下游脚本并把 viewer 的数据源优先级继续往上抬。
