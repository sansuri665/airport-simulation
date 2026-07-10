# Global Dollar Liquidity Layer Design

## 当前定位

`global_dollar_liquidity_layer_sim.py` 是宏观模拟链条里的第五层：

```text
Global GDP -> Global Inflation -> Global Policy Rate -> Global Yield Curve -> Global Dollar / Liquidity
```

当前仍然采用“世界加权宏观口径”，不是精确复制 DXY、美元实际有效汇率或某个央行的流动性指标。它更像一个全球金融条件连接层：美元强弱、全球流动性、风险偏好和新兴市场压力都在这里先形成。

## 主要输出

脚本默认写入：

- `output/global_macro/global_dollar_liquidity_seed_sweep.csv`
- `output/global_macro/global_dollar_liquidity_seed_sweep.json`
- `output/global_macro/global_dollar_liquidity_viewer_data.js`
- `output/global_macro/global_dollar_liquidity_curves.svg`

HTML viewer 会优先读取：

```js
window.GLOBAL_DOLLAR_LIQUIDITY_DATA
```

如果该数据不存在，才回退到收益率曲线、政策利率、通胀或 GDP 数据。

## 核心字段

- `global_dollar_index`：全球美元压力指数，初始值约 100。
- `dollar_yoy_change_pct`：美元指数年度变化。
- `dollar_momentum_index`：美元动量，兼顾年度变化和偏离 100 的程度。
- `global_liquidity_index`：全球流动性指数，0-100 区间。
- `liquidity_impulse_index`：流动性年度边际变化。
- `global_financial_conditions_index`：金融条件指数，越高代表越紧。
- `risk_appetite_index`：风险偏好指数，0-100 区间。
- `em_stress_index`：新兴市场压力指数。
- `dollar_funding_stress_index`：美元融资压力指数。
- `dollar_liquidity_regime`：美元/流动性状态分类。

## 状态分类

目前使用的状态包括：

- `crisis_dollar_squeeze`
- `safe_haven_dollar_bid`
- `liquidity_easing_reflation`
- `tight_financial_conditions`
- `dollar_bear_liquidity_wave`
- `risk_on_liquidity_expansion`
- `em_dollar_pressure`
- `disinflationary_dollar_strength`
- `easy_dollar_liquidity`
- `neutral_dollar_liquidity`

这些状态先用于观察，不会在 v0.1 反向改写 GDP、通胀、政策利率或收益率曲线。

## 预留反馈接口

美元层已经输出以下占位字段，方便后续接通胀、石油、股票、信用和 GDP：

- `dollar_to_import_inflation_impulse`
- `dollar_to_oil_pressure_impulse`
- `dollar_to_gdp_drag_placeholder`
- `dollar_to_credit_tightening_impulse`
- `liquidity_to_equity_impulse`
- `liquidity_to_credit_easing_impulse`

v0.1 中这些字段只向后游模块传递信号，不回写上游。后面如果做多轮联立模拟，可以把美元冲击回灌到进口通胀、油价、信用利差和 GDP 增长。

## 建议的下一层连接

美元/流动性层之后，比较自然的顺序是：

```text
Dollar / Liquidity -> Credit Spreads -> Equity / Bonds -> Oil / Commodities
```

也可以先做石油，因为美元强弱、全球增长、通胀和危机压力已经足够构造一个初版油价路径。
