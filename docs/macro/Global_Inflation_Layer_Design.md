# Global Inflation Layer Design

## 当前定位

`global_inflation_annual_sim.py` 是 GDP 背景层之后的第一层组合宏观变量。它不单独生成一条孤立通胀曲线，而是直接调用 `global_gdp_annual_sim.py`，在同一组 seed、同一年份上生成 GDP + 通胀的合并年度数据。

当前版本的原则是：

- GDP 先行，通胀读取 GDP 和事件占位字段。
- 通胀暂时不反向改写 GDP。
- 通胀对未来利率、长端收益率和 GDP 拖累的影响以 placeholder 字段输出，后续利率/央行模块再消费。

## 输入来源

通胀层读取 GDP 层中的这些字段：

| GDP 字段 | 通胀层用途 |
| --- | --- |
| `realized_growth_pct` | 需求强弱和增长 surprise |
| `potential_growth_pct` | 判断增长是否高于潜在水平 |
| `output_gap_pct` | 需求拉动型通胀 |
| `financial_stress_index` | 信用收缩和危机中的通缩压力 |
| `crisis_intensity` | 危机期需求塌陷 |
| `boom_intensity` | 过热期需求和工资压力 |
| `liquidity_impulse` | 宽松或流动性冲击预留 |
| `dollar_pressure_impulse` | 进口通胀和美元压力预留 |
| `energy_price_impulse` | 能源成本推动通胀预留 |
| `credit_stress_impulse` | 信用压力导致的需求收缩 |

## 输出字段

合并 CSV / JS 数据位于 `airport/output/global_macro`，新增通胀字段包括：

| 字段 | 含义 |
| --- | --- |
| `headline_inflation_pct` | 全球 headline 通胀 |
| `core_inflation_pct` | 核心通胀 |
| `energy_inflation_pct` | 能源通胀代理 |
| `import_inflation_pct` | 进口通胀代理 |
| `wage_pressure_pct` | 工资压力代理 |
| `inflation_expectation_pct` | 通胀预期代理 |
| `demand_pull_component_pct` | 需求拉动分量 |
| `energy_component_pct` | 能源成本推动分量 |
| `external_supply_shock_component_pct` | 临时外部供给/能源冲击占位，未来可由石油模块替换 |
| `import_component_pct` | 美元/进口成本分量 |
| `liquidity_component_pct` | 流动性分量 |
| `stress_disinflation_component_pct` | 金融压力和危机带来的通缩分量 |
| `monetary_tightening_pressure` | 未来加息压力，0-100 |
| `monetary_easing_pressure` | 未来宽松压力，0-100 |
| `inflation_regime` | 通胀状态标签 |
| `inflation_to_policy_rate_impulse` | 未来政策利率层占位输入 |
| `inflation_to_long_rate_impulse` | 未来长端利率层占位输入 |
| `inflation_to_gdp_drag_placeholder` | 未来反向拖累 GDP 的占位字段 |

## 通胀状态

当前 `inflation_regime` 可能取值：

- `anchored_normal`
- `policy_reflation`
- `energy_cost_push`
- `overheating_inflation`
- `stagflation_pressure`
- `deflationary_crisis`
- `lowflation`
- `disinflation`

## 临时供给冲击占位

在正式石油和能源模块完成前，通胀层有一个轻量的 `external_supply_shock_component_pct`。它会偶尔生成 2-5 年的成本推动通胀段，让默认 seed 中能出现较清晰的能源/供给冲击时代。

这个字段只是占位：

- 当前它影响 `energy_inflation_pct`、`headline_inflation_pct` 和少量 `import_inflation_pct`。
- 后续石油模块完成后，应由油价、能源供需和美元计价压力替代。
- 它不反向影响 GDP。

## 反馈边界

现在通胀不会反向改变 GDP。比如高通胀会输出：

```json
{
  "monetary_tightening_pressure": 72.0,
  "inflation_to_policy_rate_impulse": 0.46,
  "inflation_to_long_rate_impulse": 0.31,
  "inflation_to_gdp_drag_placeholder": -0.18
}
```

但这些只是未来利率、央行、债券和 GDP 反馈模块的接口。当前模型不把它再次写回 GDP，避免在股债利率美元石油层未完成前形成硬编码闭环。

## 运行方式

```powershell
py -3 .\airport\global_inflation_annual_sim.py --years 60 --seed-count 8
```

默认输出：

- `airport/output/global_macro/global_gdp_inflation_seed_sweep.csv`
- `airport/output/global_macro/global_gdp_inflation_seed_sweep.json`
- `airport/output/global_macro/global_gdp_inflation_viewer_data.js`
- `airport/output/global_macro/global_inflation_curves.svg`

## 后续方向

下一步如果做央行和利率层，可以读取：

- `headline_inflation_pct`
- `core_inflation_pct`
- `inflation_expectation_pct`
- `monetary_tightening_pressure`
- `monetary_easing_pressure`
- `inflation_to_policy_rate_impulse`
- `inflation_to_long_rate_impulse`

然后再由政策利率和长端利率影响债券、美元、股市、信用和 GDP。
