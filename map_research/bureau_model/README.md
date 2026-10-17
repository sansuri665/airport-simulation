# 铁路分局经营模型 V0.3 · 东北十二家与华北十家

由 `northeast12_bureau_prototype_v01.zip` 中已审阅的十二分局配置及暴露计算迁入。
这里只保存分局经营层，直接调用现有 `economy_model.scenarios.simulate_scenario`；
不复制 ZIP 中的旧宏观引擎。原压缩包保留。`bureau.html` 提供只读经营试算页面，
由 `serve.py` 的 `/api/bureau-catalog`、`/api/bureau?seed=...&bureau=...` 提供研究数据。

华北十家由已审阅的 `huabei10_virtual_freight_v02` 压缩包 JSON 迁入，配置为 `north10_profiles.json`。
不执行或复制其宏观／财务模拟器，直接使用当前仓库 V0.5 宏观和 V0.3 独立成本公式。
`load_profiles()` 默认保留东北十二家供历史审计；`load_profiles(NORTH_PROFILE_PATH)` 读取华北十家；
试算页面使用 `load_all_profiles()` 共22家。两地配置和报告哈希分别校验。

## 华北地图外货运净结算

`settlement.apply_hidden_freight` 在普通六项收支计算完成后执行，公式为：

```text
净结算收入 = 原包基期净额 × settlement_scale × freight_index / 100
隐藏等效结算量 = 原包等效吨数 × settlement_scale × freight_index / 100
货运收入 = 普通货运收入 + 净结算收入
```

现取统一 `settlement_scale=0.9`，只下调原包净结算10%；原包基值、单位结算收益和等效吨数保留。
该收入已经扣除外部直接费用，因此不再进入运营工作量、不增加四投入／三业务成本，也不增加站务收入。
基期净额总计70亿元→63亿元。普通票价、货运收益、客货运指数和人工规则均未改变。
雄安采用原包修订的2000万人次基期、客运收入12亿元、站务收入3.2亿元；基期结余0.04亿元，无隐藏净结算。

`freight_tons_10k` 与 `ordinary_freight_tons_10k` 都只表示普通货运量。
`hidden_equivalent_freight_tons_10k` 是独立结算口径，不能与普通物理运输吨数相加或回灌成本计算。
`ordinary_freight_income_yi`、`hidden_freight_income_yi`、`freight_income_yi` 分别保存普通、净结算及货运总收入。
`core_operating_surplus_yi` 保留无净结算的结余，便于比较；人工 A/B 对照也增加同一笔净结算。
无隐藏业务的东北分局新增字段为零，已有金额和运量不变。适配器拒绝重复添加。

从 `map_research` 运行：

```powershell
py -3 -m unittest bureau_model.test_operations bureau_model.test_settlement bureau_model.test_api
py -3 -m bureau_model.audit_north
```

可选 `--archive 包路径.zip` 对照已审阅的原包 CSV；只读取 JSON/CSV，不执行包内脚本。
本轮用实际项目引擎重跑 Seed 0..95，并额外核对两个示范 Seed。
原包100%权重下4,880条年度数据和96 Seed 汇总复现，最大差约3.64e-12。
`reports/north_settlement_v01.json`、`north_96seed_summary_v01.csv`、`north_96seed_samples_v01.csv`、
`north_8seed_annual_v01.csv` 保存原包100%、90%、80%及无结算对照。累计结余不含基期。
华北2085年区域合计结余中位数：100%为65.59亿元，90%为57.82亿元，80%为50.17亿元。
当前90%下山西四家同时盈利61／96，十家×96 Seed 的亏损样本占比29.58%。
这是保留华北经营优势的小幅校准，未按全国百家分局完成最终平衡。

页面按所选经济区展示对应报告。华北年度表、摘要、货运收入曲线和CSV分别展示普通量、等效结算量及净收入；
96 Seed 区域统计不随当前所选 Seed 改变。配置变化后需重跑相应审计并重启本地服务。

所有运量、单位收入、成本及敏感度均为游戏假设；金额为 2025 年不变购买力下的亿元／年。
经营结余未扣除折旧、融资成本及新增投资。V0.3 含工资高点驱动的隐含用工调整，不按年份固定提效，也没有运量硬上限。

## 十二项独立成本

`northeast12_profiles.json` 是运行配置。每个分局的 `cost_inputs` 包含：

- 三类业务：`high_speed`、`conventional`、`station`。
- 四种投入：`energy`、`wage`、`materials`、`other`。
- 每项配置：`base_cost_yi`（基期金额）、`fixed_share`（固定比例）、
  `variable_passenger_share`（变动部分的客运权重，货运权重为其补数），
  `passenger_congestion`、`freight_congestion`（独立拥挤附加系数）。

每项计算为：

```text
P = 客运量指数 / 100
F = 货运量指数 / 100
客运工作量 = P × (1 + 客运拥挤系数 × max(P - 1, 0)²)
货运工作量 = F × (1 + 货运拥挤系数 × max(F - 1, 0)²)
变动工作量 = 客运权重 × 客运工作量 + (1 - 客运权重) × 货运工作量
固定支出 = 基期金额 × 固定比例 × 本项价格系数
变动支出 = 基期金额 × (1 - 固定比例) × 变动工作量 × 本项价格系数
```

能源、材料使用对应宏观实际价格指数及原分局价格弹性；`other` 价格系数暂为 1。人工的 V0.3 规则见下节。
固定是相对当年运量而言，仍然随投入价格变化。各项的年度成本占比不是常数。
能源和材料保留原拥挤系数；人工和其他暂设为零，但保留可配置字段。
工作量仍以客货运量代理，尚未计算职工人数、列车公里或实际耗电量。

`finance()` 返回 `cost_breakdown[业务][投入]`，含固定、变动、总额、价格系数、综合投入系数及工作量系数。
同时返回三项业务成本和四项投入成本；两种汇总以及固定加变动均与总成本对账。

## 历史工资高点与隐含用工调整

每项人工成本使用：

```text
W = 当年地区原始实际工资指数 / 100
H = max(100, 截至当年出现过的地区原始工资指数) / 100
人工成本 = 基期人工成本 × [固定比例 + (1 - 固定比例) × 变动工作量] × W × H^(-θ)
```

十二家分局统一先采用高速 θ=0.35、普速 θ=0.22、站务 θ=0.18。每项人工配置在
`cost_inputs[业务].wage.labor_adjustment_theta`，校验范围 0..1。
原 `wage_price_beta` 已移出运行暴露参数；仅保留 `reference_v02_wage_price_beta` 用于旧模型对照，
不再与 θ 叠乘。单位工资参考值使用原始 W，而不是减员后的综合人工系数。

`simulate_bureaus` 按年份、按地区维护运行高点，不使用未来数据，不使用三年平滑。
工资回落后 H 不回落，组织调整效果保留；客货运增加仍可增加变动人工需求。
独立调用 `finance` 必须显式提供 `wage_peak_index`（原始指数，不是倍数），且至少为 100、不能低于当年工资。
这是隐含退休减员／组织调整假设，尚未建模实际人数、招聘、解雇或投资自动化。

人工明细的 `price_factor` 为 W，`cost_adjustment_factor` 为 H^(-θ)，`unit_cost_factor` 为二者乘积。
后台诊断 `labor_retention_index` 为 100×H^(-θ)；`equivalent_staff_index` 另乘固定／变动工作量，
是相对本业务基期的等效用工，不是实际人数。两种诊断均不在玩家摘要中展示。

年度结果保留 A 原 V0.2、B 工资完全传导、C 当前规则的人工支出和经营结余。
同一年度三组共用运量、收入和非人工支出，因此结余差异可精确归因于人工变化。

## V0.3 配对审计

在 `map_research` 目录运行：

```powershell
py -3 -m unittest bureau_model.test_operations bureau_model.test_api
py -3 -m bureau_model.audit_labor
```

`reports/labor_comparison_v03.json`、同名 CSV 及 `labor_samples_96seeds_v03.csv` 保存
Seed 0..95 的十二分局对照：2085 年亏损占比、人工成本及其占比中位数、60 年累计结余、亏损年份数、
累计人工支出和后台等效用工诊断。额外核对旧报告中的 96 个示范检查点，不计入 96 Seed 分布。
累计计算统一为 2026..2085，不含基期。

本轮 1,152 个“分局×Seed”样本的 2085 年亏损占比 A/B/C 分别为 74.22%／74.39%／65.89%。
每个 Seed 先加总十二家分局的 2085 年人工支出，再取中位数，A/B/C 分别为 81.28／81.51／75.32 亿元。
这些是参数校准统计，不是现实预测或全国铁路总量。
页面的 96 Seed 报告只在版本和配置哈希与当前运行一致时加载；修改配置后需重跑审计并重启服务。

## 初始固定比例的校准

`import_prototype.py` 只读取压缩包 JSON，不执行其中代码。原成本构成比例转换为各项基期金额。
为保留原各分局的基期成本和固定成本预算，以如下固定比例作为模板：

| 业务 | 能源 | 人工 | 材料 | 其他 |
| --- | --- | --- | --- | --- |
| 高速 | 20% | 85% | 55% | 74% |
| 普速 | 25% | 85% | 50% | 78.8% |
| 站务 | 65% | 90% | 55% | 52.8% |

每个分局、每项业务对四个模板比例施加相同的 log-odds 偏移，使其加权平均精确匹配旧固定比例。
这样比例保持在 0..1，保留投入之间的固定程度排序，各分局配置也有差异。
这是一轮保持原预算的参数初始化，不代表真实账目校准；后续可以直接修改各分局 JSON。
`finance_base_yi` 中业务总成本是基期校验值；修改投入预算时必须同时更新对应总额。

## 历史 V0.2 独立成本拆分审计

在 `map_research` 目录运行：

```powershell
py -3 -m bureau_model.audit_costs
```

此历史审计需要本地原压缩包。运行时显式选择 V0.2 人工模式，忽略新 θ，使用 0..95 共 96 个 Seed，额外查看 20261014 和 5767783356797806。
输出 `reports/cost_comparison_v02.json`（含年度检查点、十二项明细、敏感性案例）和 CSV（分局分布对比）。
60 年累计结余统一计算 2026..2085，不含基期 2025。
同时对照压缩包已有 5,856 条年度记录，检查运量一致性和原成本公式复现。

报告的 `old` 为原公式；`split_only` 只拆固定比例并保留原全部投入的拥挤系数；
`new` 再取消人工、其他的拥挤附加。这样可以区分两个变化的影响。
基期预算一致不代表未来成本一致：不同价格路径、客货结构和拥挤状态会改变结果。
本轮不以提高盈利为校准目标，长期亏损允许存在。

若需要从原压缩包重新初始化（会覆盖当前配置），显式运行：

```powershell
py -3 -m bureau_model.import_prototype northeast12_bureau_prototype_v01.zip
```
