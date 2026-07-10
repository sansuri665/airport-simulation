# Middle East Gulf Regional Macro Layer

## 定位

中东/海湾区域宏观层是超级中转、油价相关和高端长途联程市场样板。

```text
middle_east_gulf
  -> 超级中转、长途联程、油价收入、高端服务、奢侈零售、美元锚定金融条件
```

本层只输出区域经济环境，不直接生成机场客流或机场商业收入。

## 运行入口

```powershell
py -3 .\airport\macro_layers\regional_macro_layer_sim.py --region middle_east_gulf
```

默认输出：

```text
airport/output/regional_macro/middle_east_gulf_regional_macro_seed_sweep.csv
airport/output/regional_macro/middle_east_gulf_regional_macro_seed_sweep.json
airport/output/regional_macro/middle_east_gulf_regional_macro_viewer_data.js
```

## 区域结构假设

- 潜在增长高于成熟市场，但更受投资周期、油价和地缘风险影响。
- 国际暴露极高，适合承接全球长途联程和超级中转机场网络。
- 油价上行会改善贸易条件和财政/投资能力，但并不等于没有通胀和地缘压力。
- 汇率和政策利率部分锚定美元，美元紧缩会传导到融资条件。
- 基建和政策托底能力较强，危机后可能通过投资修复需求。
- 高端商业、奢侈品和中转消费对全球风险偏好、财富效应和航线连通性敏感。

## 关键参数

```text
region_id = middle_east_gulf
global_weight = 0.045
trend_growth_pct = 3.25
market_maturity = 0.72
international_exposure = 0.88
tourism_exposure = 0.58
business_exposure = 0.70
credit_sensitivity = 0.92
equity_wealth_sensitivity = 0.70
policy_rate_sensitivity = 0.82
currency_dollar_beta = 0.46
fx_management_strength = 0.62
energy_import_sensitivity = 0.36
commodity_export_sensitivity = 1.55
```

## 航空含义预留

后续区域航空需求层可以重点读取：

```text
regional_gdp_growth_pct
regional_income_index
regional_currency_index
regional_liquidity_index
regional_terms_of_trade_index
regional_geopolitical_risk_index
regional_macro_stress_index
```

这些变量可以影响：

```text
mega_hub_transfer_index
long_haul_connection_index
premium_retail_spend_index
luxury_service_demand_index
oil_income_travel_impulse
fleet_and_airport_capex_impulse
```

## 全球分岔传导

中东/海湾不单独抽事件。

如果全球发生能源危机、美元挤兑、地缘碎片化、商品超级周期或风险资产牛市，中东/海湾会先通过全球路径被动变化。显式区域暴露已统一接入：

```text
../Regional_Branch_Transmission_Plan.md
```

中东/海湾预计对这些分岔更敏感：

- `energy_crisis`
- `commodity_supercycle`
- `dollar_squeeze`
- `geopolitical_fragmentation`
- `risk_asset_bull`
