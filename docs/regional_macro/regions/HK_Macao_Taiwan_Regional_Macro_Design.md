# HK Macao Taiwan Regional Macro Layer

## 定位

港澳台区域宏观层是高收入、小型开放经济体和高价值短途国际市场样板。

```text
hk_macao_taiwan
  -> 国际中转、金融商务、免税、奢侈品、精品、电子产品、高价值短途国际
```

本层只输出区域经济环境，不直接生成机场客流或机场商业收入。

## 运行入口

```powershell
py -3 .\airport\macro_layers\regional_macro_layer_sim.py --region hk_macao_taiwan
```

默认输出：

```text
airport/output/regional_macro/hk_macao_taiwan_regional_macro_seed_sweep.csv
airport/output/regional_macro/hk_macao_taiwan_regional_macro_seed_sweep.json
airport/output/regional_macro/hk_macao_taiwan_regional_macro_viewer_data.js
```

## 区域结构假设

- 收入水平高，消费客单价高，但长期潜在增长低于新兴亚洲。
- 国际暴露、旅游暴露和商务暴露都高，适合承接免税、精品和高价值短途国际需求。
- 区域汇率和利率部分锚定美元/全球金融条件，但并非完全自由浮动。
- 油价和进口成本对通胀、消费信心和旅游承受能力有明显压力。
- 地缘和跨境政策变化会影响商务、旅游和中转节奏。
- 股市和房地产财富效应比东南亚、南亚更强，但弱于北美。

## 关键参数

```text
region_id = hk_macao_taiwan
global_weight = 0.035
trend_growth_pct = 1.82
market_maturity = 0.86
international_exposure = 0.88
tourism_exposure = 0.78
business_exposure = 0.76
credit_sensitivity = 0.96
equity_wealth_sensitivity = 0.86
policy_rate_sensitivity = 0.90
currency_dollar_beta = 0.54
fx_management_strength = 0.55
energy_import_sensitivity = 1.16
commodity_export_sensitivity = 0.12
```

## 航空含义预留

后续区域航空需求层可以重点读取：

```text
regional_income_index
household_consumption_power_index
consumer_confidence_index
regional_currency_index
regional_liquidity_index
regional_macro_stress_index
```

这些变量可以影响：

```text
duty_free_spend_index
luxury_boutique_demand_index
electronics_retail_demand_index
financial_business_travel_index
cross_border_short_haul_index
transfer_premium_index
```

## 全球分岔传导

港澳台不单独抽事件。

如果全球发生美元挤兑、信用紧缩、风险资产牛市、地缘碎片化或软着陆，港澳台会先通过全球路径被动变化。显式区域暴露已统一接入：

```text
../Regional_Branch_Transmission_Plan.md
```

港澳台预计对这些分岔更敏感：

- `dollar_squeeze`
- `credit_crunch`
- `risk_asset_bull`
- `geopolitical_fragmentation`
- `soft_landing_success`
