# Sub Saharan Africa Regional Macro Layer

## 定位

撒哈拉以南非洲区域宏观层是长期增长、航线不足、收入约束和枢纽潜力市场样板。

```text
sub_saharan_africa
  -> 长期增长、航线不足、收入约束、容量追赶、枢纽潜力、美元融资压力
```

本层只输出区域经济环境，不直接生成机场客流或机场商业收入。

## 运行入口

```powershell
py -3 .\airport\macro_layers\regional_macro_layer_sim.py --region sub_saharan_africa
```

默认输出：

```text
airport/output/regional_macro/sub_saharan_africa_regional_macro_seed_sweep.csv
airport/output/regional_macro/sub_saharan_africa_regional_macro_seed_sweep.json
airport/output/regional_macro/sub_saharan_africa_regional_macro_viewer_data.js
```

## 区域结构假设

- 长期增长潜力高，但收入水平、金融深度和基础设施约束明显。
- 国内需求权重高，航空需求会随收入和城市化缓慢抬升。
- 航线不足和容量约束会让增长先表现为潜在需求，而不是立刻转成吞吐量。
- 美元走强会通过外债、燃油、进口成本和融资条件造成压力。
- 商品周期对部分经济体有利，但区域内部差异大，因此只作为中等正向贸易条件通道。
- 信用紧缩和地缘风险会更快压制投资、机场扩建和航司运力。

## 关键参数

```text
region_id = sub_saharan_africa
global_weight = 0.038
trend_growth_pct = 4.35
market_maturity = 0.32
international_exposure = 0.46
tourism_exposure = 0.28
business_exposure = 0.26
credit_sensitivity = 1.34
equity_wealth_sensitivity = 0.28
policy_rate_sensitivity = 0.92
currency_dollar_beta = 1.02
fx_management_strength = 0.12
energy_import_sensitivity = 0.88
commodity_export_sensitivity = 0.82
```

## 航空含义预留

后续区域航空需求层可以重点读取：

```text
regional_gdp_growth_pct
regional_potential_growth_pct
regional_income_index
household_consumption_power_index
regional_credit_availability_index
regional_currency_index
regional_macro_stress_index
```

这些变量可以影响：

```text
africa_capacity_catchup_index
underserved_route_potential_index
income_constrained_domestic_index
regional_hub_emergence_index
infrastructure_airport_investment_index
commodity_cycle_business_travel_index
```

## 全球分岔传导

撒哈拉以南非洲不单独抽事件。

如果全球发生美元挤兑、信用紧缩、能源危机、地缘碎片化或商品超级周期，撒哈拉以南非洲会先通过全球路径被动变化。显式区域暴露已统一接入：

```text
../Regional_Branch_Transmission_Plan.md
```

撒哈拉以南非洲预计对这些分岔更敏感：

- `dollar_squeeze`
- `credit_crunch`
- `energy_crisis`
- `geopolitical_fragmentation`
- `commodity_supercycle`
