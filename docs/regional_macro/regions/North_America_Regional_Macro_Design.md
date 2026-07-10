# North America Regional Macro Layer

## 定位

北美区域宏观层是 14 区域宏观的第一个可运行样板。

它不直接生成机场客流，也不直接决定机场收入。它只把全球宏观路径翻译成北美的区域经济环境：

```text
Global macro feedback path
  -> North America regional sensitivity
  -> single-region soft anchor
  -> regional macro path
```

当前口径把北美视为美元体系主导区域，主要由美国周期决定，同时隐含加拿大和墨西哥的贸易/能源暴露。

## 运行入口

```powershell
python .\airport\macro_layers\regional_macro_layer_sim.py --region north_america
```

默认输出：

```text
airport/output/regional_macro/north_america_regional_macro_seed_sweep.csv
airport/output/regional_macro/north_america_regional_macro_seed_sweep.json
airport/output/regional_macro/north_america_regional_macro_viewer_data.js
```

## 北美结构假设

北美 v0.1 的核心特征：

- 成熟高收入市场，长期潜在增长低于全球平均。
- 利率敏感度较高，政策利率和 10Y 利率接近美元体系。
- 信用和股债资产市场成熟，HY 利差、股市、债券回报对宏观压力反应明显。
- 财富效应强，股债回报会影响信心、消费能力和收入压力。
- 油价会提高能源成本，但北美不是单纯油价进口受损区域，因此能源冲击不会按欧洲/日韩那样放大。
- 美元强弱对北美本币压力较小，但美元波动仍会进入金融条件、资产和进口价格。

参数集中在 `RegionalMacroParams`：

```text
global_weight = 0.285
trend_growth_pct = 1.85
market_maturity = 0.93
domestic_demand_weight = 0.82
international_exposure = 0.42
oil_sensitivity = 0.56
credit_sensitivity = 0.94
equity_wealth_sensitivity = 1.18
policy_rate_sensitivity = 1.12
reconciliation_sensitivity = 0.82
```

## 输出字段

北美层覆盖区域路线图里的 v0.1 主字段：

```text
regional_gdp_index
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

并额外输出：

```text
regional_core_inflation_pct
regional_credit_availability_index
regional_default_risk_index
regional_bond_index
regional_wealth_effect_index
regional_terms_of_trade_index
regional_policy_uncertainty_index
regional_geopolitical_risk_index
```

这些字段足够给下一层区域航空需求使用，但目前仍保持宏观层边界，不生成：

```text
business_travel_index
leisure_travel_index
international_openness_index
ticket_affordability_index
aviation_demand_index
```

## 当前对账方式

14 区静态路径已经完成，独立区域对账层已经输出 `weighted_14_region_soft_reconciliation`。

当前使用的是 `single_region_soft_anchor`：

```text
regional_raw_value
  + (global_anchor - regional_raw_value)
    * anchor_strength
```

这个步骤只做轻微拉回，避免北美路径脱离全球大周期，同时保留本地差异。

输出中的这些字段用于后续升级：

```text
regional_reconciliation_scope
regional_reconciliation_adjustment_index
growth_reconciliation_adjustment_pct
inflation_reconciliation_adjustment_pct
rate_reconciliation_adjustment_pct
credit_reconciliation_adjustment_bps
equity_reconciliation_adjustment_pct
```

等 14 个区域都完成后，这些字段可以接入真正的加权对账：

```text
sum(region_weight * regional_value) ~= global_anchor
```

## 与全球层的关系

北美层读取全球层的关键锚：

```text
realized_growth_pct
output_gap_pct
headline_inflation_pct
core_inflation_pct
global_policy_rate_pct
global_10y_yield_pct
global_dollar_index
global_liquidity_index
global_financial_conditions_index
risk_appetite_index
global_high_yield_spread_bps
global_equity_index
sovereign_bond_total_return_pct
brent_oil_price_usd
energy_cost_pressure_index
macro_feedback_intensity_index
```

全球层负责大周期，北美层负责把这些变量变成区域口径。

## 全球分岔传导

当前北美层会被动响应全球路径。

如果全球分岔情景已经改变了全球 GDP、通胀、美元、HY、股市或油价，北美区域宏观会随之改变。

北美层不单独抽事件，但已经接入显式 `branch_transmission` 字段。`watch` 状态显示潜在相对传导；当 orchestrator 生成 `occurred` / `counterfactual` 状态时，北美会按暴露系数承接额外区域冲击。相关设计记录在：

```text
../Regional_Branch_Transmission_Plan.md
```

北美预计对这些分岔更敏感：

- `credit_crunch`
- `policy_mistake`
- `risk_asset_bull`

对这些分岔中等或较低敏感：

- `energy_crisis`
- `dollar_squeeze`

## 后续预留

后面补其他区域时，建议继续复用同一个脚本和字段：

```text
REGION_CONFIGS
  north_america
  china_mainland
  west_north_europe
  hk_macao_taiwan
  southeast_asia
  middle_east_gulf
  oceania
  south_east_europe_mediterranean
  central_asia_turkey_eurasia
  north_africa
  latin_america_caribbean
  sub_saharan_africa
  ...
```

下一步可以选择：

1. 补中国大陆区域宏观。
2. 补西欧/北欧区域宏观。
3. 先做多区域加权对账器。
4. 做区域宏观 viewer，把当前全球面板切到区域模式。
