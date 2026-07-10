# Global Asset Price Layer Design

## 当前定位

`global_asset_price_layer_sim.py` 是宏观模拟链条里的第七层：

```text
Global GDP -> Global Inflation -> Global Policy Rate -> Global Yield Curve -> Global Dollar / Liquidity -> Global Credit Spreads -> Global Asset Prices
```

当前采用“全球股债资产环境口径”，不是精确复制某个股票指数、国债指数或公司债指数。它更像一个资产定价连接层：盈利、估值、实际利率、信用利差、美元、流动性和风险偏好共同决定股票和债券表现。

## 主要输出

脚本默认写入：

- `output/global_macro/global_asset_price_seed_sweep.csv`
- `output/global_macro/global_asset_price_seed_sweep.json`
- `output/global_macro/global_asset_price_viewer_data.js`
- `output/global_macro/global_asset_price_curves.svg`

HTML viewer 会优先读取：

```js
window.GLOBAL_ASSET_PRICE_DATA
```

如果该数据不存在，才回退到信用利差、美元/流动性、收益率曲线、政策利率、通胀或 GDP 数据。

## 核心字段

- `global_equity_index`：全球股票价格/总回报指数。
- `equity_total_return_pct`：股票年度总回报。
- `equity_earnings_index`：股票盈利指数。
- `equity_eps_growth_pct`：盈利年度增长。
- `equity_valuation_pe`：估值 PE。
- `equity_risk_premium_pct`：股票风险溢价。
- `equity_drawdown_pct`：股票相对历史高点回撤。
- `global_sovereign_bond_index`：全球主权债指数。
- `sovereign_bond_total_return_pct`：主权债年度总回报。
- `global_corporate_bond_index`：全球公司债指数。
- `corporate_bond_total_return_pct`：公司债年度总回报。
- `global_60_40_portfolio_index`：60/40 股债组合指数。
- `portfolio_60_40_total_return_pct`：60/40 组合年度回报。
- `asset_volatility_index`：资产波动/风险指数。
- `asset_risk_regime`：资产市场状态分类。

债券和 60/40 指数不再使用硬上限。高位时只对新增正回报做软压缩，避免长期低利率路径下指数机械跑飞，同时保留继续上涨或回落的空间。

资产层会读取信用层的 `credit_impairment_stock_index`。当信用危机疤痕较高时，EPS 增长修复会变慢，权益风险溢价会更高，PE 扩张会被压制，资产波动也会更高。这样流动性托底仍可能带来反弹，但更难在银行资产负债表尚未修复时直接形成平滑牛市。

## 状态分类

目前使用的状态包括：

- `liquidity_equity_bull`
- `goldilocks_asset_rally`
- `credit_beta_rally`
- `bear_market_rebound`
- `valuation_compression`
- `credit_drag_risk_off`
- `equity_risk_off`
- `equity_credit_crash`
- `stock_bond_inflation_shock`
- `bond_rally_recession_hedge`
- `normal_asset_cycle`

这些状态先用于观察，不会在 v0.1 反向改写上游路径。

## 预留反馈接口

资产层已经输出以下占位字段，方便后续做多轮反馈：

- `asset_to_gdp_wealth_impulse`
- `asset_to_policy_financial_conditions_impulse`
- `asset_to_credit_risk_appetite_impulse`
- `asset_to_inflation_wealth_demand_impulse`

v0.1 中这些字段只向后游模块传递信号，不回写上游。后面如果做多轮联立模拟，可以把资产价格的财富效应、金融条件和风险偏好重新输入 GDP、央行和信用层。

## 建议的下一层连接

股债之后，比较自然的下一步是石油/大宗商品层：

```text
GDP + Dollar + Inflation + Credit + Asset Risk -> Oil / Commodities
```

也可以先做一个“资产配置/组合层”，把股票、主权债、公司债、现金和商品组合起来。
