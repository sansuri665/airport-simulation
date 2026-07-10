# Global Oil Commodity Layer Design

## 当前定位

`global_oil_commodity_layer_sim.py` 是宏观模拟链条里的第八层：

```text
Global GDP -> Global Inflation -> Global Policy Rate -> Global Yield Curve -> Global Dollar / Liquidity -> Global Credit Spreads -> Global Asset Prices -> Global Oil / Commodities
```

当前采用“全球 Brent 油价 + 广义商品指数口径”，不是精确复制某个原油期货合约、现货篮子或商品指数。它更像一个能源与商品连接层：全球需求、美元、流动性、信用压力、资产风险偏好和外生供给事件共同决定油价和广义商品周期。

## 主要输出

脚本默认写入：

- `output/global_macro/global_oil_commodity_seed_sweep.csv`
- `output/global_macro/global_oil_commodity_seed_sweep.json`
- `output/global_macro/global_oil_commodity_viewer_data.js`
- `output/global_macro/global_oil_commodity_curves.svg`

HTML viewer 会优先读取：

```js
window.GLOBAL_OIL_COMMODITY_DATA
```

如果该数据不存在，才回退到资产、信用利差、美元/流动性、收益率曲线、政策利率、通胀或 GDP 数据。

## 核心字段

- `brent_oil_price_usd`：Brent 油价，单位为美元/桶。
- `global_oil_price_index`：油价指数，初始值约 100。
- `oil_yoy_change_pct`：油价年度变化率。
- `broad_commodity_index`：广义商品指数，初始值约 100。
- `commodity_yoy_change_pct`：广义商品指数年度变化率。
- `oil_demand_pressure_index`：油品需求压力，0-100 区间。
- `oil_supply_shock_index`：供给冲击指数，正值代表短缺/地缘/OPEC 式压力，负值代表供给宽松或库存过剩。
- `oil_inventory_pressure_index`：库存压力，正值代表库存偏紧，负值代表库存宽松。
- `energy_cost_pressure_index`：能源成本压力，0-100 区间。
- `oil_financial_pressure_index`：由美元、流动性、风险偏好、信用压力共同形成的金融定价压力。
- `oil_regime`：石油/商品状态分类。

## 状态分类

目前使用的状态包括：

- `geopolitical_oil_shock`
- `stagflationary_energy_squeeze`
- `energy_inflation_pressure`
- `commodity_supercycle`
- `risk_on_commodity_bid`
- `strong_dollar_oil_pressure`
- `oil_demand_slump`
- `supply_glut_disinflation`
- `oil_glut_disinflation`
- `crisis_oil_liquidation`
- `normal_oil_cycle`

这些状态先用于观察，不会在 v0.1 反向改写 GDP、通胀、利率、信用或资产价格路径。

## 预留反馈接口

石油层已经输出以下占位字段，方便后续做多轮反馈：

- `oil_to_headline_inflation_impulse`
- `oil_to_gdp_drag_placeholder`
- `oil_to_credit_stress_impulse`
- `oil_to_policy_pressure_impulse`
- `commodity_to_terms_of_trade_impulse`

v0.1 中这些字段只向后游模块传递信号，不回写上游。后面如果做多轮联立模拟，可以把油价对 headline 通胀、真实收入、信用压力、央行反应和贸易条件的影响重新输入宏观路径。

## 当前建模节奏

油价路径不是单纯平滑趋势，而是由几类力量叠加：

- 全球增长、产出缺口、风险偏好和信用可得性推升或压低需求压力。
- 强美元、美元动量和紧金融条件压制油价；宽流动性和风险偏好会托住商品定价。
- 随机供给短缺和供给过剩事件制造数年的冲击段落。
- 高油价会通过需求破坏和价格重力形成软约束，而不是使用硬上限。
- 广义商品指数在很高水平时只对新增正回报做软压缩，不使用硬上限。
- 油价和广义商品指数之间保持相关，但商品指数波动略低、受美元和需求周期影响更分散。

## 建议的下一层连接

石油/商品之后，比较自然的下一步是：

```text
Oil / Commodities -> Sector Profits / Terms of Trade -> Portfolio Allocation
```

也可以先做“宏观反馈接口调度器”，把 GDP、通胀、政策、美元、信用、资产和石油层输出的 `*_impulse` 字段统一收集，再决定哪些字段进入第二轮模拟。
