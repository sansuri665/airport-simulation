# Global Macro Branch Risk Layer Design

## 当前定位

分岔风险层分成两层：

```text
Macro stack outputs -> branch risk scoring -> watchlist fields + overview commentary
watchlist risk -> viewer simulate / Python orchestrator -> manual or probabilistic branch path
```

默认 baseline 状态仍然不改变 GDP、通胀、政策利率、收益率曲线、美元、信用、资产价格或油价路径。当前路径就是“未发生/尚未发生”情景。

发生路径有两种入口：

- HTML viewer：临时模拟，用于观察图表上的虚线分叉。
- `macro_run_orchestrator_sim.py`：持久化 `occurred` / `counterfactual` / `probabilistic` 路径，写出全球、14 区、区域航空、城市机场和北京经营样例 CSV/JSON/JS。

## 输出字段

`global_macro_feedback_calibration_sim.py` 在反馈校准后的记录上追加：

- `branch_risk_param_version`
- `branch_risk_interface_version`
- `branch_risk_primary_id`
- `branch_risk_primary_label`
- `branch_risk_primary_probability_pct`
- `branch_risk_primary_severity_index`
- `branch_risk_primary_horizon_years`
- `branch_risk_primary_impact_years`
- `branch_risk_primary_tail_years`
- `branch_risk_primary_cooldown_years`
- `branch_risk_secondary_ids`
- `branch_risk_watchlist`
- `branch_risk_evidence`
- `branch_risk_count`

`branch_risk_watchlist` 是 JSON 字符串，最多保留当年分数最高的 4 个风险。HTML viewer 的随机 seed 也会在前端重新计算同一类字段。

## 时间字段

- `horizon_years`：从当前年份开始，未来多久内可能触发或值得观察。它不是冲击持续时间。
- `impact_years`：点击“模拟发生”后，直接冲击持续多久。
- `tail_years`：主冲击结束后的余波衰减期。
- `cooldown_years`：同一个风险在观察窗口内不重复作为新分岔点提示。

过了 `impact_years + tail_years` 后，增长率、通胀、利率、美元和油价会逐渐向模型自身状态回归，但 GDP 水平、信用疤痕和资产价格指数不会被强行贴回原路径。

## 当前可观察分岔

- 虚假黎明：表面复苏后 1-3 年可能二次探底。
- 政策失误：过早收紧：通胀不高、产出缺口为负时仍收紧。
- 政策失误：落后曲线：通胀和预期升温，但政策反应偏慢。
- 信用事故：HY 利差、再融资压力和信用可得性同时恶化。
- 银行惜贷循环：流动性宽松，但银行放贷意愿不足。
- 美元挤兑升级：美元走强、融资压力和新兴市场压力叠加。
- 能源冲击升级：油价高位且供给冲击没有消退。
- 债券市场失控：长端利率、期限溢价或主权债回报快速恶化。
- 软着陆成功：通胀降温、增长未破位、信用保持稳定。
- 流动性牛市脱实向虚：资产上涨由流动性和估值主导，盈利跟不上。
- 再融资墙：企业到期压力和高融资成本延长信用拖累。
- 需求破坏式降通胀：通胀回落来自需求转弱，而不是健康降温。
- 滞胀陷阱：低增长和高通胀同时存在，政策两难。
- 风险资产牛市脆弱化：风险资产很强，但盈利或信用基础偏弱。

## 与叙事层的关系

叙事层回答“现在像什么时期”，分岔风险层回答“接下来可能拐向哪里”。两者可以同时出现：例如当前被解释为“政策宽松修复”，但分岔观察里仍可能列出“虚假黎明”和“银行惜贷循环”。

## 发生情景 v0.1

HTML viewer 在总览风险卡上提供“模拟发生”按钮：

- 当前路径 = 未发生情景。
- 发生情景 = 从当前年份后分叉出一条临时路径。
- 情景路径不会写回 CSV/JSON，也不会替换 seed。
- 图表用虚线叠加发生路径；切换到通胀、政策、收益率、美元、信用、资产或石油栏时，会显示对应指标的分岔路径。

Python orchestrator 提供持久化路径：

```powershell
py -3 .\airport\macro_layers\macro_run_orchestrator_sim.py --seed 20260630 --scenario-state occurred --scenario-branch-id auto
```

也可以让同一 seed 自动抽取历史岔路时间线：

```powershell
py -3 .\airport\macro_layers\macro_run_orchestrator_sim.py --seed 20260630 --scenario-state probabilistic
```

它会把 baseline 和 scenario 分别写到：

```text
airport/output/macro_runs/<run_id>/baseline/
airport/output/macro_runs/<run_id>/occurred_<branch_id>_<trigger_year>/
airport/output/macro_runs/<run_id>/probabilistic_branch_timeline_<n>events/
```

如果加 `--publish-viewer scenario`，scenario 会覆盖当前 viewer canonical 输出，便于直接打开页面查看。

发生情景会构造一条或多条事件反馈路径，并经过 3 轮动态宏观反馈闭环。冲击会进入：

- GDP 增长、产出缺口和金融压力
- headline/core 通胀和通胀预期
- 政策利率、QE 和政策立场
- 收益率曲线和长端利率
- 美元、全球流动性和金融条件
- HY/IG 利差、银行放贷意愿和信用疤痕
- 股票、主权债、企业债和 60/40 组合
- Brent 油价和广义商品指数

## 概率历史岔路 v0.5

`--scenario-state probabilistic` 已经是最小版多事件自动抽签系统。它不是另起一套事件表，而是复用每年 baseline 的 `branch_risk_watchlist`：

```text
baseline yearly watchlist -> seeded event draw -> selected branch events -> combined macro feedback path
```

基本规则：

- 同一 seed、起始年份、模拟时长和概率参数会得到同一条历史岔路时间线。
- 换 seed 后，每年的 watchlist 和随机抽取都会变化，因此历史岔路可能改变。
- 默认每年至少从第三个年度点开始抽取，避免开局第一年就硬拐弯。
- 默认自动上限约为“每 15 年最多 1 个事件”，长时限模式可以提高 `--probabilistic-scenario-max-events`。
- 每个事件的 `impact_years + tail_years` 后还会追加冷却期，默认 6 年，避免多个岔路密集重叠。
- 如果概率抽取完全未命中，但 `--probabilistic-scenario-min-events` 大于 0，会从最强候选中补足最低事件数。

当前运行时历史岔路 profile 收束为 12 种核心类型：

```text
bond_market_accident
bank_lending_trap
credit_accident
dollar_squeeze_escalation
energy_shock_escalation
false_dawn
liquidity_bubble
policy_behind_curve
policy_mistake_tightening
refinancing_wall
soft_landing_success
stagflation_trap
```

旧的碎片化 id 会折叠到核心类型：

- `false_dawn_reversal`、`demand_destruction_disinflation` -> `false_dawn`
- `credit_crunch_amplification`、`debt_deflation_loop` -> `credit_accident`
- `bank_lending_freeze` -> `bank_lending_trap`
- `dollar_funding_squeeze` -> `dollar_squeeze_escalation`
- `energy_supply_squeeze` -> `energy_shock_escalation`
- `inflation_expectation_unanchor` -> `policy_behind_curve`
- `policy_reflation_boost`、`commodity_disinflation_relief` -> `soft_landing_success`
- `risk_asset_boom_overheat`、`risk_asset_bull_fragility` -> `liquidity_bubble`
- `stagflation_entrenchment` -> `stagflation_trap`

## 与事件层的关系

当前概率岔路仍然是宏观 watchlist 驱动，不是完整叙事事件系统。后续如果做真正的事件层，可以在这 12 个核心 profile 之下继续扩展：

```text
branch risk watchlist -> event draw / player choice -> macro impulse path -> narrative event package
```

例如 `false_dawn` 可以在事件层里变成一个概率分支：正常修复、U 型磨底、二次衰退。事件层需要决定触发概率、持续时间、冲击路径、政策响应是否抵消、多个事件是否允许串联，以及事件文本如何进入玩家界面。
