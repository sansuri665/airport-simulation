# IMPORTANT: City Airport Quarterly Operations Parameter Range Guide

这份文档记录城市机场季度经营层的设计边界。它的重点不是逐项解释所有收入和成本，而是防止后续忘记：经营参数当然会随城市变化；翻新的施工期容量折扣，以及翻新、新建、拆除重建的费用、工期、维护年龄处理更需要按区域、城市和特殊槽位调制。拆除重建施工期容量固定归零。

真实 source of truth 仍然是代码和城市季度经营 JSON。本文件是重要调参记忆。

## 当前代码和配置入口

先看这些位置：

- `airport/macro_layers/city_airport_quarterly_operations_layer_sim.py`
- `airport/config/city_airport_operations/beijing_airport_system_quarterly_operations_v1.json`
- `airport/config/city_airport_operations/reference_defaults/china_mainland_quarterly_operations_reference_defaults_v1.json`
- `airport/config/city_airport_operations/templates/city_airport_quarterly_operations_parameter_schema_v1.json`
- `airport/beijing_airport_operations_viewer.html`

当前状态：

- 季度经营层当前以北京为样板配置。
- `reference_defaults` 和 `templates` 主要是文档化参考，不是运行时自动继承。
- 城市季度经营配置必须自己填完整参数。
- 当前配置已包含航运收入、槽位固定经营成本、旅客接待成本、拥挤成本、商业三分项、城市机场感知品质指数、翻新事件、翻新资产折旧、新建航站楼事件、新建资产折旧、拆除重建事件和重建资产折旧。
- 拆除重建机制 v0.1 已接入北京样板：施工期容量归零、建造 capex、拆除费用、旧翻新资产核销、完工后目标规格和维护年龄重置均在季度经营层输出。
- v0.19 起，季度经营层会先把年度潜在分项和年度航司供给分项按季节权重拆到季度，再用当季潜在客流、当季航司供给、当季真实容量和容量实现率重新裁剪实际承接客流；上游年度 `served` 不再决定季度实际吞吐。

## 核心设计结论

季度机场经营层应采用：

```text
区域经营参考默认
  -> 城市经营配置
  -> 特殊机场 / 特殊槽位 / 具体翻新事件覆盖
```

普通收入和成本随城市变化是基本前提，不必每次重新讨论。真正需要特别记住的是：翻新、新建和拆除重建参数不应全球同质。

重要原则：翻新、新建和拆除重建的造价、工期、资产折旧口径都不得视为全球统一参数；翻新的施工期容量扰动也需要可调。拆除重建的容量扰动不调，施工期固定归零。它们应先有区域经营参考默认，再由城市经营配置覆盖，最后允许特殊机场、特殊槽位或具体事件单独覆盖。

## 季度承接与容量实现率

季度经营层的实际承接客流按以下顺序计算。v0.19 起，季度潜在和季度航司供给先由五类分项分别按季度权重拆出，再汇总成当季总潜在和总供给：

```text
quarter_component_potential_passengers
  = annual_component_potential_passengers
    * component_quarter_weight

quarter_component_airline_supply_passengers
  = annual_component_airline_supply_passengers
    * component_quarter_weight

quarter_serviceable_demand
  = min(quarter_city_potential_passengers, quarter_airline_supply_passengers)

quarter_served_passengers
  = min(
      quarter_serviceable_demand,
      quarter_max_capacity * quarter_capacity_realization_factor
    )
```

`quarter_capacity_realization_factor` 的作用是避免机场被撑爆时永远机械等于最大容量。未接近最大容量时为 `100%`；接近或超过最大容量时通常应落在 `97% - 99%` 附近；翻新或拆除重建施工期可以略低。这个口径让 2056-2061 这类重建期真实压低承接客流，也让 2062 完工后的新容量可以被重新使用，而不是继续被旧年度容量口径卡住。

分项承接暂时按 `quarter_served_passengers / quarter_city_potential_passengers` 等比例压低分项潜在客流。周期解释主要看分项潜在和分项航司供给，承接分项只是容量、航司总供给和容量实现率约束后的派生结果。

## 普通经营参数的城市差异

这些本来就应按城市填写，不是本文重点：

- 航运侧每客收入。
- 启用槽位固定经营成本。
- 旅客接待成本。
- 拥挤成本和宽松红利。
- 餐饮零售自营收入、固定成本、销售成本、服务成本。
- 免税和奢侈品合同销售额、保底、分成。
- 季度客流季节性。
- 城市复杂度、宏观成本压力、消费环境响应。

这些参数后续可继续做区域模板，但城市覆盖必须保留。

## 城市机场感知品质指数

城市机场感知品质指数用于表达航站楼豪华程度、新旧状态、拥挤度和施工扰动对旅客观感的影响。它的目标是影响商业收入，而不是反向改变客流需求、航司供给或机场运行成本。

第一版应保持通用参数，不建议逐城市频繁特调。城市差异主要由以下输入自然产生：

- 各城市实际启用的槽位规格。
- 各槽位建成年份。
- 翻新事件完成后形成的有效维护年龄前推。
- 拆除重建完工后形成的维护年龄重置和目标规格变化。
- 当季设计客流使用率和最大客流使用率。
- 普通翻新施工期扰动；拆除重建施工期则通过有效槽位移除和容量归零体现。

计算顺序：

```text
单槽位感知品质
  = 100
  + 航站楼规格分
  + 连续新旧状态分
  + 容量压力分
  + 普通翻新施工扰动

城市机场感知品质指数
  = 单槽位感知品质按承接客流加权

商业收入/销售额
  = 原商业模型输出 * 感知品质商业乘数
```

当前通用参数建议：

- `commercial.perceived_quality_model.facility_size_scores`
  - `small -4`
  - `medium -1`
  - `large +1.5`
  - `extra_large +4`
  - `giant +6`
- `commercial.perceived_quality_model.age_score`
  - 使用连续函数：`max_score - score_span * sigmoid((effective_age - midpoint_years) / softness_years)`。
  - 当前口径约等于：新航站楼小幅加分，中年逐步转中性，30 年以上明显扣分。
- `commercial.perceived_quality_model.capacity_pressure_score`
  - 低于设计容量给小幅宽松红利。
  - 超过设计容量开始拥挤扣分。
  - 接近最大容量时触发硬压力扣分。
  - 设计容量和最大容量用 `max(design_penalty, hard_penalty)`，不要直接相加，避免同一拥挤被重复惩罚。
- `commercial.perceived_quality_model.renovation_construction_disruption_score`
  - 当前只处理普通翻新，默认 `-5`。
  - 新建空槽位不扰动既有航站楼观感。
  - 拆除重建施工期不再额外扣同一槽位观感分，而是把该槽位从有效槽位中移除；城市品质通过剩余槽位的容量压力自然恶化。

商业乘数使用非线性函数：

```text
commercial_multiplier
  = 1 + sensitivity * tanh((quality_index - 100) / quality_scale)
```

当前建议：

- 自营餐饮零售：`sensitivity = 0.10`
- 免税：`sensitivity = 0.18`
- 奢侈品/精品：`sensitivity = 0.28`
- `quality_scale = 18`

这样 100 附近的变化较敏感；当品质指数偏离很远时，乘数会逐渐钝化，不会线性爆炸。

## 翻新机制为什么需要区域/城市差异

翻新不是简单的“花钱减年龄”。同样规格的航站楼翻新，在不同区域和城市会出现明显差异：

- 人工成本、材料价格、进口设备依赖不同。
- 土地和施工组织难度不同。
- 审批、监管、安全标准不同。
- 气候和地理条件不同：高寒、高温、高原、海岛、台风、沙尘都会影响工期。
- 物流和运输条件不同。
- 不停航施工难度不同。
- 老航站楼结构复杂度不同。
- 繁忙枢纽的施工期容量损失可能更大。

因此翻新机制应按“区域默认 + 城市难度 + 槽位/事件覆盖”来处理。

## 翻新相关参数

当前已有这些关键参数：

- `facility_renovation_model.city_construction_cost_multiplier`
  - 城市级施工费用乘数。
  - 用于反映城市人工、材料、物流、土地和施工组织难度。
- `facility_renovation_model.replacement_cost_million_cny_by_facility_size`
  - 各规格航站楼的游戏口径重置成本。
- `facility_renovation_model.capex_ratio_by_facility_size`
  - 翻新费用占重置成本比例。
- `facility_renovation_model.duration_quarters_by_facility_size`
  - 各规格默认翻新工期。
- `facility_renovation_model.default_construction_capacity_multiplier`
  - 施工期该槽位可用容量比例。
  - 数值越低，施工对容量扰动越大。
- `facility_renovation_model.maintenance_age_retention_ratio`
  - 翻新完工后有效维护年龄的保留比例。
  - 数值越低，翻新越有效；数值越高，翻新越保守。
- `facility_renovation_model.minimum_effective_maintenance_age_years`
  - 翻新后的有效维护年龄下限。
  - 防止老航站楼被频繁翻新洗成全新设施。
- `facility_renovation_model.renovation_asset_depreciation`
  - 翻新新增资产的折旧年限和残值率。
- `facility_renovation_events`
  - 具体翻新事件。
  - 事件级可覆盖 `duration_quarters`、`construction_capacity_multiplier`、`capex_million_cny`、`useful_life_years`、`residual_value_pct`。

动态测试器口径：每个已运营槽位可在任意玩家季度启动一次标准翻新事件。确认开工时，系统会把上述事件级参数按当时的城市默认值写入 seed 绑定的行动日志；服务端随后只按这份冻结参数重算该工程的施工容量、资本开支、在建工程、转固和折旧。这样后续调整城市默认参数不会改写已经立项的项目。同一槽位施工期不允许重叠工程，不同槽位可分别施工。

## 新建航站楼相关参数

新建航站楼和翻新应分开理解：

- 翻新：不改变槽位规格，不扩容；施工期降低该槽位容量，完工后形成翻新资产，并前推有效维护年龄。
- 新建：只用于空槽位；玩家从槽位角色允许的非空规格中选择目标。施工期不增加容量，完工后城市机场客流层通过完成事件暴露新槽位，季度经营层记录 capex、在建工程和新建资产折旧。
- 拆除重建：用于已启用槽位；施工期关闭该槽位容量，完工后槽位变成目标规格，维护年龄按新资产重置，并形成重建资产。

新建层本身不需要太复杂，但造价和工期必须允许区域/城市差异。同样的 `large` 航站楼，在人工、材料、土地、审批、物流、气候、施工组织、机场不停航要求不同的区域和城市，成本与工期都可能明显不同。区域默认值只是一组起点，不能替代城市和事件级判断。

动态测试器中，新建确认开工时会把目标规格、工期、资本化支出、折旧年限和残值率冻结到 seed 绑定的行动日志；同槽位施工不得重叠，当前现金为负时不能开工，初版不可取消。空槽位在施工期不进入容量和感知质量计算，完工后维护年龄从 `0` 年开始，并冷却 `12` 年（`48` 季）才能翻新。默认航站楼名称按机场独立顺序生成（首都机场已有 T2/T3 后从 T4 起，大兴机场已有 T1 后从 T2 起），玩家改名不改变后续编号。

当前已有这些关键参数：

- `facility_construction_model.construction_cost_million_cny_by_facility_size`
  - 各规格航站楼完整新建造价。
  - 和翻新 `replacement_cost_million_cny_by_facility_size` 使用同一 2025 不变价游戏口径。
- `facility_construction_model.duration_quarters_by_facility_size`
  - 各规格新建标准工期。
- `facility_construction_model.city_construction_cost_multiplier`
  - 城市级施工费用乘数。
  - 用于表达同一区域内不同城市的人工、材料、物流、土地和施工组织难度。
- `facility_construction_model.new_asset_depreciation`
  - 新建资产折旧年限和残值率。
- `facility_construction_events`
  - 具体新建事件。
  - 事件级可覆盖 `duration_quarters`、`capex_million_cny`、`construction_cost_multiplier`、`useful_life_years`、`residual_value_pct`。
- 用于表达具体机场或槽位的特殊施工条件，不要为了一个特殊项目改整座城市的默认值。

## 拆除重建机制

拆除重建 v0.1 已实现。它不应和翻新或新建混为一谈。

边界：

- 只能用于已启用槽位。
- 目标规格可以等于原规格，也可以升级，但必须符合该槽位允许规格。
- 施工期该槽位容量归零；第一版不保留拆除槽位的任何运营容量。
- 完工后槽位变成目标规格，城市设计容量和最大容量按目标规格与源规格的差额调整。
- 完工后维护年龄从重建完工期重新开始读取，不再使用旧航站楼维护年龄。
- 完工后形成重建资产，并按 `new_asset_depreciation` 折旧。
- 重建建造费用资本化为资产；拆除费用是期间费用，不形成资产。
- 同槽位旧初始资产由财务状态层核销；同槽位已完工翻新资产由季度经营层输出核销额，并从后续翻新资产中移除。
- 同一槽位的翻新和拆除重建施工窗口不得重叠。翻新完工后冷却 `6` 年（`24` 季）才可再次翻新；重建完工后冷却 `20` 年（`80` 季）才可再次重建，且重建完工后同样需冷却 `6` 年（`24` 季）才可翻新。
- 重建目标规格由玩家从槽位角色允许的非空规格中选择；启动前要求当前现金不为负，确认开工后不可取消。
- 重建施工期槽位从有效设施和感知质量计算中退出：容量归零，维护年龄和维护年龄分显示为不参与；完工后维护年龄重置为 `0` 年。

与翻新、新建的区别：

| 类型 | 适用对象 | 是否改变规格 | 施工期容量 | 完工后维护年龄 | 资产口径 |
|---|---|---:|---:|---:|---|
| 翻新 | 已启用槽位 | 否 | 部分下降 | 部分前推 | 新增翻新资产 |
| 新建 | 空槽位 | 是 | 不影响旧容量 | 新槽位从 0 开始 | 新增新建资产 |
| 拆除重建 | 已启用槽位 | 可同规格或升级 | 归零 | 重置为新资产 | 新增重建资产，旧资产核销 |
| 拆除 | 已启用槽位 | 变为空白 | 归零 | 不参与 | 拆除费用化，旧资产核销 |

当前参数：

### 北京样板：拆除、新建与组合重建工期表

以下数值**只适用于北京动态测试样板**，不是中国或全球默认值。它把工期与造价分开：拆除看原规格，新建看目标规格；拆除重建严格串行组合两段工期。城市施工能力、繁忙枢纽的不停航组织、气候、审批和项目级特殊条件，后续应通过独立的工期系数或事件覆盖调整。

| 规格 | 单独拆除工期 | 北京拆除费率 | 新建工期 | 北京新建资本开支 |
|---|---:|---:|---:|---:|
| 小型 | 4 季 | 8% | 8 季 | 67.5 亿元 |
| 中型 | 5 季 | 8% | 10 季 | 135.0 亿元 |
| 大型 | 7 季 | 10% | 14 季 | 285.0 亿元 |
| 超大型 | 9 季 | 12% | 18 季 | 510.0 亿元 |
| 巨型 | 12 季 | 14% | 24 季 | 787.5 亿元 |

组合规则：

```text
拆除重建总工期 = 拆除工期(原规格) + 新建工期(目标规格)
拆除重建现金支出 = 拆除费用(原规格) + 新建资本开支(目标规格)
旧资产减记 = 拆除开工时的旧资产账面价值
```

例如，北京大型槽位拆除并重建为超大型：`7 + 18 = 25 季`；现金支出为大型拆除费用加超大型新建资本开支。大型拆除并重建为中型则是 `7 + 10 = 17 季`，不会因为目标规格变小而跳过拆旧所需的时间。

运行时已按上述组合公式计算新发起的拆除重建项目，并在开工时冻结拆除子工期、新建子工期、总工期、拆除费用和资本化支出。旧的 `facility_rebuild_model.duration_quarters_by_facility_size` 仅保留给既有配置兼容，不再用于动态测试玩家项目的工期计算。

- `facility_rebuild_model.asset_cost_million_cny_by_facility_size`
  - 重建后目标规格的建造费用。
  - 当前可沿用新建造价，也可用城市或事件级覆盖。
- `facility_rebuild_model.demolition_cost_ratio_by_source_facility_size`
  - 拆除费用按源规格资产成本乘比例估算。
  - 北京默认：`small/medium 0.08`，`large 0.10`，`extra_large 0.12`，`giant 0.14`。
- `facility_rebuild_model.duration_quarters_by_facility_size`
  - 目标规格对应的标准工期。
  - 北京默认：`small 10`、`medium 13`、`large 18`、`extra_large 24`、`giant 32`。
- `facility_rebuild_model.default_construction_capacity_multiplier`
  - 保留字段仅用于兼容输出和配置阅读；拆除重建 v0.1 的代码口径固定为 `0.0`。
  - 不建议按区域、城市或事件调整这一项；差异应放在工期、建造费和拆除费。
- `facility_rebuild_model.city_construction_cost_multiplier`
  - 城市级建造费用乘数。
- `facility_rebuild_model.city_demolition_cost_multiplier`
  - 城市级拆除费用乘数。
- `facility_rebuild_model.new_asset_depreciation`
  - 重建资产折旧年限和残值率。
  - 北京默认 `40` 年，残值 `10%`。
- `facility_rebuild_events`
  - 具体重建事件。
  - 事件级可覆盖 `duration_quarters`、`asset_capex_million_cny` / `capex_million_cny`、`demolition_expense_million_cny`、`construction_cost_multiplier`、`demolition_cost_multiplier`、`useful_life_years`、`residual_value_pct`。

适用场景：

- 土地紧机场没有空槽位，只能拆旧建新。
- 老旧航站楼容量太小，翻新已经不够。
- 旧楼结构复杂，维护年龄前推意义不大。
- 玩家希望把旧 `small/medium` 槽位升级为 `large/extra_large`。
- 特殊枢纽需要把旧航站楼资产改造成新的主力槽位。

实现状态：

1. 已加入 `facility_rebuild_model` 和 `facility_rebuild_events`。
2. 已处理施工期容量归零、capex、拆除费用、完工后规格变化、维护年龄重置、新资产折旧。
3. 已接入旧翻新资产核销；旧初始资产核销由财务状态层读取 `rebuild_started_slot_ids` 后处理。
4. 暂未加入 salvage / 处置收入；第一版把拆除费用视为纯费用，旧资产核销视为非现金损益。
5. 动态测试经营报告中，面向玩家的槽位显示为 `主槽位`、`次槽位`、`辅助槽位1/2/3`；`PEK_SLOT_2` 这类 `slot_id` 保留为内部配置、输出和调试键。

北京样板：

拆除重建：

- `PEK_SLOT_2_REBUILD_2056Q1`
- 槽位：北京首都 `PEK_SLOT_2`（玩家显示：次槽位，首都T2航站楼）
- 源规格：`large`
- 目标规格：`extra_large`
- 标准建造费：`51000 million_cny`
- 标准拆除费：`28500 * 0.10 = 2850 million_cny`
- 标准工期：`24` 季度，`2056Q1` 开工，`2062Q1` 投用
- 施工期容量：该槽位设计容量和最大容量归零
- 完工后容量增量：从 `large` 到 `extra_large`，设计容量增加约 `18m`，最大容量增加约 `20m`
- 资产口径：建造费形成重建资产，拆除费期间费用化；`PEK_SLOT_2` 初始资产和既有翻新资产在重建开始时核销

新建：

- `PKX_SLOT_2_CONSTRUCTION_2065Q3`
- 槽位：北京大兴 `PKX_SLOT_2`（玩家显示：次槽位，大兴T2航站楼新建工程）
- 目标规格：`large`
- 标准造价：`28500 million_cny`
- 标准工期：`14` 季度，`2065Q3` 开工，`2069Q1` 投用
- 城市机场客流层年度口径：`PKX_SLOT_2` 从 `2069` 年开始按 `large` 计入容量
- 完工资产折旧：`40` 年，残值 `10%`
- 设计目的：比早建 `extra_large` 更贴近需求释放节奏；当前默认 seed 下现金口径可在 2080s 初期回本，但不是无脑盈利项目。

## 建议参数范围

这些是游戏调参起点，不是最终标定：

- 城市施工费用乘数 `city_construction_cost_multiplier`
  - 常规：`0.85 - 1.25`。
  - 困难城市：`1.25 - 1.50`。
  - 极端困难：`1.50+`，需要明确理由。
- 翻新费用比例 `capex_ratio_by_facility_size`
  - 轻度模型暂不拆分时：`0.12 - 0.25`。
  - 当前北京样板：`0.16`。
  - 如果未来翻新更像大修或结构改造，可到 `0.25 - 0.40`。
- 翻新工期 `duration_quarters_by_facility_size`
  - `small`：`3 - 5` 季度。
  - `medium`：`4 - 6` 季度。
  - `large`：`5 - 8` 季度。
  - `extra_large`：`7 - 10` 季度。
  - `giant`：`9 - 14` 季度。
- 施工期容量乘数 `default_construction_capacity_multiplier`
  - 常规不停航翻新：`0.70 - 0.85`。
  - 繁忙或土地紧机场：`0.55 - 0.75`。
  - 极端复杂槽位：`0.45 - 0.60`。
  - 完全关闭式施工应作为特殊事件，不要默认为常态。
- 维护年龄保留比例 `maintenance_age_retention_ratio`
  - 常规：`0.50 - 0.70`。
  - 高质量翻新：`0.35 - 0.50`。
  - 保守翻新或旧结构复杂：`0.70 - 0.85`。
  - 不建议设为 `0`，否则翻新过于接近重建。
- 翻新后最低有效维护年龄 `minimum_effective_maintenance_age_years`
  - 常规：`3 - 8` 年。
  - 老旧复杂建筑：`5 - 12` 年。
- 翻新资产折旧 `renovation_asset_depreciation`
  - 使用寿命：`15 - 30` 年。
  - 残值率：`0% - 10%`。
- 新建造价 `construction_cost_million_cny_by_facility_size`
  - `small`：`6750m`。
  - `medium`：`13500m`。
  - `large`：`28500m`。
  - `extra_large`：`51000m`。
  - `giant`：`78750m`。
  - 这套价格同步用于翻新 replacement cost，再由翻新比例计算翻新费用。
- 新建工期 `facility_construction_model.duration_quarters_by_facility_size`
  - `small`：`8` 季度。
  - `medium`：`10` 季度。
  - `large`：`14` 季度。
  - `extra_large`：`18` 季度。
  - `giant`：`24` 季度。
- 新建资产折旧 `new_asset_depreciation`
  - 使用寿命：`35 - 50` 年。
  - 残值率：`5% - 15%`。
- 重建建造费 `facility_rebuild_model.asset_cost_million_cny_by_facility_size`
  - 可先沿用新建造价。
  - 常规同规格重建可设为新建造价的 `0.90 - 1.05`。
  - 升级重建、地下/轨道/边运营复杂项目可设为 `1.05 - 1.25`。
  - 极端复杂项目应使用事件级 `asset_capex_million_cny`，不要修改全城默认。
- 拆除费用比例 `facility_rebuild_model.demolition_cost_ratio_by_source_facility_size`
  - `small/medium`：`0.05 - 0.10`。
  - `large`：`0.08 - 0.14`。
  - `extra_large`：`0.10 - 0.18`。
  - `giant`：`0.12 - 0.22`。
  - 拆除费是期间费用，不资本化。
- 重建工期 `facility_rebuild_model.duration_quarters_by_facility_size`
  - `small`：`8 - 12` 季度。
  - `medium`：`10 - 16` 季度。
  - `large`：`14 - 22` 季度。
  - `extra_large`：`18 - 30` 季度。
  - `giant`：`24 - 40` 季度。
- 重建施工期容量乘数 `facility_rebuild_model.default_construction_capacity_multiplier`
  - v0.1 固定为 `0.0`。
  - 不设置区域/城市差异。
  - 不建议事件级覆盖；拆除就是拆除，该槽位施工期容量归零。
- 重建资产折旧 `facility_rebuild_model.new_asset_depreciation`
  - 使用寿命：`35 - 50` 年。
  - 残值率：`5% - 15%`。
- 感知品质规格分 `commercial.perceived_quality_model.facility_size_scores`
  - `small`：`-6` 到 `-2`。
  - `medium`：`-2` 到 `0`。
  - `large`：`0` 到 `3`。
  - `extra_large`：`3` 到 `6`。
  - `giant`：`5` 到 `8`。
  - 不建议继续放大，否则航站楼规格会压过新旧和拥挤。
- 感知品质年龄函数 `commercial.perceived_quality_model.age_score`
  - 新楼最高加分建议 `4 - 8`。
  - 老楼最大扣分建议 `-10` 到 `-16`。
  - `midpoint_years` 可在 `20 - 30` 年。
  - `softness_years` 可在 `6 - 12` 年。
- 感知品质容量压力 `commercial.perceived_quality_model.capacity_pressure_score`
  - 宽松红利最高 `+2` 到 `+4`。
  - 超设计容量惩罚最高 `-10` 到 `-18`。
  - 接近最大容量硬惩罚最高 `-14` 到 `-24`。
  - 设计惩罚和最大容量惩罚应取较大值，不应直接相加。
- 感知品质商业敏感度 `commercial.perceived_quality_model.commercial_revenue_response`
  - 自营餐饮零售：`0.06 - 0.14`。
  - 免税：`0.12 - 0.22`。
  - 奢侈品/精品：`0.20 - 0.34`。
  - 建议使用 `tanh` 钝化，不要使用无限线性放大。

## 区域差异示例

这些不是最终参数，只是后续建区域模板时的方向：

- 中国大陆
  - 施工组织能力强，常规城市费用和工期可接近默认值。
  - 一线繁忙机场的翻新容量折扣应更明显；拆除重建仍然归零。
- 日本/韩国
  - 土地和运营约束更强，费用和工期可略高。
  - 大型繁忙机场施工期容量乘数应偏低。
- 西欧/北欧
  - 环保、噪音、审批、人工成本压力较高。
  - 工期和费用乘数应偏高。
- 北美
  - 多航站楼系统常见，施工可分散，但人工和工程成本高。
  - 翻新时单槽容量折扣不一定极端，费用乘数可能偏高；拆除重建仍然归零。
- 中东海湾
  - 新机场和巨型设施能力强，但大型项目费用规模高。
  - 巨型槽位工期和 capex 应特别关注。
- 东南亚/南亚
  - 成长快，施工扰动可能受雨季、审批、城市拥堵和物流影响。
  - 热带气候和运营增长压力会影响翻新工期与容量折扣，也会影响拆除重建工期和费用。
- 岛屿和旅游城市
  - 物流、土地、季节性客流压力明显。
  - 翻新的费用、工期和施工期容量折扣都应允许更高差异；拆除重建只调费用和工期，容量仍归零。

## 城市和槽位覆盖原则

城市级覆盖适合表达：

- 城市施工成本整体高低。
- 城市物流和施工组织难度。
- 城市监管和审批节奏。
- 机场不停航施工的总体复杂度。

槽位或事件级覆盖适合表达：

- 某个航站楼过老或结构复杂。
- 某个槽位是主槽位，施工期对容量冲击更大。
- 某次翻新涉及国际区、行李系统、安检、轨道接驳等复杂内容。
- 某次翻新因为玩家选择或剧情事件导致费用、工期、容量折扣不同。

不要为了一个特殊槽位修改整个城市的默认参数。

## 与折旧和固定成本的边界

当前翻新机制有三步影响：

1. 投资：施工期发生 capex outlay，并形成在建工程。
2. 资产：完工后形成独立翻新资产，并按翻新资产折旧参数折旧。
3. 维护年龄：完工后前推有效维护年龄，影响槽位固定经营成本读取的年龄曲线。

注意：

- 翻新不改变槽位规格。
- 翻新不是扩容。
- 翻新不会清除旧航站楼历史。
- 翻新资产是额外资产，不是把原资产直接重置。
- 维护年龄前推是经营成本口径，不等于会计资产年龄完全归零。
- 动态测试中，同一槽位可有多次翻新实例，但施工窗口不得重叠；每次翻新完工后冷却 `12` 年（`48` 季）才可再次开工。
- 每次翻新形成独立新增资产，按发生顺序使用 `航站楼名-2`、`航站楼名-3` 等名称；已完成项目退出项目事务的施工中列表，但保留在资产台账和项目台账。

新建机制的边界：

- 新建只用于空槽位。
- 新建施工期不增加容量。
- 新建不影响既有槽位容量。
- 新建完工后由城市机场客流层的 `open_year` 和目标 `facility_size` 决定年度容量。
- 新建资产不前推维护年龄；它从完工年份按新资产读取固定成本年龄曲线。
- 新建和翻新都使用 2025 不变价人民币，不做累计通胀滚动。

拆除重建机制的边界：

- 拆除重建只用于已启用槽位。
- 拆除重建施工期会关闭该槽位容量。
- 拆除重建完工后同一槽位按目标规格参与容量、固定成本和感知品质计算。
- 当前代码由季度经营层对上游城市容量做 `target_size - source_size` 的容量增量修正；因此上游城市机场客流层暂时不要同时把同一槽位改成目标规格，否则会双算容量。
- 拆除重建会重置该槽位维护年龄。
- 拆除重建建造费资本化，拆除费费用化。
- 拆除重建会核销被拆槽位的旧初始资产和已完工翻新资产。
- 同槽位施工窗口不能重叠，尤其不能让翻新和重建同时发生。
- 翻新、新建和拆除重建都使用 2025 不变价人民币，不做累计通胀滚动。

## 后续扩展顺序

1. 先为季度经营层建立区域参考默认。
2. 再为每个城市填经营配置。
3. 对特殊机场或特殊槽位追加翻新、新建或拆除重建事件级覆盖。
4. 用同一 seed 路径检查客流、经营、翻新、新建、拆除重建、折旧和资产核销是否连续。
5. 最后再微调收入、成本和商业合同参数。

这样能保证季度经营层既能表达城市差异，也不会把翻新机制做成一组无法迁移的北京特例。
