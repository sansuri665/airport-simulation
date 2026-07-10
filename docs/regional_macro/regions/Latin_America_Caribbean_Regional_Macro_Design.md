# Latin America Caribbean Regional Macro Layer

## 定位

拉美/加勒比区域宏观层是旅游、侨民探亲、汇率波动和商品周期弹性市场样板。

```text
latin_america_caribbean
  -> 旅游、侨民探亲、汇率波动、商品周期、周期弹性、价格敏感消费
```

本层只输出区域经济环境，不直接生成机场客流或机场商业收入。

## 运行入口

```powershell
py -3 .\airport\macro_layers\regional_macro_layer_sim.py --region latin_america_caribbean
```

默认输出：

```text
airport/output/regional_macro/latin_america_caribbean_regional_macro_seed_sweep.csv
airport/output/regional_macro/latin_america_caribbean_regional_macro_seed_sweep.json
airport/output/regional_macro/latin_america_caribbean_regional_macro_viewer_data.js
```

## 区域结构假设

- 潜在增长中等，高于成熟市场但低于南亚/印度和撒哈拉以南非洲。
- 旅游、侨民探亲和区域商务共同支撑航空需求。
- 美元走强会通过汇率、进口通胀、外债和融资条件传导。
- 商品周期可能改善贸易条件，但并不能完全抵消金融压力。
- 信用和政策利率对企业投资、消费信贷和航空需求有明显约束。
- 市场成熟度中等，资产财富效应存在但弱于北美和港澳台。

## 关键参数

```text
region_id = latin_america_caribbean
global_weight = 0.070
trend_growth_pct = 2.65
market_maturity = 0.52
international_exposure = 0.70
tourism_exposure = 0.66
business_exposure = 0.42
credit_sensitivity = 1.18
equity_wealth_sensitivity = 0.48
policy_rate_sensitivity = 1.02
currency_dollar_beta = 0.94
fx_management_strength = 0.14
energy_import_sensitivity = 0.70
commodity_export_sensitivity = 1.05
```

## 航空含义预留

后续区域航空需求层可以重点读取：

```text
regional_gdp_growth_pct
regional_income_index
household_consumption_power_index
regional_currency_index
currency_pressure_index
regional_terms_of_trade_index
regional_macro_stress_index
```

这些变量可以影响：

```text
latin_america_leisure_index
caribbean_inbound_tourism_index
diaspora_visiting_friends_relatives_index
commodity_cycle_business_travel_index
fx_sensitive_outbound_index
regional_low_cost_carrier_index
```

## 全球分岔传导

拉美/加勒比不单独抽事件。

如果全球发生美元挤兑、信用紧缩、商品超级周期、风险资产牛市或滞胀，拉美/加勒比会先通过全球路径被动变化。显式区域暴露已统一接入：

```text
../Regional_Branch_Transmission_Plan.md
```

拉美/加勒比预计对这些分岔更敏感：

- `dollar_squeeze`
- `credit_crunch`
- `commodity_supercycle`
- `stagflation`
- `soft_landing_success`
