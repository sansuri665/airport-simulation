# Japan / Korea Regional Macro Layer

## 定位

日韩区域宏观层是亚洲成熟高收入经济体样板。

它和已经完成的北美、中国大陆、西欧/北欧形成对照：

```text
japan_korea
  -> 低潜在增长、高收入、能源进口敏感、短途国际和精品消费
```

本层只输出区域经济环境，不直接生成机场客流或机场收入。

## 运行入口

```powershell
py -3 .\airport\macro_layers\regional_macro_layer_sim.py --region japan_korea
```

默认输出：

```text
airport/output/regional_macro/japan_korea_regional_macro_seed_sweep.csv
airport/output/regional_macro/japan_korea_regional_macro_seed_sweep.json
airport/output/regional_macro/japan_korea_regional_macro_viewer_data.js
```

## 区域结构假设

- 成熟高收入，潜在增长低。
- 能源进口依赖高，油价和美元走强会推高成本。
- 通胀锚低于全球平均，但能源冲击时 headline 可以上行。
- 政策利率和长债收益率低于美元体系，全球利率只部分传导。
- 股市财富效应中等，弱于北美。
- 信用市场成熟，但整体信用弹性弱于新兴市场。
- 地缘风险对信心、能源和汇率压力有中等影响。

## 关键参数

```text
region_id = japan_korea
global_weight = 0.072
trend_growth_pct = 1.05
market_maturity = 0.90
international_exposure = 0.64
tourism_exposure = 0.45
business_exposure = 0.72
credit_sensitivity = 0.88
equity_wealth_sensitivity = 0.72
policy_rate_sensitivity = 0.72
currency_dollar_beta = 0.72
fx_management_strength = 0.35
energy_import_sensitivity = 1.32
commodity_export_sensitivity = 0.18
```

## 航空含义预留

后续区域航空需求层可以重点读取：

```text
regional_income_index
consumer_confidence_index
regional_currency_index
regional_energy_cost_pressure_index
regional_macro_stress_index
```

这些变量可以影响：

```text
short_haul_international_index
premium_retail_spending_power_index
outbound_travel_affordability_index
inbound_tourism_pressure_index
```

## 全球分岔传导

日韩不单独抽事件。

如果全球发生能源危机、美元挤兑、地缘碎片化或滞胀，日韩会先通过全球路径被动变化。显式区域暴露已统一接入：

```text
../Regional_Branch_Transmission_Plan.md
```

日韩预计对这些分岔更敏感：

- `energy_crisis`
- `dollar_squeeze`
- `stagflation`
- `geopolitical_fragmentation`
