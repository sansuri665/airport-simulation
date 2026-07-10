# Global Regional Macro Layer Design

> 架构入口见 `../README.md`。本文件保留为区域宏观层的详细设计草案；路线图和校准计划分别整理在 `Regional_Macro_Roadmap.md` 与 `Regional_Macro_Reconciliation_Plan.md`。

## 当前定位

区域宏观层用于把已经完成的全球宏观路径，转成不同地区的经济环境。

它不是 14 套完整国家宏观模型，而是：

```text
Global macro path
  -> regional sensitivity / structure
  -> regional macro path
  -> aviation demand layer
  -> airport passenger business
```

全球宏观负责大周期，区域宏观负责差异化。航空直接变量，例如商务出行、旅游出行、国际开放、航司运力，暂时不放在本层，后面单独做区域航空需求层。

## 区域结构性 seed 势能

v0.3 增加 `regional-structural-seed-v0.1`。它解决一个根子问题：如果只靠固定区域参数和普通随机冲击，不同 seed 下区域长期排序会过于接近，玩家很快会记住“固定答案”。

区域 seed 势能不是短期事件，而是一条隐藏的长期世界线。每个 seed 会为 14 个区域生成可复现的结构性倾向：

```text
regional_seed_momentum_label
regional_seed_effective_growth_bias_pct
regional_seed_aviation_propensity_bias_pct
regional_seed_investment_cycle_bias_pct
regional_seed_openness_bias_pct
regional_seed_demand_multiplier
```

它会逐年释放，主要影响：

- 区域潜在增长和长期 GDP 份额。
- 区域投资周期、开放度和信心。
- 区域航空需求层里的旅游、商务、长航线和中转倾向。

设计边界：

- 不能让所有区域同时开挂。区域对账层仍然把 14 区总量拉回全球 GDP 锚。
- 不应把成熟区域和新兴区域完全打乱。北美、中国大陆、西北欧、南亚等初始体量和现实基准仍然重要。
- 但不同 seed 可以出现明显世界线差异：北美科技周期强势、中国大陆高增长、欧洲再工业化、南亚/东南亚跃迁、非洲城市化追赶等。

## 14 个大区

| region_id | 中文名称 | 主要运营意义 |
|---|---|---|
| `china_mainland` | 中国大陆 | 超大国内市场、省会网络、商务与旅游混合、宏观政策敏感 |
| `hk_macao_taiwan` | 港澳台 | 国际中转、金融商务、免税、高价值短途国际 |
| `japan_korea` | 日韩 | 成熟高收入、短途国际、精品消费、稳定商务与旅游 |
| `southeast_asia` | 东南亚 | 高增长、旅游、低成本航空、区域中转 |
| `south_asia_india` | 南亚/印度 | 长期高增长、人口红利、收入约束、基础设施约束 |
| `middle_east_gulf` | 中东/海湾 | 超级中转、长途联程、油价相关、高端服务 |
| `central_asia_turkey_eurasia` | 中亚/土耳其/欧亚桥 | 欧亚连接、地缘扰动、中转和边缘枢纽 |
| `west_north_europe` | 西欧/北欧 | 成熟商务、高收入、长途国际、高票价市场 |
| `south_east_europe_mediterranean` | 南欧/东欧/地中海 | 旅游、季节性、价格敏感、欧洲休闲需求 |
| `north_america` | 北美 | 巨大国内市场、商务、留学、远程航线、利率敏感 |
| `latin_america_caribbean` | 拉美/加勒比 | 旅游、侨民探亲、汇率波动、周期弹性 |
| `oceania` | 大洋洲 | 长途旅游、留学、资源经济、季节性 |
| `north_africa` | 北非 | 欧洲旅游外溢、中东/非洲连接、价格敏感 |
| `sub_saharan_africa` | 撒哈拉以南非洲 | 长期增长、航线不足、收入约束、枢纽潜力 |

## 字段原则

区域宏观字段应该对齐全球宏观面板，但保持轻量。

当前全球面板包含：

```text
GDP / 增长
通胀
政策利率
10Y / 收益率曲线
美元 / 流动性
信用
资产
石油 / 商品
反馈强度
叙事 / 分岔风险
```

区域宏观 v0.1 先覆盖前 8 类，不做区域叙事和分岔事件。叙事/分岔可以后续复用全球层逻辑。

## 区域宏观字段

### 1. 区域增长

```text
region_id
region_name
year

regional_gdp_index
regional_gdp_growth_pct
regional_potential_growth_pct
regional_output_gap_pct
regional_financial_stress_index
regional_growth_regime
```

用途：

- 决定区域经济活跃度。
- 后续传给商务出行、居民旅游、机场扩建信心。

### 2. 区域通胀

```text
regional_headline_inflation_pct
regional_core_inflation_pct
regional_energy_inflation_pct
regional_import_inflation_pct
regional_inflation_expectation_pct
regional_inflation_regime
```

用途：

- 影响真实收入、消费信心和票价承受力。
- 与油价、汇率、区域需求联动。

### 3. 区域收入与消费能力

```text
regional_income_index
real_income_growth_pct
household_consumption_power_index
consumer_confidence_index
```

用途：

- 连接宏观和客运需求的核心桥梁。
- 以后可以直接影响 leisure / outbound / premium travel。

### 4. 区域政策与利率

```text
regional_policy_rate_pct
regional_real_policy_rate_pct
regional_10y_yield_pct
regional_real_10y_yield_pct
regional_term_spread_pct
regional_financial_conditions_index
```

用途：

- 影响机场融资、基建投资、航司融资和资产估值。
- 对成熟市场和高债务区域尤其重要。

说明：

- 不必每个大区都有真实独立央行。
- 欧元区、海湾、东南亚这类区域可以使用加权区域利率。

### 5. 区域货币与流动性

```text
regional_currency_index
regional_currency_yoy_pct
currency_pressure_index
fx_volatility_index
regional_liquidity_index
regional_risk_appetite_index
```

用途：

- 影响出境购买力、进口通胀、国际旅行成本。
- 新兴市场区域对美元强弱更敏感。

### 6. 区域信用

```text
regional_ig_spread_bps
regional_hy_spread_bps
regional_credit_availability_index
regional_default_risk_index
regional_credit_stress_index
```

用途：

- 影响航司扩张、机场融资、商业地产和投资节奏。
- 后续可以传导到机场项目融资成本。

### 7. 区域资产

```text
regional_equity_index
regional_equity_return_pct
regional_bond_index
regional_bond_return_pct
regional_wealth_effect_index
```

用途：

- 股市和财富效应影响高端旅行、商务舱、免税与奢侈消费。
- 债券指数不一定马上展示，但能补全利率/资产层。

### 8. 区域能源与贸易条件

```text
regional_energy_cost_pressure_index
regional_terms_of_trade_index
regional_commodity_pressure_index
```

用途：

- 油价是全球变量，但区域暴露不同。
- 中东/资源经济体可能受益，欧洲、日本、印度等进口区域更受压。

### 9. 区域状态

```text
regional_macro_stress_index
regional_policy_uncertainty_index
regional_geopolitical_risk_index
regional_macro_regime
```

用途：

- 给区域事件、旅游信心、安全溢价和航线恢复留接口。
- v0.1 可以轻量生成，不需要复杂事件系统。

## 最小可行字段

如果 v0.1 想先小步跑通，可以先只做这些：

```text
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

这组字段已经足够从全球宏观传到区域航空需求。

## 区域参数

每个区域不需要独立写复杂公式，而是配置一组敏感度：

```text
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
```

示例：

- 中国大陆：国内权重高、政策敏感、消费信心重要。
- 港澳台：国际暴露高、金融和免税敏感、货币/资产敏感。
- 日韩：收入高、成熟、汇率和旅游敏感。
- 东南亚：趋势增长高、旅游暴露高、价格敏感。
- 南亚/印度：趋势增长高、收入约束强、容量约束强。
- 中东/海湾：中转和油价暴露高、收入高、政策/地缘敏感。
- 北美：成熟、国内大盘大、利率和消费敏感。
- 欧洲：成熟、能源和政策不确定性敏感。
- 非洲：趋势潜力高，但收入和供给约束强。

## 与航空需求层的边界

区域宏观层不直接输出：

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

这些应属于下一层“区域航空需求层”。

原因：

- 区域宏观负责经济环境。
- 区域航空需求负责把经济环境翻译成客运需求。
- 机场层再根据机场属性分流。

## 建议实现顺序

1. 创建 14 区静态配置表。已完成。
2. 从全球宏观读取 GDP、通胀、政策、10Y、美元、流动性、信用、资产、油价。
3. 用区域敏感度生成区域宏观路径。
4. 输出 CSV/JSON/JS。
5. 做一个区域宏观 viewer 或先接入现有总览。
6. 下一步再做区域航空需求层。
