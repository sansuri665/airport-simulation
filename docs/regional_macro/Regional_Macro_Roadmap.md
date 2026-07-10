# Regional Macro Roadmap

## 当前目标

区域宏观层用于把全球宏观转成 14 个大区的宏观路径。

它不是航空需求层，也不是机场层。它只回答：

```text
这个区域在这一年的经济、通胀、利率、货币、信用、资产和压力环境如何？
```

## 当前实现状态

已实现：

```text
north_america
china_mainland
west_north_europe
japan_korea
southeast_asia
south_asia_india
hk_macao_taiwan
middle_east_gulf
oceania
south_east_europe_mediterranean
central_asia_turkey_eurasia
north_africa
latin_america_caribbean
sub_saharan_africa
```

脚本：

```text
../../macro_layers/regional_macro_layer_sim.py
```

文档：

```text
regions/North_America_Regional_Macro_Design.md
regions/China_Mainland_Regional_Macro_Design.md
regions/West_North_Europe_Regional_Macro_Design.md
regions/Japan_Korea_Regional_Macro_Design.md
regions/Southeast_Asia_Regional_Macro_Design.md
regions/South_Asia_India_Regional_Macro_Design.md
regions/HK_Macao_Taiwan_Regional_Macro_Design.md
regions/Middle_East_Gulf_Regional_Macro_Design.md
regions/Oceania_Regional_Macro_Design.md
regions/South_East_Europe_Mediterranean_Regional_Macro_Design.md
regions/Central_Asia_Turkey_Eurasia_Regional_Macro_Design.md
regions/North_Africa_Regional_Macro_Design.md
regions/Latin_America_Caribbean_Regional_Macro_Design.md
regions/Sub_Saharan_Africa_Regional_Macro_Design.md
Regional_Branch_Transmission_Plan.md
```

当前 14 区版本已经输出 GDP、通胀、收入、政策利率、10Y、货币、流动性、信用、股债资产、能源压力、宏观状态和全球分岔传导字段。区域静态生成层仍保留 `single_region_soft_anchor`，独立对账层已经输出 `weighted_14_region_soft_reconciliation`。

全球分岔风险的区域传导见 `Regional_Branch_Transmission_Plan.md`。当前已接入 `regional-branch-transmission-v0.1`：区域层不单独抽事件，只读取全球 `branch_risk_primary_*` / `scenario_*` 字段，并按区域暴露矩阵输出相对传导。`scenario_*` 字段由 `macro_run_orchestrator_sim.py` 在 occurred / counterfactual 路径中写入。

## 14 个大区

| region_id | 中文名称 | 核心特征 |
|---|---|---|
| `china_mainland` | 中国大陆 | 超大国内市场、政策敏感、省会网络、商务与旅游混合 |
| `hk_macao_taiwan` | 港澳台 | 国际中转、金融商务、免税、高价值短途国际 |
| `japan_korea` | 日韩 | 成熟高收入、精品消费、短途国际、稳定商务与旅游 |
| `southeast_asia` | 东南亚 | 高增长、旅游、低成本航空、区域中转 |
| `south_asia_india` | 南亚/印度 | 人口红利、高增长、收入约束、基础设施约束 |
| `middle_east_gulf` | 中东/海湾 | 超级中转、油价相关、高端服务、长途联程 |
| `central_asia_turkey_eurasia` | 中亚/土耳其/欧亚桥 | 欧亚连接、地缘扰动、中转和边缘枢纽 |
| `west_north_europe` | 西欧/北欧 | 成熟商务、高收入、长途国际、高票价市场 |
| `south_east_europe_mediterranean` | 南欧/东欧/地中海 | 旅游、季节性、价格敏感、休闲需求 |
| `north_america` | 北美 | 巨大国内市场、商务、远程航线、利率敏感 |
| `latin_america_caribbean` | 拉美/加勒比 | 旅游、侨民探亲、汇率波动、周期弹性 |
| `oceania` | 大洋洲 | 长途旅游、留学、资源经济、季节性 |
| `north_africa` | 北非 | 欧洲旅游外溢、中东/非洲连接、价格敏感 |
| `sub_saharan_africa` | 撒哈拉以南非洲 | 长期增长、航线不足、收入约束、枢纽潜力 |

## 字段分组

### 1. 区域增长

```text
regional_gdp_index
regional_gdp_growth_pct
regional_potential_growth_pct
regional_output_gap_pct
regional_financial_stress_index
regional_growth_regime
```

### 2. 区域通胀

```text
regional_headline_inflation_pct
regional_core_inflation_pct
regional_energy_inflation_pct
regional_import_inflation_pct
regional_inflation_expectation_pct
regional_inflation_regime
```

### 3. 区域收入与消费能力

```text
regional_income_index
real_income_growth_pct
household_consumption_power_index
consumer_confidence_index
```

### 4. 区域政策与利率

```text
regional_policy_rate_pct
regional_real_policy_rate_pct
regional_10y_yield_pct
regional_real_10y_yield_pct
regional_term_spread_pct
regional_financial_conditions_index
```

### 5. 区域货币与流动性

```text
regional_currency_index
regional_currency_yoy_pct
currency_pressure_index
fx_volatility_index
regional_liquidity_index
regional_risk_appetite_index
```

### 6. 区域信用

```text
regional_ig_spread_bps
regional_hy_spread_bps
regional_credit_availability_index
regional_default_risk_index
regional_credit_stress_index
```

### 7. 区域资产

```text
regional_equity_index
regional_equity_return_pct
regional_bond_index
regional_bond_return_pct
regional_wealth_effect_index
```

### 8. 区域能源与贸易条件

```text
regional_energy_cost_pressure_index
regional_terms_of_trade_index
regional_commodity_pressure_index
```

### 9. 区域状态

```text
regional_macro_stress_index
regional_policy_uncertainty_index
regional_geopolitical_risk_index
regional_macro_regime
```

### 10. 全球分岔传导

```text
regional_branch_transmission_version
branch_scenario_id
branch_scenario_label
branch_scenario_state
branch_source_year
branch_impact_years
branch_tail_years
branch_year_in_effect
branch_effect_phase
regional_branch_transmission_active
regional_branch_exposure_index
regional_branch_relative_exposure_index
regional_branch_strength_index
regional_branch_growth_impulse_pct
regional_branch_inflation_impulse_pct
regional_branch_policy_impulse_pct
regional_branch_credit_impulse_bps
regional_branch_fx_pressure_impulse
regional_branch_energy_impulse
regional_branch_liquidity_impulse
regional_branch_asset_impulse_pct
regional_branch_confidence_impulse
regional_branch_tail_scarring_index
```

这些字段已经进入 v0.2 输出。`watch` 状态显示潜在相对传导，不改写 baseline 主路径；`occurred` / `counterfactual` 状态由 orchestrator 的全球发生路径写入，会把额外区域冲击施加到区域宏观变量。

## v0.1 最小可行字段

第一版可以先只输出：

```text
region_id
region_name
year
seed

regional_gdp_growth_pct
regional_output_gap_pct
regional_headline_inflation_pct
regional_income_index
consumer_confidence_index
regional_policy_rate_pct
regional_10y_yield_pct
regional_currency_index
regional_liquidity_index
regional_hy_spread_bps
regional_equity_index
regional_energy_cost_pressure_index
regional_macro_stress_index
regional_macro_regime
```

这组字段已经足够传给区域航空需求层。

## 区域参数

每个区域用参数表达结构差异：

```text
global_weight
trend_growth
income_level
market_maturity
domestic_demand_weight
international_exposure
tourism_exposure
business_exposure
oil_sensitivity
dollar_sensitivity
credit_sensitivity
equity_wealth_sensitivity
policy_rate_sensitivity
geopolitical_sensitivity
capacity_constraint
shock_volatility
reconciliation_sensitivity
```

## 与航空需求层的边界

区域宏观层暂时不输出：

```text
business_travel_index
leisure_travel_index
outbound_travel_index
inbound_tourism_index
airline_capacity_index
international_openness_index
ticket_affordability_index
aviation_demand_index
```

这些属于下一层区域航空需求。区域宏观只提供经济环境。

区域航空需求层总览见：

```text
../regional_aviation/Regional_Aviation_Demand_Layer_Overview.md
```

下一层会优先输出：

```text
regional_air_demand_index
regional_air_demand_growth_pct
business_travel_demand_index
leisure_travel_demand_index
vfr_travel_demand_index
long_haul_demand_index
transfer_demand_index
airfare_price_sensitivity_index
premium_passenger_propensity_index
duty_free_propensity_index
luxury_retail_propensity_index
electronics_retail_propensity_index
```

## 建议实现顺序

1. 建立 14 区静态配置。已完成。
2. 从全球宏观读取年度路径。
3. 按区域参数生成 raw regional macro。
4. 接入全球分岔的区域传导接口。已完成。
5. 做区域宏观对账/校准。已完成。
6. 输出 CSV/JSON/JS。已完成。
7. 做 viewer 区域模式和 run browser。已完成。
8. 再做区域航空需求层。
