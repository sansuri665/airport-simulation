# South Asia / India Regional Macro Layer

## 定位

南亚/印度区域宏观层是人口红利和长期增长区域样板。

```text
south_asia_india
  -> 高潜在增长、收入约束、基础设施约束、油价和美元压力强
```

本层只输出区域经济环境，不直接生成机场客流或机场收入。

## 运行入口

```powershell
py -3 .\airport\macro_layers\regional_macro_layer_sim.py --region south_asia_india
```

默认输出：

```text
airport/output/regional_macro/south_asia_india_regional_macro_seed_sweep.csv
airport/output/regional_macro/south_asia_india_regional_macro_seed_sweep.json
airport/output/regional_macro/south_asia_india_regional_macro_viewer_data.js
```

## 区域结构假设

- 潜在增长高，但收入水平和基础设施约束明显。
- 国内需求权重高，长期客运潜力大。
- 油价上行和美元走强会同时压制通胀、汇率和消费能力。
- 政策托底和基建脉冲较强，但市场成熟度低于北美/欧洲/日韩。
- 股市财富效应较弱，收入和票价可负担性更重要。
- 信用压力和外部融资压力会对增长形成滞后拖累。

## 关键参数

```text
region_id = south_asia_india
global_weight = 0.060
trend_growth_pct = 5.25
market_maturity = 0.48
domestic_demand_weight = 0.86
international_exposure = 0.50
credit_sensitivity = 1.22
equity_wealth_sensitivity = 0.48
policy_rate_sensitivity = 0.92
currency_dollar_beta = 0.88
fx_management_strength = 0.22
policy_support_sensitivity = 0.58
infrastructure_sensitivity = 0.60
energy_import_sensitivity = 1.28
commodity_export_sensitivity = 0.32
```

## 航空含义预留

后续区域航空需求层可以重点读取：

```text
regional_gdp_growth_pct
regional_income_index
household_consumption_power_index
regional_currency_index
regional_energy_cost_pressure_index
regional_macro_stress_index
```

这些变量可以影响：

```text
domestic_growth_travel_index
labor_and_vfr_travel_index
outbound_affordability_index
airport_capacity_pressure_index
price_sensitive_leisure_index
```

## 全球分岔传导

南亚/印度不单独抽事件。

如果全球发生美元挤兑、能源危机、信用紧缩或商品超级周期，南亚/印度会先通过全球路径被动变化。显式区域暴露已统一接入：

```text
../Regional_Branch_Transmission_Plan.md
```

南亚/印度预计对这些分岔更敏感：

- `dollar_squeeze`
- `energy_crisis`
- `credit_crunch`
- `stagflation`
- `commodity_supercycle`
