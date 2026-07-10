# Central Asia Turkey Eurasia Regional Macro Layer

## 定位

中亚/土耳其/欧亚桥区域宏观层是欧亚连接、地缘扰动和边缘枢纽市场样板。

```text
central_asia_turkey_eurasia
  -> 欧亚桥、中转枢纽、地缘扰动、汇率波动、边缘市场增长
```

本层只输出区域经济环境，不直接生成机场客流或机场商业收入。

## 运行入口

```powershell
py -3 .\airport\macro_layers\regional_macro_layer_sim.py --region central_asia_turkey_eurasia
```

默认输出：

```text
airport/output/regional_macro/central_asia_turkey_eurasia_regional_macro_seed_sweep.csv
airport/output/regional_macro/central_asia_turkey_eurasia_regional_macro_seed_sweep.json
airport/output/regional_macro/central_asia_turkey_eurasia_regional_macro_viewer_data.js
```

## 区域结构假设

- 潜在增长中高，但金融市场成熟度低，波动显著。
- 国际暴露较高，欧亚中转、侨民探亲和区域商务都重要。
- 美元走强会带来汇率、进口通胀和融资压力。
- 地缘风险暴露高，可能改变航线绕飞、中转选择和边缘枢纽机会。
- 商品周期既能带来部分出口收入，也会通过能源和进口成本制造压力。
- 政策和基建托底存在，但不足以完全抵消外部融资冲击。

## 关键参数

```text
region_id = central_asia_turkey_eurasia
global_weight = 0.030
trend_growth_pct = 3.05
market_maturity = 0.50
international_exposure = 0.72
tourism_exposure = 0.50
business_exposure = 0.48
credit_sensitivity = 1.20
equity_wealth_sensitivity = 0.50
policy_rate_sensitivity = 1.05
currency_dollar_beta = 0.92
fx_management_strength = 0.18
energy_import_sensitivity = 0.86
commodity_export_sensitivity = 0.68
```

## 航空含义预留

后续区域航空需求层可以重点读取：

```text
regional_gdp_growth_pct
regional_currency_index
fx_volatility_index
regional_liquidity_index
regional_geopolitical_risk_index
regional_macro_stress_index
regional_terms_of_trade_index
```

这些变量可以影响：

```text
eurasia_bridge_transfer_index
istanbul_style_hub_index
rerouting_transfer_opportunity_index
diaspora_visiting_friends_relatives_index
regional_business_travel_index
fx_sensitive_outbound_index
```

## 全球分岔传导

中亚/土耳其/欧亚桥不单独抽事件。

如果全球发生美元挤兑、地缘碎片化、能源危机、商品超级周期或信用紧缩，中亚/土耳其/欧亚桥会先通过全球路径被动变化。显式区域暴露已统一接入：

```text
../Regional_Branch_Transmission_Plan.md
```

中亚/土耳其/欧亚桥预计对这些分岔更敏感：

- `dollar_squeeze`
- `geopolitical_fragmentation`
- `energy_crisis`
- `commodity_supercycle`
- `credit_crunch`
