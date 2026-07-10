# Global Macro Layer Index

## 当前定位

全球宏观层是机场游戏的外部世界引擎。它负责生成全球经济周期、通胀、利率、美元、信用、资产、能源和风险分岔，不直接决定单个机场客流。

当前推荐入口不是单个全球脚本，而是完整编排脚本：

```powershell
py -3 .\airport\macro_layers\macro_run_orchestrator_sim.py --random-seed
```

底层全球脚本仍可单独调试：

```powershell
py -3 .\airport\macro_layers\global_macro_feedback_calibration_sim.py
```

## 主链条

```text
GDP / Cycle
  -> Inflation
  -> Policy Rate / QE
  -> Yield Curve
  -> Dollar / Liquidity
  -> Credit / Banking Stress
  -> Asset Prices
  -> Oil / Commodity
  -> Feedback Calibration
  -> Narrative
  -> Branch Risk
```

orchestrator 会在全球链条之后继续执行：

```text
optional occurred / counterfactual branch path
  -> 14 regional macro paths
  -> regional reconciliation and GDP levels
  -> optional viewer publish
```

## 分层索引

| 层级 | 脚本 | 文档 | 主要意义 |
|---|---|---|---|
| Run orchestration | `../../macro_layers/macro_run_orchestrator_sim.py` | `Macro_Run_Orchestration.md` | 一键生成 baseline、scenario、14 区和对账输出 |
| GDP / 周期 | `../../macro_layers/global_gdp_annual_sim.py` | 暂无单独汇总文档 | 全球 GDP、潜在增长、产出缺口、金融压力 |
| 通胀 | `../../macro_layers/global_inflation_annual_sim.py` | `Global_Inflation_Layer_Design.md` | headline/core/能源/进口通胀、通胀预期 |
| 政策利率 | `../../macro_layers/global_policy_rate_layer_sim.py` | `Global_Policy_Rate_Layer_Design.md` | 政策利率、真实政策利率、QE、央行反应 |
| 收益率曲线 | `../../macro_layers/global_yield_curve_layer_sim.py` | `Global_Yield_Curve_Layer_Design.md` | 2Y、10Y、期限利差、期限溢价 |
| 美元/流动性 | `../../macro_layers/global_dollar_liquidity_layer_sim.py` | `Global_Dollar_Liquidity_Layer_Design.md` | 美元指数、全球流动性、风险偏好、EM 压力 |
| 信用 | `../../macro_layers/global_credit_spread_layer_sim.py` | `Global_Credit_Spread_Layer_Design.md` | HY/IG 利差、银行放贷、信用疤痕、再融资压力 |
| 资产 | `../../macro_layers/global_asset_price_layer_sim.py` | `Global_Asset_Price_Layer_Design.md` | 股票、债券、60/40、估值、财富效应 |
| 石油/商品 | `../../macro_layers/global_oil_commodity_layer_sim.py` | `Global_Oil_Commodity_Layer_Design.md` | Brent、商品、能源成本压力、油价反馈 |
| 反馈校准 | `../../macro_layers/global_macro_feedback_calibration_sim.py` | `Global_Macro_Feedback_Calibration_Design.md` | 多轮 rerun、宏观闭环、收敛诊断 |
| 宏观叙事 | viewer 内实现 | `Global_Macro_Narrative_Layer_Design.md` | 解释金融危机、软着陆、能源危机等局面 |
| 分岔风险 | Python + viewer + orchestrator | `Global_Macro_Branch_Risk_Layer_Design.md` | 风险观察、发生路径、反事实路径 |
| 事件接口 | GDP stub | `Macro_Event_Interface_Stub.md` | 更外部的事件接口预留 |

## 主要输出

orchestrator 归档输出：

```text
../../output/macro_runs/<run_id>/
```

当前 viewer canonical 输出：

```text
../../output/global_macro/
../../output/regional_macro/
../../output/regional_macro_reconciled/
```

使用 `--publish-viewer baseline` 或 `--publish-viewer scenario` 时，orchestrator 会把指定路径复制到 canonical 输出。

## Viewer 面板

当前 viewer 展示：

```text
总览
GDP
增长
通胀
利率
10Y
美元
信用
资产
石油
区域
```

年度明细中已经包含：

```text
GDP、增长率、headline/core 通胀、政策利率、目标利率、真实政策利率、
10Y、期限利差、美元、流动性、金融条件、HY/IG、信用可得性、
股票、股票回报、PE、债券、Brent、油价 YoY、商品、能源压力、
反馈强度、潜在增长、产出缺口、金融压力、叙事、分岔风险。
```

## 对机场游戏最有用的全球变量

直接影响航空需求：

- GDP 增长和产出缺口。
- 通胀和真实收入压力。
- 油价/能源成本。
- 美元和汇率压力。
- 金融压力、信用状态和危机叙事。
- 股市和财富效应。

影响机场与航司经营：

- 政策利率和 10Y 利率。
- HY/IG 信用利差。
- 全球流动性和风险偏好。
- 再融资压力。
- 主权债/企业债环境。

影响游戏叙事：

- 宏观 regime。
- 叙事标签。
- 分岔风险 watchlist。
- occurred/counterfactual 路径。

## 当前边界

全球宏观层暂时不做：

- 国家级宏观。
- 多个分岔风险同时发生。
- 航空客运需求。
- 机场收入。

这些由后续层完成：

```text
Regional macro
Regional aviation demand
Airport passenger business
Airport commercial business
```

## 区域连接点

区域宏观主要读取：

```text
realized_growth_pct
output_gap_pct
headline_inflation_pct
core_inflation_pct
global_policy_rate_pct
global_10y_yield_pct
term_spread_10y_2y_pct
global_dollar_index
global_liquidity_index
global_financial_conditions_index
risk_appetite_index
global_high_yield_spread_bps
global_investment_grade_spread_bps
global_equity_index
sovereign_bond_total_return_pct
brent_oil_price_usd
energy_cost_pressure_index
macro_feedback_intensity_index
branch_risk_primary_id
scenario_risk_id
scenario_state
```

区域宏观不复制全球层所有细节，而是按区域敏感度生成差异化路径，再通过对账层校准回全球总量。
