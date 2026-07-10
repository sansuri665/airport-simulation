# South East Europe Mediterranean Regional Macro Layer

## 定位

南欧/东欧/地中海区域宏观层是旅游、季节性、价格敏感和欧洲休闲需求样板。

```text
south_east_europe_mediterranean
  -> 旅游季节性、低成本航空、欧洲休闲需求、价格敏感、能源进口压力
```

本层只输出区域经济环境，不直接生成机场客流或机场商业收入。

## 运行入口

```powershell
py -3 .\airport\macro_layers\regional_macro_layer_sim.py --region south_east_europe_mediterranean
```

默认输出：

```text
airport/output/regional_macro/south_east_europe_mediterranean_regional_macro_seed_sweep.csv
airport/output/regional_macro/south_east_europe_mediterranean_regional_macro_seed_sweep.json
airport/output/regional_macro/south_east_europe_mediterranean_regional_macro_viewer_data.js
```

## 区域结构假设

- 潜在增长高于西欧/北欧，但低于东南亚和南亚/印度。
- 国际暴露和旅游暴露高，航空需求对欧洲休闲周期和汇率敏感。
- 能源进口压力较强，油价上行会压制实际收入和价格敏感客流。
- 信用和利率压力会影响旅游投资、酒店扩张和低成本航空需求。
- 地缘扰动和欧洲外围金融压力会放大周期波动。
- 股市财富效应弱于北美和港澳台，消费更多取决于收入、就业和旅游恢复。

## 关键参数

```text
region_id = south_east_europe_mediterranean
global_weight = 0.040
trend_growth_pct = 2.05
market_maturity = 0.62
international_exposure = 0.78
tourism_exposure = 0.86
business_exposure = 0.42
credit_sensitivity = 1.08
equity_wealth_sensitivity = 0.56
policy_rate_sensitivity = 0.96
currency_dollar_beta = 0.68
fx_management_strength = 0.20
energy_import_sensitivity = 1.20
commodity_export_sensitivity = 0.24
```

## 航空含义预留

后续区域航空需求层可以重点读取：

```text
regional_gdp_growth_pct
regional_income_index
household_consumption_power_index
consumer_confidence_index
regional_currency_index
regional_energy_cost_pressure_index
regional_macro_stress_index
```

这些变量可以影响：

```text
mediterranean_leisure_index
low_cost_carrier_demand_index
seasonal_tourism_peak_index
price_sensitive_outbound_index
hotel_and_resort_air_demand_index
```

## 全球分岔传导

南欧/东欧/地中海不单独抽事件。

如果全球发生能源危机、信用紧缩、美元挤兑、滞胀或软着陆，南欧/东欧/地中海会先通过全球路径被动变化。显式区域暴露已统一接入：

```text
../Regional_Branch_Transmission_Plan.md
```

南欧/东欧/地中海预计对这些分岔更敏感：

- `energy_crisis`
- `credit_crunch`
- `dollar_squeeze`
- `stagflation`
- `soft_landing_success`
