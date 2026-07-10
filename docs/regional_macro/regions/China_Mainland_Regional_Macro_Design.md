# China Mainland Regional Macro Layer

## 定位

中国大陆区域宏观层是 14 区域宏观的第二个可运行样板。

它和北美形成一组对照：

```text
north_america
  -> 成熟美元体系、利率/信用/股债财富效应强

china_mainland
  -> 超大国内市场、政策/信用/基建敏感、能源进口暴露更强
```

本层仍然不直接生成机场客流，也不直接决定机场收入。它只输出中国大陆区域的经济环境。

## 运行入口

```powershell
py -3 .\airport\macro_layers\regional_macro_layer_sim.py --region china_mainland
```

默认输出：

```text
airport/output/regional_macro/china_mainland_regional_macro_seed_sweep.csv
airport/output/regional_macro/china_mainland_regional_macro_seed_sweep.json
airport/output/regional_macro/china_mainland_regional_macro_viewer_data.js
```

## 中国大陆结构假设

中国大陆 v0.1 的核心特征：

- 潜在增长高于北美，但长期仍会被全球周期、能源和信用压力约束。
- 国内需求权重高，政策支持和基建脉冲可以缓冲全球下行。
- 政策利率不一比一跟随全球美元利率，更多体现本地政策和融资条件。
- 信用环境对增长很重要，`regional_hy_spread_bps` 是区域信用压力代理，不等于真实单一高收益债市场口径。
- 股市财富效应弱于北美，股价对消费信心和收入的传导较小。
- 汇率指数更平滑，体现管理型汇率/资本账户约束，但美元走强仍会带来外部压力和进口通胀。
- 能源进口暴露较高，油价上行会更明显推高能源成本并压低贸易条件。

## 关键参数

参数集中在 `RegionalMacroParams`：

```text
region_id = china_mainland
global_weight = 0.185
trend_growth_pct = 3.85
market_maturity = 0.66
domestic_demand_weight = 0.89
international_exposure = 0.58
credit_sensitivity = 1.16
equity_wealth_sensitivity = 0.62
policy_rate_sensitivity = 0.74
policy_global_beta = 0.42
long_rate_global_beta = 0.50
currency_dollar_beta = 0.38
fx_management_strength = 0.68
policy_support_sensitivity = 0.92
infrastructure_sensitivity = 0.82
energy_import_sensitivity = 1.18
commodity_export_sensitivity = 0.36
```

这些参数让中国大陆不会只是跟着全球线同步移动，而是会出现本地政策托底、信用周期和能源进口压力。

## 政策口径

`regional_policy_rate_pct` 在中国大陆层里不是某一个单一挂牌利率。

它是区域宏观模型里的综合政策/融资条件口径，近似代表：

```text
政策利率
  + 银行体系融资条件
  + 信贷支持强弱
  + 本地逆周期政策取向
```

所以它可以和全球政策利率分化。

当全球压力加大、通胀不高、产出缺口为负时，模型会生成 `policy_support_index`，并通过以下渠道影响区域宏观：

```text
policy_support_index
  -> regional_liquidity_index up
  -> regional_credit_availability_index up
  -> regional_hy_spread_bps down
  -> regional_gdp_growth_pct support
  -> regional_equity_return_pct support
```

这个机制用于表达政策托底和基建脉冲，但不会完全抵消全球信用、美元和能源冲击。

## 输出字段

中国大陆层沿用区域宏观统一字段：

```text
regional_gdp_index
regional_gdp_growth_pct
regional_potential_growth_pct
regional_output_gap_pct
regional_headline_inflation_pct
regional_core_inflation_pct
regional_income_index
consumer_confidence_index
regional_policy_rate_pct
regional_10y_yield_pct
regional_currency_index
regional_liquidity_index
regional_hy_spread_bps
regional_equity_index
regional_bond_index
regional_energy_cost_pressure_index
regional_terms_of_trade_index
regional_macro_stress_index
regional_macro_regime
```

后续航空需求层可优先读取：

```text
regional_gdp_growth_pct
regional_income_index
consumer_confidence_index
regional_headline_inflation_pct
regional_currency_index
regional_energy_cost_pressure_index
regional_macro_stress_index
regional_macro_regime
```

## 与北美的主要差异

| 维度 | 北美 | 中国大陆 |
|---|---|---|
| 潜在增长 | 较低 | 较高 |
| 政策利率 | 接近全球美元体系 | 本地政策权重更高 |
| 股市财富效应 | 强 | 中低 |
| 信用传导 | 市场利差更直接 | 信贷/融资条件代理 |
| 汇率 | 美元体系主导 | 更平滑但有外部压力 |
| 能源冲击 | 中等 | 较强 |
| 政策托底 | 弱 | 强 |
| 基建脉冲 | 弱 | 中高 |

## 当前对账方式

当前仍使用 `single_region_soft_anchor`。

也就是说，中国大陆路径会被全球主路径轻微锚定，但不会被强行拉成全球平均。

真正的多区域加权对账需要等多个区域都完成后再启用：

```text
sum(region_weight * regional_value) ~= global_anchor
```

## 全球分岔传导

中国大陆当前不会单独抽事件。

如果全球分岔情景已经改变了全球 GDP、通胀、美元、HY、油价或股市，中国大陆会通过被动传导随之变化。

显式区域暴露已统一接入，设计见：

```text
../Regional_Branch_Transmission_Plan.md
```

中国大陆后续预计对这些分岔更敏感：

- `policy_mistake`
- `credit_crunch`
- `energy_crisis`
- `supply_chain_shock`
- `geopolitical_fragmentation`

对这些分岔中等敏感：

- `dollar_squeeze`
- `risk_asset_bull`
- `commodity_supercycle`

## 后续预留

后续中国大陆机场/航空层可以把这些宏观字段翻译成：

```text
domestic_business_travel_index
domestic_leisure_travel_index
outbound_travel_affordability_index
inbound_travel_pressure_index
airport_retail_spending_power_index
```

这些不属于当前区域宏观层，应该放到下一层区域航空需求。
