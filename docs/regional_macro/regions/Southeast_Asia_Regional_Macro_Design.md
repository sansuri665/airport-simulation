# Southeast Asia Regional Macro Layer

## 定位

东南亚区域宏观层是高增长、旅游、中转和制造业外溢区域样板。

```text
southeast_asia
  -> 高增长、旅游恢复、低成本航空、区域中转、美元和资本流动敏感
```

本层只输出区域经济环境，不直接生成机场客流或机场收入。

## 运行入口

```powershell
py -3 .\airport\macro_layers\regional_macro_layer_sim.py --region southeast_asia
```

默认输出：

```text
airport/output/regional_macro/southeast_asia_regional_macro_seed_sweep.csv
airport/output/regional_macro/southeast_asia_regional_macro_seed_sweep.json
airport/output/regional_macro/southeast_asia_regional_macro_viewer_data.js
```

## 区域结构假设

- 潜在增长高于成熟市场。
- 国际暴露和旅游暴露高，全球需求和汇率会明显影响周期。
- 美元走强会带来资本流动、融资和进口成本压力。
- 政策有一定托底，但不能完全抵消外部融资冲击。
- 能源暴露中等偏高，部分经济体受益于商品周期，部分受进口成本约束。
- 股市财富效应弱于北美，消费更多取决于收入和旅游/就业修复。

## 关键参数

```text
region_id = southeast_asia
global_weight = 0.052
trend_growth_pct = 4.20
market_maturity = 0.58
international_exposure = 0.82
tourism_exposure = 0.78
business_exposure = 0.52
credit_sensitivity = 1.10
equity_wealth_sensitivity = 0.58
policy_rate_sensitivity = 0.88
currency_dollar_beta = 0.82
fx_management_strength = 0.32
energy_import_sensitivity = 0.95
commodity_export_sensitivity = 0.58
```

## 航空含义预留

后续区域航空需求层可以重点读取：

```text
regional_gdp_growth_pct
regional_income_index
consumer_confidence_index
regional_currency_index
regional_liquidity_index
regional_macro_stress_index
```

这些变量可以影响：

```text
intra_asia_leisure_index
low_cost_carrier_demand_index
hub_transfer_index
inbound_tourism_index
outbound_affordability_index
```

## 全球分岔传导

东南亚不单独抽事件。

如果全球发生美元挤兑、能源危机、风险资产牛市或软着陆，东南亚会先通过全球路径被动变化。显式区域暴露已统一接入：

```text
../Regional_Branch_Transmission_Plan.md
```

东南亚预计对这些分岔更敏感：

- `dollar_squeeze`
- `energy_crisis`
- `risk_asset_bull`
- `soft_landing_success`
- `supply_chain_shock`
