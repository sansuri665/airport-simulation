# Global Policy Rate Layer Design

## 当前定位

`global_policy_rate_layer_sim.py` 是 GDP + 通胀之后的央行反应层。它读取同一 seed 下的 GDP、金融压力、通胀、事件占位和通胀反馈接口，生成全球政策利率、实际政策利率、QE/流动性状态以及未来金融市场要消费的政策冲击。

当前版本仍是单向组合：

- GDP 和通胀先生成。
- 央行层读取这些变量并生成政策反应。
- 政策层暂时不反向重算 GDP、通胀、美元、股债或石油。

## 输入来源

央行层读取以下字段：

| 字段 | 用途 |
| --- | --- |
| `headline_inflation_pct` | headline 通胀压力 |
| `core_inflation_pct` | 核心通胀压力 |
| `inflation_expectation_pct` | 名义中性利率和实际利率计算 |
| `monetary_tightening_pressure` | 通胀层给出的加息压力 |
| `monetary_easing_pressure` | 通胀层给出的宽松压力 |
| `inflation_to_policy_rate_impulse` | 通胀对政策利率的占位冲击 |
| `output_gap_pct` | Taylor-rule 需求项 |
| `potential_growth_pct` | 实际中性利率代理 |
| `financial_stress_index` | 金融压力导致的宽松需求 |
| `crisis_intensity` | 危机期快速降息和 QE 需求 |
| `policy_rate_impulse` | GDP 事件接口中预留的政策冲击 |

## 输出字段

| 字段 | 含义 |
| --- | --- |
| `global_policy_rate_pct` | 全球政策利率代理 |
| `policy_reaction_target_rate_pct` | 反应函数给出的目标政策利率 |
| `neutral_policy_rate_pct` | 名义中性政策利率代理 |
| `real_policy_rate_pct` | 政策利率减通胀预期 |
| `shadow_policy_rate_pct` | 扣除 QE 流动性后的影子政策利率 |
| `policy_rate_change_pct` | 当年政策利率变化 |
| `rate_hike_pressure` | 加息压力，0-100 |
| `rate_cut_pressure` | 降息压力，0-100 |
| `qe_liquidity_index` | QE / 流动性支持指数，0-100 |
| `balance_sheet_impulse` | QE 指数年度变化 |
| `policy_stance_index` | 实际政策立场，越高越紧，越低越松 |
| `central_bank_reaction_regime` | 央行反应状态 |
| `policy_to_credit_tightening_impulse` | 未来信用层占位 |
| `policy_to_dollar_pressure_impulse` | 未来美元层占位 |
| `policy_to_equity_valuation_impulse` | 未来权益估值层占位 |
| `policy_to_gdp_drag_placeholder` | 未来 GDP 反馈占位 |
| `policy_to_inflation_lagged_impulse` | 未来通胀滞后反馈占位 |

## 央行状态

当前 `central_bank_reaction_regime` 可能包括：

- `initial`
- `emergency_easing`
- `stagflation_dilemma`
- `hawkish_tightening`
- `rate_cut_cycle`
- `qe_repair`
- `restrictive_pause`
- `inflation_watch`
- `dovish_support`
- `neutral_hold`
- `accommodative_hold`
- `mildly_restrictive`

## 反应函数简述

政策利率目标类似一个简化 Taylor rule：

```text
target_rate =
  neutral_policy_rate
  + headline_inflation_beta * headline_inflation_gap
  + core_inflation_beta * core_inflation_gap
  + output_gap_beta * output_gap
  + inflation_policy_impulse_beta * inflation_policy_impulse
  + event_policy_impulse_beta * event_policy_impulse
  + feedback_policy_impulse_beta * feedback_policy_impulse
  - financial_stress_easing
  - crisis_easing
```

这个公式在代码里对应 `policy_reaction_target_rate()`。`policy_reaction_target_rate_pct` 是反应函数的目标利率，`global_policy_rate_pct` 是考虑年度调整速度、最大加息/降息幅度之后真正执行的政策利率路径。危机强度高时允许更快降息。

QE / 流动性指数在两种情况下上升：

- 政策利率接近下限。
- 降息压力高、危机压力高，但利率工具不够。

## 反馈边界

单独运行当前政策层时，`policy_to_*` 字段仍然只是向后游传递。例如：

```json
{
  "global_policy_rate_pct": 4.25,
  "policy_stance_index": 1.10,
  "policy_to_credit_tightening_impulse": 0.52,
  "policy_to_dollar_pressure_impulse": 0.31,
  "policy_to_equity_valuation_impulse": -0.42,
  "policy_to_gdp_drag_placeholder": -0.20
}
```

这些字段是后续收益率曲线、美元、股债信用和 GDP 反馈层的接口。通过 `global_macro_feedback_calibration_sim.py` 运行完整栈时，政策层也会消费 `feedback_policy_impulse_pct`，并把政策拖累重新纳入下一轮 GDP、通胀和信用路径。

## 运行方式

```powershell
py -3 .\airport\global_policy_rate_layer_sim.py --years 60 --seed-count 8
```

默认输出：

- `airport/output/global_macro/global_policy_rate_seed_sweep.csv`
- `airport/output/global_macro/global_policy_rate_seed_sweep.json`
- `airport/output/global_macro/global_policy_viewer_data.js`
- `airport/output/global_macro/global_policy_rate_curves.svg`

## 后续方向

下一层建议做长端利率 / 收益率曲线层。它应读取：

- `global_policy_rate_pct`
- `neutral_policy_rate_pct`
- `real_policy_rate_pct`
- `qe_liquidity_index`
- `policy_to_dollar_pressure_impulse`
- `inflation_to_long_rate_impulse`
- `financial_stress_index`

然后生成短端、长端、期限利差、实际长端利率和债券价格代理。
