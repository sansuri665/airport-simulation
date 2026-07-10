# Macro Event Interface Stub

## 目的

当前 `global_gdp_annual_sim.py` 仍然是一个 GDP 背景层，不是完整宏观事件引擎。这里先预留一层很薄的事件接口，让后续股、债、利率、美元、石油、信用等模块完成后，可以把事件系统接进来，而不是现在把“央行宽松”硬编码成 GDP 加减项。

这层接口的原则是：

- GDP 模块只发布事件线索，不直接定义完整政策反应函数。
- `event_*` 和 `*_impulse` 字段暂时只读，不反向改变当前 GDP 曲线。
- 后续的 Macro Event Engine 可以读取这些字段，统一分发给利率、美元、股债、油价、信用、GDP 等模块。

## 当前输出字段

年度 CSV / JS 数据中新增以下字段：

| 字段 | 含义 |
| --- | --- |
| `event_interface_version` | 当前接口版本，现为 `macro-event-interface-v0.1` |
| `event_type` | 抽象事件类型，例如 `systemic_crisis`、`central_bank_easing_placeholder` |
| `event_phase` | 事件阶段，例如 `onset`、`trough`、`repair`、`late_cycle` |
| `event_severity` | 0-1 强度刻度 |
| `policy_rate_impulse` | 对未来政策利率模块的方向性冲击预留 |
| `liquidity_impulse` | 对未来流动性 / QE / 金融条件模块的方向性冲击预留 |
| `credit_stress_impulse` | 对信用利差、融资压力、银行中介层的方向性冲击预留 |
| `dollar_pressure_impulse` | 对美元压力 / 全球美元流动性的方向性冲击预留 |
| `energy_price_impulse` | 对石油和能源价格层的方向性冲击预留 |
| `gdp_lagged_support` | 对 GDP 的滞后支撑或拖累预留，不在当前模型内二次生效 |

## 当前事件类型

| `event_type` | 触发来源 | 当前语义 |
| --- | --- | --- |
| `none` | 普通年份 | 没有显著宏观事件线索 |
| `financial_stress_event` | `crisis_onset` | 危机初期，信用压力、美元压力上升 |
| `systemic_crisis` | `deep_crisis` | 危机低谷，信用压力高、GDP 拖累明显 |
| `central_bank_easing_placeholder` | `crisis_repair` / `recovery` | 预留给未来央行宽松、流动性修复、信用利差收窄 |
| `credit_stress_event` | `stress_slowdown` | 信用条件偏紧但未必进入系统性危机 |
| `tightening_risk_placeholder` | `high_expansion` / `overheating_boom` | 预留给未来加息、缩表、流动性回收风险 |
| `demand_slowdown_event` | `slowdown` / `recession` | 需求放缓或轻度衰退 |

## 设计边界

现在不要把真实央行逻辑直接写进 GDP 层。原因是央行宽松至少应该经过这些通道：

1. 政策利率下降。
2. 长端利率和期限溢价变化。
3. 债券价格、信用利差和融资条件变化。
4. 美元压力和全球美元流动性变化。
5. 股市估值和风险偏好修复。
6. 石油需求预期和价格变化。
7. 最后滞后影响 GDP 和产出缺口。

因此，`central_bank_easing_placeholder` 现在只是接口占位。它会给出类似：

```json
{
  "event_type": "central_bank_easing_placeholder",
  "event_phase": "repair",
  "event_severity": 0.72,
  "policy_rate_impulse": -0.61,
  "liquidity_impulse": 0.79,
  "credit_stress_impulse": -0.50,
  "dollar_pressure_impulse": -0.14,
  "energy_price_impulse": 0.11,
  "gdp_lagged_support": 0.32
}
```

但这些数值目前只是给未来模块读的“方向和强度”，不会在 GDP 模块中再次生效。

## 后续接入建议

等股债利率石油美元等核心层完成后，可以新增一个 `macro_event_engine.py`：

- 输入：各模块年度状态和上一年事件状态。
- 生成：跨模块 `MacroEvent` 对象。
- 分发：将政策、流动性、信用、美元、能源、风险偏好等通道分别注入对应模块。
- 反馈：事件影响各模块后，再通过金融条件、需求、能源成本和贸易条件回流到 GDP。

届时 GDP 层应从“发布事件 stub”升级为“消费事件结果的一部分”，但仍不应该独自决定完整宏观政策反应。
