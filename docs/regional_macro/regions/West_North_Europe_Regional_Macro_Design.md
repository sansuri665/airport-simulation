# West / North Europe Regional Macro Layer

## 定位

西欧/北欧区域宏观层是 14 区域宏观的第三个可运行样板。

它补上了成熟高收入、欧洲能源暴露、长途国际商务和旅游市场：

```text
north_america
  -> 美元体系、股债财富效应、信用市场

china_mainland
  -> 政策/信用/基建托底、内需大盘、能源进口压力

west_north_europe
  -> 成熟低增长、能源进口敏感、欧元/英镑利率、旅游和商务混合
```

本层仍然只输出区域经济环境，不直接生成机场客流或机场收入。

## 运行入口

```powershell
py -3 .\airport\macro_layers\regional_macro_layer_sim.py --region west_north_europe
```

默认输出：

```text
airport/output/regional_macro/west_north_europe_regional_macro_seed_sweep.csv
airport/output/regional_macro/west_north_europe_regional_macro_seed_sweep.json
airport/output/regional_macro/west_north_europe_regional_macro_viewer_data.js
```

## 区域结构假设

西欧/北欧 v0.1 的核心特征：

- 成熟高收入，长期潜在增长低于全球平均。
- 国际暴露高，商务、旅游、跨境贸易和长途航线重要。
- 能源进口暴露高，油价和能源成本对通胀、消费能力和贸易条件影响更强。
- 政策利率和 10Y 利率接近全球成熟市场，但不是完全美元口径。
- 信用市场成熟，HY/IG 利差可以作为融资压力代理。
- 股市财富效应存在，但弱于北美。
- 汇率为欧元、英镑、瑞郎、北欧货币等综合口径，美元走强会带来进口/金融压力。
- 政策托底存在，但弱于中国大陆，不应完全抹平能源和信用冲击。

## 关键参数

参数集中在 `RegionalMacroParams`：

```text
region_id = west_north_europe
global_weight = 0.165
trend_growth_pct = 1.38
market_maturity = 0.91
domestic_demand_weight = 0.70
international_exposure = 0.68
tourism_exposure = 0.54
business_exposure = 0.78
credit_sensitivity = 0.98
equity_wealth_sensitivity = 0.82
policy_rate_sensitivity = 1.04
geopolitical_sensitivity = 0.58
policy_global_beta = 0.72
long_rate_global_beta = 0.70
currency_dollar_beta = 0.62
energy_import_sensitivity = 1.36
commodity_export_sensitivity = 0.22
```

这些参数让西欧/北欧更像成熟低增长区域：普通年份较稳，能源危机、美元压力和信用冲击会更容易压低增长和消费信心。

## 政策和利率口径

`regional_policy_rate_pct` 不是某一个单一央行利率。

它是区域加权口径，大致代表：

```text
欧元区政策利率
+ 英国政策利率
+ 北欧主要经济体政策利率
+ 区域融资条件
```

`regional_10y_yield_pct` 同样是区域成熟市场长债收益率代理，不等于德国 10Y 或英国 10Y 的单一序列。

## 能源压力

西欧/北欧设置了较高的：

```text
energy_import_sensitivity = 1.36
commodity_export_sensitivity = 0.22
```

含义是：

- 油价/能源成本上行时，能源成本压力更强。
- 贸易条件更容易恶化。
- 通胀可能上行，但增长和消费能力受压。
- 商品超级周期不像资源经济体那样明显受益。

这会让西欧/北欧在 `energy_crisis` 或 `stagflation` 这类全球分岔中更有解释力。

## 输出字段

西欧/北欧沿用区域宏观统一字段：

```text
regional_gdp_index
regional_gdp_growth_pct
regional_potential_growth_pct
regional_output_gap_pct
regional_headline_inflation_pct
regional_core_inflation_pct
regional_income_index
consumer_confidence_index
regional_policy_rate_pct
regional_10y_yield_pct
regional_currency_index
regional_liquidity_index
regional_hy_spread_bps
regional_equity_index
regional_bond_index
regional_energy_cost_pressure_index
regional_terms_of_trade_index
regional_macro_stress_index
regional_macro_regime
```

后续航空需求层可优先读取：

```text
regional_gdp_growth_pct
regional_income_index
consumer_confidence_index
regional_currency_index
regional_energy_cost_pressure_index
regional_macro_stress_index
regional_macro_regime
```

## 与北美和中国大陆的主要差异

| 维度 | 北美 | 中国大陆 | 西欧/北欧 |
|---|---|---|---|
| 潜在增长 | 较低 | 较高 | 低 |
| 政策利率 | 美元体系 | 本地政策权重高 | 欧洲成熟市场加权 |
| 股市财富效应 | 强 | 中低 | 中等 |
| 能源冲击 | 中等 | 较强 | 强 |
| 汇率压力 | 美元体系主导 | 管理更强 | 欧元/英镑等综合 |
| 信用市场 | 成熟直接 | 融资条件代理 | 成熟直接 |
| 政策托底 | 弱 | 强 | 中弱 |
| 航空含义 | 国内+商务+长途 | 国内大盘+出境潜力 | 高收入国际商务+旅游 |

## 当前对账方式

当前仍使用 `single_region_soft_anchor`。

也就是说，西欧/北欧会被全球主路径轻微锚定，但不会被强行拉成全球平均。

真正的多区域加权对账需要等更多区域完成后再启用：

```text
sum(region_weight * regional_value) ~= global_anchor
```

## 全球分岔传导

西欧/北欧当前不会单独抽事件。

如果全球分岔情景已经改变全球 GDP、通胀、美元、HY、油价或股市，西欧/北欧会通过被动传导随之变化。

显式区域暴露已统一接入，设计见：

```text
../Regional_Branch_Transmission_Plan.md
```

西欧/北欧后续预计对这些分岔更敏感：

- `energy_crisis`
- `stagflation`
- `geopolitical_fragmentation`
- `credit_crunch`
- `policy_mistake`

对这些分岔中等敏感：

- `dollar_squeeze`
- `risk_asset_bull`
- `fiscal_reflation`

## 后续预留

后续欧洲航空需求层可以把这些宏观字段翻译成：

```text
business_travel_index
intra_europe_leisure_index
long_haul_outbound_index
inbound_tourism_index
ticket_affordability_index
airport_retail_spending_power_index
```

这些不属于当前区域宏观层，应该放到下一层区域航空需求。
