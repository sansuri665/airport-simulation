# North Africa Regional Macro Layer

## 定位

北非区域宏观层是欧洲旅游外溢、中东/非洲连接和价格敏感增长市场样板。

```text
north_africa
  -> 欧洲旅游外溢、低收入价格敏感、中东/非洲连接、长期增长潜力
```

本层只输出区域经济环境，不直接生成机场客流或机场商业收入。

## 运行入口

```powershell
py -3 .\airport\macro_layers\regional_macro_layer_sim.py --region north_africa
```

默认输出：

```text
airport/output/regional_macro/north_africa_regional_macro_seed_sweep.csv
airport/output/regional_macro/north_africa_regional_macro_seed_sweep.json
airport/output/regional_macro/north_africa_regional_macro_viewer_data.js
```

## 区域结构假设

- 长期增长潜力高于欧洲成熟市场，但收入约束明显。
- 旅游暴露较高，欧洲休闲需求和汇率会影响入境客流。
- 美元走强会带来进口通胀、外债和融资压力。
- 能源和商品周期对不同经济体方向不完全一致，因此同时保留进口成本和出口收入通道。
- 地缘与政策不确定性较高，会影响旅游信心、航司运力和机场投资。
- 金融市场成熟度较低，信用紧缩会更快传导到消费和投资。

## 关键参数

```text
region_id = north_africa
global_weight = 0.022
trend_growth_pct = 3.65
market_maturity = 0.42
international_exposure = 0.68
tourism_exposure = 0.62
business_exposure = 0.32
credit_sensitivity = 1.25
equity_wealth_sensitivity = 0.38
policy_rate_sensitivity = 0.96
currency_dollar_beta = 0.88
fx_management_strength = 0.24
energy_import_sensitivity = 0.95
commodity_export_sensitivity = 0.52
```

## 航空含义预留

后续区域航空需求层可以重点读取：

```text
regional_gdp_growth_pct
regional_income_index
household_consumption_power_index
consumer_confidence_index
regional_currency_index
currency_pressure_index
regional_macro_stress_index
```

这些变量可以影响：

```text
north_africa_inbound_tourism_index
europe_leisure_spillover_index
price_sensitive_domestic_index
middle_east_africa_connection_index
airport_capacity_catchup_index
```

## 全球分岔传导

北非不单独抽事件。

如果全球发生美元挤兑、能源危机、信用紧缩、地缘碎片化或软着陆，北非会先通过全球路径被动变化。显式区域暴露已统一接入：

```text
../Regional_Branch_Transmission_Plan.md
```

北非预计对这些分岔更敏感：

- `dollar_squeeze`
- `energy_crisis`
- `credit_crunch`
- `geopolitical_fragmentation`
- `soft_landing_success`
