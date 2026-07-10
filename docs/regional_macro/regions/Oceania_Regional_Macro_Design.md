# Oceania Regional Macro Layer

## 定位

大洋洲区域宏观层是高收入、长途旅游、留学和资源经济市场样板。

```text
oceania
  -> 长途旅游、留学、资源周期、高收入消费、远程航线、季节性需求
```

本层只输出区域经济环境，不直接生成机场客流或机场商业收入。

## 运行入口

```powershell
py -3 .\airport\macro_layers\regional_macro_layer_sim.py --region oceania
```

默认输出：

```text
airport/output/regional_macro/oceania_regional_macro_seed_sweep.csv
airport/output/regional_macro/oceania_regional_macro_seed_sweep.json
airport/output/regional_macro/oceania_regional_macro_viewer_data.js
```

## 区域结构假设

- 收入水平高、市场成熟，长期增长介于北美/欧洲和高增长亚洲之间。
- 国际暴露和旅游暴露高，远程航线、留学和入境旅游对全球周期敏感。
- 资源出口会改善商品周期中的贸易条件，但能源和进口成本仍会影响通胀。
- 汇率较自由，美元周期会影响出境消费能力和入境旅游吸引力。
- 利率敏感度较高，房地产和家庭部门会放大紧缩周期。
- 地缘风险直接暴露低于东亚和中东，但会通过全球航线和贸易间接传导。

## 关键参数

```text
region_id = oceania
global_weight = 0.028
trend_growth_pct = 2.18
market_maturity = 0.84
international_exposure = 0.74
tourism_exposure = 0.70
business_exposure = 0.54
credit_sensitivity = 0.90
equity_wealth_sensitivity = 0.78
policy_rate_sensitivity = 1.02
currency_dollar_beta = 0.70
fx_management_strength = 0.18
energy_import_sensitivity = 0.72
commodity_export_sensitivity = 0.92
```

## 航空含义预留

后续区域航空需求层可以重点读取：

```text
regional_gdp_growth_pct
regional_income_index
household_consumption_power_index
regional_currency_index
regional_terms_of_trade_index
regional_macro_stress_index
```

这些变量可以影响：

```text
long_haul_leisure_index
student_travel_index
resource_cycle_business_travel_index
inbound_tourism_index
outbound_affordability_index
seasonal_route_resilience_index
```

## 全球分岔传导

大洋洲不单独抽事件。

如果全球发生商品超级周期、美元挤兑、软着陆、风险资产牛市或信用紧缩，大洋洲会先通过全球路径被动变化。显式区域暴露已统一接入：

```text
../Regional_Branch_Transmission_Plan.md
```

大洋洲预计对这些分岔更敏感：

- `commodity_supercycle`
- `dollar_squeeze`
- `soft_landing_success`
- `risk_asset_bull`
- `credit_crunch`
