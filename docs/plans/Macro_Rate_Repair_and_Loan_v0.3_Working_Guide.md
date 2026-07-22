# 宏观—利率修复与贷款利率 v0.3 临时指导

## 文档用途

这是一份滚动更新的临时线路文档，用来把宏观审计问题与“短端、长端贷款基准分离”组织为连续但可分批验收的工作。它不是当前功能说明；文中只有明确标记为“已完成”的部分已经上线，其余公式和验收阈值仍是待实施计划。

完成全部任务后，应把最终事实分别更新到：

- `docs/models/Global_Macro.md`
- `docs/models/Regional_Macro.md`
- `docs/models/Finance_Contracts_and_Projects.md`
- `docs/reference/Finance_and_Valuation_Parameters.md`
- 必要的配置 Schema、API 契约和版本交接说明

正式文档更新并完成阶段提交后，删除本临时文档，不建立旧稿归档。

## 2026-07-22 阶段状态

已完成：

- 子 Goal 1.1“保留反馈诊断元数据”和 1.2“对账后重新执行字段边界”已在本地提交 `ba63702`（标签 `v0721a`）完成；
- 子 Goal 2“宏观反馈收敛契约与发布护栏”已在本地提交 `64c7a1e`（标签 `v0721b`）完成实现与数值验收；
- 子 Goal 3“输出缺口口径与增长斜率护栏”已完成本地合入和最终验收，并由本地标签 `v0721c` 固化；尚未推送 GitHub；
- 相关契约测试位于 `tests/test_macro_feedback_and_reconciliation_boundaries.py`；
- 当前区域对账后字段不再越过公开边界，宏观 raw 诊断和强度也不再被编排器清零。

仍未完成：

- 全球 2Y、10Y、美元指数及金融条件的系统性触底；
- 信用、能源和少数长期水平指标的饱和；
- `year_index=0` 的统一起点语义；
- 贷款利率 v0.3。

子 Goal 2 最终采用完整常量反馈更新和独立的无松弛固定点残差验证。此前 GPT Pro 候选使用递减调和 Mann 步长，虽然让相邻 Pass 的 80/80 Seed 显示收敛，但完整反馈影子检查只有 2/80 真正通过，因此没有直接合入。完成版保留其诊断、Manifest 和发布护栏框架，删除会机械缩小相邻差异的递减步长；严格八字段容差没有放宽。

子 Goal 2 完成后已重新运行 Goal 3 基线：调参集 `20261001..20261040` 与留出集 `20262001..20262040` 均为默认 60 年、各 2440 个 Seed-年份，80/80 Seed 通过收敛契约。Goal 3 的执行基线以 3.1 中这次 `v0721b` 复算结果为准，不再沿用收敛修复前的旧统计。

## 总目标

在不扩张贷款产品范围的前提下，先修复会污染区域利率和融资输入的宏观集成问题，再发布 `general-loan-rate-v0.3`：

```text
短期周转贷款     -> 区域政策利率
长期建设贷款     -> 区域 10 年期收益率
宽限期建设贷款   -> 区域 10 年期收益率

锁定年利率
  = 选定的区域基准利率
  + 产品利差
  + 期限 / 宽限利差
  + 信用利差
  + 杠杆利差
  -> 最终限制在 1.0%–9.5%
  -> 提款时锁定，存续期不重定价
```

这组任务改善的是宏观字段可信度、贷款期限选择和报价可解释性，不引入新的偿债或违约玩法。

## 当前基线与已知问题

### 当前健康部分

- 全球 GDP 金额、实际 GDP 指数和年度增长能够守恒。
- 实际政策利率、实际 10 年期利率和期限利差等主要恒等式成立。
- 14 个区域、61 年数据完整，区域 GDP 对账后能够回到全球 GDP。
- 当前贷款在提款季度锁定利率，利率上下限、信用压力、杠杆曲线和期限利差已经存在。

### 历史问题 A（已完成）：区域软对账后可能越界

修复前，区域原始 10 年期收益率在 `regional_macro_layer_sim.py` 中限制为 `0.05%–11%`，能源压力限制为 `0–100`，但 `regional_macro_reconciliation_sim.py` 在原始值上直接增加统一调整量，输出前没有按字段重新裁剪。

修复前抽样中已经观察到：

- 对账后区域 10 年期收益率最低达到 `-0.40%`；
- 对账后能源成本压力超过 `100`；
- 其它有明确物理边界的字段也存在同类风险。

这不是全球 GDP 守恒错误，但会让 Viewer、区域下游模型和未来长期贷款基准接收超出字段契约的值。当前已经建立单一边界表、对账后重新裁剪、裁剪计数和真实残差诊断；本问题保留在文档中仅用于解释修复背景。

### 历史问题 B（已完成）：宏观反馈诊断字段在编排合并时丢失

反馈校准层会生成：

- `macro_feedback_intensity_index`
- `macro_feedback_growth_raw_pct`
- `macro_feedback_stress_raw`
- `macro_feedback_inflation_raw_pct`
- `macro_feedback_policy_raw_pct`

修复前，`macro_run_orchestrator_sim.py` 的 `merge_feedback_paths()` 只保留五个 applied impulse 字段。最终 Run 中真实反馈冲击存在，而上述强度和 raw 诊断字段全部为零。

这会造成两类后果：

1. 全球 Viewer 把已经发生的反馈显示为零强度；
2. 区域层读取 `macro_feedback_intensity_index` 计算政策不确定性时得到零，低估区域政策不确定性及其后续宏观压力。

当前已明确 macro raw、macro applied 和 scenario applied 的合并语义，强度按宏观 applied impulse 重算；本问题保留在文档中仅用于解释修复背景。

### 问题 C：输出缺口与实际/潜在 GDP 水平没有完全闭合

全球层把 `output_gap_pct` 作为独立周期状态更新，同时又分别生成 `real_gdp_index` 和 `potential_gdp_index`。因此当前并不保证：

```text
output_gap_pct
  = 100 × ln(real_gdp_index / potential_gdp_index)
```

40 Seed 审计显示，这个问题比早期单 Seed 抽样更明显：

- 报告输出缺口的全部样本均值为 `-2.581%`，由实际/潜在 GDP 水平反推的严格缺口均值为 `-3.197%`；
- 40 个 Seed 的平均报告输出缺口全部为负；
- 30/40 个 Seed 的最后十年平均报告缺口低于 `-2%`；
- 两种口径最大绝对偏差达到 `6.575` 个百分点；
- 631 个 Seed-年份的绝对偏差超过 1 个百分点，277 个超过 2 个百分点。

GDP 金额、实际和潜在指数、年度增长本身仍然守恒，但“输出缺口”究竟是严格水平缺口，还是平滑后的周期压力状态，尚未在字段契约中说清；同时，全样本负偏说明还需要检查反馈支持与拖累是否形成了长期向下棘轮。

这个问题直接影响政策反应、区域增长、需求与风险解释，不能通过简单改名或强制赋值草率处理。

### 问题 D：宏观反馈默认迭代没有稳定收敛

默认运行固定执行 3 次反馈迭代，并根据最后一次 pass 的宽松阈值标记 `macro_feedback_converged`。40 Seed 审计中只有 31 个被标记为收敛，以下 9 个仍为 `false`：

```text
9, 11, 15, 16, 19, 22, 25, 29, 36
```

对其中 Seed 22、25、29、36 追加到 6 次迭代后均能按现有阈值收敛，但 pass delta 并非单调下降，而且三次与六次迭代的最终路径差异仍然很大：

- 政策利率单年最大差异达到 `2.0841` 个百分点；
- 10Y 单年最大差异达到 `2.4419` 个百分点；
- 美元指数单年最大差异达到 `14.9883` 点；
- HY 利差单年最大差异达到 `559.26 bps`；
- Brent 单年最大差异达到 `201.17 USD`。

因此，“固定跑三次”目前不是可靠的数值契约。发布链也没有阻止 `macro_feedback_converged=false` 的路径成为 Viewer 或贷款输入。必须先解决这一点，再校准利率和美元公式。

### 问题 E：全球短端、长端和美元指数系统性触底

当前公开硬边界为：

```text
全球 short / 2Y / 10Y：-0.35%–10.50%
美元指数：82–124
全球金融条件指数：-4–4
实际政策利率的名义政策下限：0.05%
```

40 Seed、2440 个 Seed-年份的默认三次迭代审计结果：

| 字段 | 触底 Seed | 触底年份 | 最长连续触底 |
|---|---:|---:|---:|
| 全球 2Y | 37/40 | 473 | 26 年 |
| 全球 10Y | 25/40 | 274 | 21 年 |
| 美元指数 | 34/40 | 341 | 16 年 |
| 全球金融条件指数下限 `-4` | 28/40 | 218 | 18 年 |

现存正式 Seed 也能复现：Seed 20261943 的 10Y 连续 5 年为 `-0.35%`、美元指数连续 8 年为 `82`；Seed 424242 的美元指数连续 2 年为 `82`。

所有发生 10Y 触底的审计 Seed 同时发生美元指数触底，说明这不是四个独立边界太窄，而是同一轮低利率—QE—弱美元链条的共同结果。当前还有三处语义风险：

1. 名义政策利率下限是 `0.05%`，但 `expected_short_rate_10y_pct` 使用收益率下限，允许长期停在 `-0.35%`，没有明确说明它代表可观察短端还是影子短端；
2. QE、负实际 10Y、宽松政策立场、负期限溢价和收益率曲线冲击高度相关，却分别进入 10Y 或美元目标，存在重复放大风险；
3. 美元指数由全球绝对利率驱动，而严格意义上的美元指数应主要反映美国相对其它地区的增长、利差和避险需求。当前字段更接近“美元资金条件指数”，名称和公式尚未完全一致。

单纯把下限改到 `-1%` 或 `70` 只会把平台移到更低位置，不能算完成修复。

### 问题 F：增长变化率形成机械硬斜率

GDP 层先把目标增长限制在上一年增长的 `±2.05` 个百分点，再以 `0.50` 速度平滑，因此最终相邻年度增长变化的有效硬边界正好是 `±1.025` 个百分点。

40 Seed 的 2400 个年度转换中，有 346 次精确命中 `±1.025`，覆盖 38/40 个 Seed，占 `14.4%`。这会让部分危机和复苏路径出现连续、等斜率的锯齿形状，也会拖慢实际 GDP 对潜在路径的回归。安全斜率本身可以保留，但不应成为常态动力学。

### 问题 G：其它指标存在次级饱和簇

以下边界没有越界，恒等式也没有破坏，但在默认基准路径中命中频率偏高：

| 字段与边界 | 命中 Seed | 命中年份 | 最长连续命中 |
|---|---:|---:|---:|
| 股票风险溢价上限 `12%` | 28/40 | 265 | 17 年 |
| 能源成本压力上限 `100` | 28/40 | 172 | 9 年 |
| 全球信用利差指数上限 `100` | 16/40 | 136 | 16 年 |
| 信贷可得性下限 `0` | 11/40 | 54 | 11 年 |
| 信用减值存量上限 `100` | 7/40 | 34 | 11 年 |
| 股票盈利指数上限 `460` | 4/40 | 18 | 7 年 |
| Brent 下限 `18 USD` | 4/40 | 13 | 4 年 |

这些项目不能一概视为错误：危机指数在极端年份触边是合理的。但长时间贴边会压扁“严重”和“灾难”之间的差异，固定水平上限也可能不适合 60 年指数。应先增加未裁剪目标和触边诊断，再决定是调整尺度、改用软饱和，还是保留硬边界。

现有两个区域存档没有再发生对账后越界，但全球触底会向区域传播：Seed 20261943 有 13 个年份发生区域 10Y 裁剪，9 个年份发生能源压力裁剪；对账后软残差会如实保留。这说明区域边界修复有效，但不能替代上游全球校准。

### 问题 H：`year_index=0` 起点语义不一致

正式文档说明第 0 行是起点，不是第一年运行结束；但当前各层处理方式不同：GDP 的实际与潜在指数保持 `100`，政策利率保持 `3.25%`，而通胀、收益率、美元、信用、盈利和油气压力中的许多字段已经执行了一次状态更新。

40 Seed 的第 0 行中：

- 全球 10Y 已在 `3.9288%–4.0858%` 之间随机变化，而状态初值是 `4.05%`；
- 美元指数已在 `101.3408–102.9962`，而状态初值是 `100`；
- HY 利差已在 `440.32–461.14 bps`，而状态初值是 `420 bps`；
- 股票盈利指数已在 `103.03–105.13`，而状态初值是 `100`；
- GDP 的实际与潜在指数都为 `100`，但报告输出缺口已在 `-1.1774%–1.1573%` 随 Seed 变化。

这会让“起点值”“第一期估计值”和“第一年结束值”混在同一行。它暂未破坏年度序列，但会影响初始贷款报价、Viewer 比较和固定 Seed 的经济解释，需要单独决定统一口径。

### 当前贷款定价的实际结构

`city_airport_financial_state_layer_sim.py` 当前对所有没有手工利率的贷款统一读取 `input_10y_yield_pct`，再用 `short_term_reference_adjustment_pct` 区分短期产品。前端 `operations-actions.js` 复制了同一逻辑。

当前数据链只传递：

- `input_10y_yield_pct`
- `input_hy_spread_bps`

尚未把区域政策利率传入城市年度数据、季度经营数据和北京经营 API。因此贷款 v0.3 不是只替换一个字段，还需要补齐一条权威输入链。

## 范围和执行顺序

整份指导可以作为一个阶段 Goal，但实施应拆成六个可独立回退的子 Goal。修复顺序必须遵守“数值收敛 -> GDP 口径 -> 利率与美元 -> 次级饱和 -> 贷款输入”的依赖关系，不得把多组数值变化混成一次无法解释的巨大差异。

### 子 Goal 1（已完成）：宏观字段与区域边界修复

#### 1.1 保留反馈诊断元数据

任务：

1. 明确 applied impulse、raw diagnostic 和 scenario metadata 三类字段集合。
2. `merge_feedback_paths()` 合并宏观反馈与情景反馈时，保留宏观 raw 诊断和强度字段。
3. 情景与宏观反馈重叠时：
   - applied impulse 按现有规则相加；
   - 宏观 raw 字段保持宏观反馈原值，不把情景冲击伪装成宏观 raw 值；
   - 总强度应依据最终 applied impulse 重新计算，或明确拆成宏观强度与情景强度，不能静默覆盖。
4. 验证全球 Viewer 不再把真实反馈显示为零。
5. 验证区域 `policy_uncertainty_index` 和 `regional_macro_stress_index` 收到预期的小幅变化。

验收：

- 有 applied feedback 的年份，强度不能全部为零；
- 无反馈年份仍为零；
- raw 字段与反馈校准层输出一致；
- 固定 Seed 的变化仅限预期字段及其明确下游；
- 更新宏观接口版本和固定 Seed 数值基线。

难度：低—中。建议使用较强编码模型；重点是字段语义和合并规则，不是算法复杂度。

#### 1.2 对账后重新执行字段边界

任务：

1. 为所有对账字段建立单一边界表，不在输出组装处散落临时常数。
2. 对账后的区域字段重新裁剪，至少覆盖：
   - 政策利率；
   - 10 年期收益率；
   - 宏观压力；
   - 能源成本压力；
   - 其它原始层明确限制为 `0–100` 的指数。
3. 诊断文件同时记录：
   - 请求的统一调整量；
   - 边界裁剪后的实际加权结果；
   - 被边界裁剪的区域数量；
   - 裁剪后与全球锚的残差。
4. 不为了追求零残差而反复把所有区域压在同一边界；GDP 继续硬对账，其它指标继续保留“软对账”语义。

验收：

- 对账后字段不再突破自己的公开边界；
- `regional_reconciliation_quality` 使用裁剪后的真实残差；
- 14 区 GDP 份额与增长贡献守恒不受影响；
- 多 Seed、60 年抽样中不存在边界回归；
- Viewer 和下游读取到的值与诊断文件一致。

难度：中。建议使用较强编码模型，并要求它能处理加权对账、边界裁剪和诊断口径。

### 子 Goal 2（已完成）：宏观反馈收敛契约与发布护栏

#### 2.0A 完成记录（2026-07-21）

最终契约为：最少 3 次、最多 16 次反馈回跑，最后两个相邻 Pass 均须通过八字段严格门槛，并额外执行一次不带松弛的影子 Pass 验证候选路径的固定点残差。默认反馈更新系数为常量 `1.0`；`feedback_iterations=1` 仍保持一次完整回跑的历史数值语义。影子 Pass 只作验证，正式输出仍来自最后一个被接受的完整模型 Pass。

正式 60 年审计结果：

- 调参集 `20261001..20261040`：`40/40` 通过；
- 留出集 `20262001..20262040`：`40/40` 通过；
- 迭代分布：`6:1, 7:2, 8:11, 9:31, 10:30, 11:5`；
- `66/80` 需要超过 8 次，已按成本风险明确记录；没有 Seed 触及 16 次硬上限；
- 最终没有 Seed 以 delta bounce 结束；所有 Seed 的最后两个相邻诊断和无松弛固定点残差均逐字段通过；
- `PYTHONHASHSEED=1/2/3` 的全球路径与收敛摘要一致；另修复经营层组件分配使用无序集合造成的 `0.0001` 跨进程舍入差异；
- 严格门槛保持增长 `0.15pp`、通胀 `0.20pp`、政策/2Y/10Y 各 `0.25pp`、美元 `1.5`、HY `100bps`、Brent `20 USD`；没有修改任何经济层系数。
- 收敛定向测试 `78/78`、完整 Python 3.13 测试 `426/426` 通过；真实 12 年 baseline + occurred scenario 的 seed-cache 编排演练完成，两条 variant 均通过 Manifest Schema、固定点残差与发布授权检查。

实现版本为 `global-macro-feedback-calibration-v0.3`、`macro-feedback-interface-v0.4`、`constant-relaxation-with-residual-check-v1` 和 `macro-feedback-fixed-point-residual-v1`。Manifest 保存完整相邻 Pass 与残差诊断；缺失、旧版、被放宽或未通过的 convergence 元数据只能归档，不能发布 Viewer。当前状态尚未 Git 提交、打 Tag 或推送；提交由后续阶段统一处理。

#### 2.0B 历史执行任务身份

本节是一份可以直接交给编码模型执行的工作规格。执行者应把自己视为“现有失败实现的接手者”，而不是从空白项目开始：

1. 先读取本节、当前 `git diff` 和所有相关测试，再修改代码；
2. 保留用户工作区中与本任务有关的合理改动，不使用 `git reset --hard`、`git checkout --` 或其它覆盖式回退；
3. 一次只完成子 Goal 2，不进入输出缺口、收益率—美元、次级饱和或贷款 v0.3；
4. 持续执行到全部验收项通过，或者触发本节规定的停止条件；
5. 不提交、不打 Tag、不推送 GitHub，最终由上游审查者决定是否保留；
6. 最后按本节模板报告改动、实验、测试、未决风险、耗时和可获得的 Token 用量。

难度：高。规划已经由本节提供，适合交给编码执行力强、能够稳定运行测试并根据结果迭代的模型。执行者仍需具备足够的数值推理能力，不能只做机械替换。

建议给 Composer 2.5 的入口提示词保持简短，避免重复整份背景：

```text
在 C:\d_e\oiltanker\airport 中，严格执行
docs/plans/Macro_Rate_Repair_and_Loan_v0.3_Working_Guide.md
的“子 Goal 2（待重做）：宏观反馈收敛契约与发布护栏”。

当前工作区包含上一轮未通过验收的实现和用户其它改动。先读完整的 2.0–2.10、
git status、git diff 与相关测试，在现有实现上修复；不要覆盖、提交、打 Tag 或推送。
按阶段 A–F 持续执行，只有满足 2.9 的全部完成条件才能宣布完成；触发停止条件时
按 2.10 输出阻塞报告。不要进入子 Goal 3–6，也不要靠放宽容差或更新失败基线过关。
```

#### 2.1 唯一目标

把宏观反馈循环从“固定回跑若干次后取最后一次结果”改造成可验证、确定、可拒绝发布的数值契约：

```text
同一 Seed + 同一参数 + 同一代码版本
  -> 得到相同的 pass 序列和最终路径
  -> 至少运行最小迭代次数
  -> 只有连续两个 pass 均满足逐字段容差才可提前停止
  -> 达到硬上限仍未满足时保留 Run 诊断，但拒绝 Viewer 发布
```

本任务可以改变“如何求取反馈固定点”，但不能改变宏观模型想表达的经济关系。也就是说，可以调整确定性的阻尼、松弛、停止和循环检测机制；不能借机调整 GDP、通胀、政策利率、2Y、10Y、美元、信用或油价公式中的经济系数。

#### 2.2 历史接手基线

当前未提交工作区已经包含一轮实现尝试，执行者必须先复现以下事实：

- 主要实现位于 `macro_layers/global_macro_feedback_calibration_sim.py`；
- `macro_layers/macro_run_orchestrator_sim.py` 和 `macro_layers/regional_macro_layer_sim.py` 已尝试共用收敛循环；
- `macro_layers/orchestrator_run_validation.py` 已尝试增加 Manifest 摘要与发布拒绝线；
- `tests/test_macro_feedback_convergence_contract.py` 已存在，但部分断言仍写死旧容差；
- 当前默认候选是 `min=3`、`max=8`、连续 2 次通过；
- 当前实现把逐字段容差放宽为增长 `0.30pp`、通胀 `0.35pp`、政策 `0.75pp`、2Y `0.90pp`、10Y `0.85pp`、美元 `5.5`、HY `120bps`、Brent `25 USD`；
- 固定审计集 `20261001..20261040` 当前仅 `33/40` 收敛；
- 未收敛 Seed 为 `20261003`、`20261012`、`20261013`、`20261017`、`20261025`、`20261031`、`20261039`；
- 9 个 Seed 的最终 composite delta 发生反弹；
- 当前 44 项定向测试有 7 项失败，其中 3 项来自测试仍按旧容差构造，4 项来自多 Seed 验收；
- `_iteration_diff_report.py` 仍描述旧候选容差，并把“相邻 pass 收敛”错误解释成“三次路径与最终路径的总差异必然在容差内”；
- 固定 Seed 摘要在不同 `PYTHONHASHSEED` 下出现过不一致。执行者需要判断它是否由本轮改动引入；若无关，不得顺手扩大范围，但必须在报告中留下可复现证据。

接手后的第一条命令必须是：

```powershell
git status --short
```

然后运行当前失败基线，不得先改测试掩盖失败：

```powershell
py -3.13 -m unittest tests.test_macro_feedback_convergence_contract
```

#### 2.3 允许修改的范围

核心实现文件：

- `macro_layers/global_macro_feedback_calibration_sim.py`
- `macro_layers/macro_run_orchestrator_sim.py`
- `macro_layers/regional_macro_layer_sim.py`
- `macro_layers/orchestrator_run_validation.py`

契约、版本和文档文件，仅在实现通过验收后同步：

- `config/airport_versions.json`
- `schemas/macro-run-manifest.schema.json`
- `schemas/airport-version-record.schema.json`
- `schemas/api-envelope.schema.json`
- `docs/models/Global_Macro.md`
- `docs/reference/API_and_Data_Contracts.md`
- 本临时指导文档

测试与固定基线：

- `tests/test_macro_feedback_convergence_contract.py`
- `tests/test_orchestrator_run_validation_service.py`
- `tests/test_long_horizon_contract.py`
- `tests/test_safety_baseline.py`
- 只有在字段或版本契约确实改变时，才更新对应 fixture 或 digest；不得把无法解释的数值变化直接接受为新基线。

超出以上清单的文件默认不修改。确实需要新增一个小型测试辅助模块或审计脚本时，应放在 `tests/` 或项目认可的开发脚本目录中，并在最终报告解释用途；不要继续向项目根目录堆积 `_audit_*`、`_verify_*` 一次性文件。

#### 2.4 不可违反的约束

1. 不修改任何宏观经济系数来追求收敛。
2. 不把容差提高到“刚好覆盖最差 Seed”；容差是业务稳定性标准，不是测试数据包络线。
3. 不以单纯增加最大迭代次数作为唯一修复。提高硬上限只能作为经过性能和收敛分布验证后的安全余量。
4. 不删除失败 Seed，不减少 60 年长度，不把失败改成 warning。
5. 不把连续两次收敛降为一次，也不只判断 composite index；八个逐字段门槛均为权威条件。
6. 不通过输出路径取平均、选择“看起来较平滑”的某个旧 pass 或裁剪 delta 来伪造收敛。最终结果必须来自一次合法的完整模型 pass。
7. 不把边界命中后的相同值自动视为稳定；必须保留前后 pass 的触底、触顶计数，必要时比较未裁剪目标。
8. 不改变 scenario 与 macro feedback 的合并语义。尤其要核对 pass 0 是否包含 scenario feedback，并修正任何与实际行为不一致的注释。
9. `feedback_iterations=1` 必须继续表示一次反馈回跑，除新增诊断字段外，原有数值路径不得无理由变化。
10. 不在测试通过前升级最终版本号；若当前工作区已经提前升级，最终必须明确说明是保留、调整还是回退，不能留下半完成版本。
11. 不提交、不清理用户不相关改动、不删除无法确认归属的未跟踪文件。

#### 2.5 收敛字段和诊断契约

每一对相邻 pass 至少比较以下字段在 `year_index=1..years` 的最大绝对差和平均绝对差：

| 字段 | 单位 | 初始目标容差 |
|---|---|---:|
| `realized_growth_pct` | 百分点 | `0.15` |
| `headline_inflation_pct` | 百分点 | `0.20` |
| `global_policy_rate_pct` | 百分点 | `0.25` |
| `global_2y_yield_pct` | 百分点 | `0.25` |
| `global_10y_yield_pct` | 百分点 | `0.25` |
| `global_dollar_index` | 指数点 | `1.5` |
| `global_high_yield_spread_bps` | bps | `100` |
| `brent_oil_price_usd` | USD | `20` |

这些值是要优先恢复并验证的稳定性目标，不是不可讨论的永恒常数。如果执行者认为某一目标不合理，必须先输出该字段在调参集和留出集上的 pass delta 分布、经济解释以及替代值，再做最小修改。禁止仅引用“95 分位刚好是多少”作为放宽理由。

每个 Run 的内存结果和 Manifest 摘要至少包含：

```text
converged
convergence_reason
iterations_run
min_iterations
max_iterations
consecutive_converged_passes
last_pass_converged
delta_bounced
last_pass_delta_index
max_pass_delta_index
pass_diagnostics[]
```

每个 `pass_diagnostics` 至少包含：

- 八个字段的 max delta 与 mean delta；
- `from_pass`、`to_pass`；
- 逐字段容差版本或可追踪的参数来源；
- 前后 pass 的边界命中计数；
- `pass_converged`；
- composite delta 仅作诊断，不作为替代逐字段判断的门槛。

#### 2.6 分阶段执行流程

##### 阶段 A：冻结事实和修正测试契约

1. 保存当前 `git status --short` 与 `git diff --stat` 到最终报告，不写入临时根目录文件。
2. 重跑 44 项定向测试，记录实际失败名称。
3. 把基础测试中的魔法数字改成从 `MacroFeedbackParams` 读取，或显式构造专用参数；测试注释、输入差值和断言必须使用同一容差。
4. 保留至少一个“只突破单字段就失败”的参数化测试，八个字段逐一覆盖。
5. 修正迭代差异报告：明确区分“相邻两个最终 pass 的 delta”和“固定 3 次结果与最终结果的总差异”，不得再声称后者天然受前者约束。
6. 在算法尚未修好时，多 Seed 测试必须继续失败，不能先更新预期为 `33/40`。

阶段 A 完成标志：基础单元测试能准确表达契约，多 Seed 测试仍真实暴露算法失败。

##### 阶段 B：诊断不收敛的数值形态

对 7 个已知失败 Seed 和至少 3 个稳定 Seed 输出逐 pass 诊断，回答：

1. delta 是单调下降、缓慢下降、两周期振荡、多周期振荡，还是被边界切换触发跳变；
2. 哪些字段最先失稳，哪些字段只是下游响应；
3. 当前 `feedback_iteration_relaxation=0.25` 在每个失败 Seed 上的有效行为；
4. 增加到 12、16、20 次时是最终收敛，还是继续形成极限循环；
5. 边界命中是否让两个不同的未裁剪路径看起来相同；
6. scenario variant 与 baseline 是否使用同一停止逻辑且保持原合并语义。

诊断必须形成结构化测试输出或可复用测试辅助函数，不能只在聊天里凭观察下结论。

##### 阶段 C：选择最小确定性求解策略

根据阶段 B 的证据，只选择一种主策略实现。允许考虑：

- 当 composite 或关键字段 delta 连续反弹时，按确定规则降低松弛系数；
- 对检测到的两周期振荡启用确定性的额外阻尼；
- 使用预先定义、与 Seed 无关的松弛日程；
- 在保持经济公式不变的前提下，把反馈更新写成更清晰的阻尼固定点步骤；
- 在证明确有必要后，把硬上限提高到 12 或 16，同时保持提前停止。

主策略必须满足：

- 相同输入完全确定；
- 不读取墙钟、进程顺序或未固定的全局随机状态；
- 不针对具体 Seed 写特殊分支；
- 不依赖未来年份之外的信息；
- 最终返回合法完整 pass；
- 代码中解释它处理的数值现象，而不是只写“让测试通过”。

若需要比较多种策略，可以先用局部实验，但最终代码只保留被选择的策略和必要诊断，不保留三套半成品求解器。

##### 阶段 D：集成三个入口和发布护栏

统一以下三个入口，避免各自复制循环：

```text
global_macro_feedback_calibration_sim.py standalone
regional_macro_layer_sim.py standalone
macro_run_orchestrator_sim.py full Run
```

要求：

1. 三者使用同一迭代边界解析、同一求解器、同一收敛摘要；
2. CLI 的 `feedback_iterations` 明确表示最大回跑次数，`min_feedback_iterations` 表示最小门槛；
3. 参数为 0、1、`min > max` 和缺失旧参数时有明确、测试覆盖的行为；
4. 发布 `baseline` 或 scenario variant 时，目标 variant 的 `convergence.converged` 必须为 true；
5. 新格式 Manifest 中缺失 convergence block 必须拒绝发布并给出可操作错误；
6. `--publish-viewer none` 仍允许保留未收敛开发 Run；
7. 旧归档 Manifest 的读取兼容与“能否重新发布”必须区分，不能因为兼容读取而绕过新发布护栏。

##### 阶段 E：调参集、留出集和跨进程验收

调参审计集固定为：

```text
20261001..20261040
```

不得在调参过程中查看后再排除其中任何 Seed。算法确定后，再运行未参与调参的留出集：

```text
20262001..20262040
```

两组均使用：

```text
years=60
start_year=2025
initial_gdp=100.0
volatility_scale=1.0
scenario_state=none
```

验收要求：

- 调参集 `40/40` 收敛；
- 留出集 `40/40` 收敛；
- 每个 Seed 最后连续两个 pass 均逐字段通过；
- 没有 Seed 以 `max_iterations_reached` 结束；
- 记录迭代次数分布，优先目标为绝大多数不超过 8 次，任何 Seed 不超过最终版本化硬上限；
- 若超过 10% 的 Seed 需要 8 次以上，报告运行成本和原因，不得隐去；
- 记录 delta bounce 数量；bounce 可以作为诊断存在，但发生时仍须证明最后连续两次逐字段通过；
- baseline 和至少一个 scenario variant 各做一次确定性复跑；
- 使用至少 `PYTHONHASHSEED=1,2,3` 的独立 Python 进程比较全局行与收敛摘要的规范化哈希；
- 若跨进程差异来自本任务之外的既有下游模块，提供最小复现并停止扩大范围，由上游决定是否另立 Goal。

##### 阶段 F：版本、文档和工作区收尾

只有阶段 E 全部通过后才允许：

1. 确认并统一模型、编排器和相关接口版本；
2. 更新 Schema、API fixture、header digest 和固定 Seed baseline；
3. 对每个 digest 变化说明是“新增字段”“迭代路径变化”还是其它原因；
4. 更新 `Global_Macro.md` 和 API 契约中的参数与 Manifest 字段；
5. 在本临时文档把子 Goal 2 标记为已完成，并写入实际阈值、硬上限、80 Seed 结果和提交状态；
6. 清点根目录中的一次性审计文件，只报告哪些可以删除，不擅自删除无法确认归属的文件；
7. 运行完整 Python 3.13 测试；不得用更新 baseline 的方式吞掉未解释失败。

#### 2.7 必须存在的测试层次

| 层次 | 最低覆盖 |
|---|---|
| 纯函数 | 八字段 max/mean delta、逐字段单独突破、连续 pass 计数、bounce、边界计数 |
| 求解器 | 最小门槛、提前停止、硬上限、振荡处理、确定性、合法最终 pass |
| 入口一致性 | standalone、regional standalone、orchestrator 使用同一契约 |
| Manifest | 收敛摘要字段、Schema、字段缺失、版本一致性 |
| 发布护栏 | 已收敛 baseline/scenario 可发布；未收敛或缺失摘要拒绝；none 可归档 |
| 数值审计 | 40 Seed 调参集 + 40 Seed 留出集，均为 60 年 |
| 回归 | 固定 Seed、长期路径、scenario 语义、Python 3.13 完整测试 |
| 跨进程 | `PYTHONHASHSEED=1,2,3` 规范化结果一致 |

测试不得依赖执行顺序，不得把 warning 当作验收成功，也不得在生产代码中加入只供测试 Seed 使用的分支。

#### 2.8 推荐验收命令

执行者可以根据最终测试拆分调整模块名，但至少应提供等价命令并全部通过：

```powershell
py -3.13 -m unittest tests.test_macro_feedback_convergence_contract
py -3.13 -m unittest tests.test_orchestrator_run_validation_service
py -3.13 -m unittest tests.test_safety_baseline
py -3.13 -m unittest tests.test_long_horizon_contract
py -3.13 -m unittest discover -s tests -p "test_*.py"
```

跨进程确定性必须由新 Python 进程完成，不能在同一解释器里重复调用两次就宣称成立。

#### 2.9 完成、失败与停止条件

只有以下条件全部成立，执行者才能报告“子 Goal 2 完成”：

- 80/80 固定审计 Seed 收敛；
- 连续两次逐字段门槛真实满足；
- 发布护栏和 Manifest 契约通过；
- 三个运行入口统一；
- 跨进程确定性通过或已证明差异完全属于另一个既有模块；
- 定向测试和完整测试全部通过；
- 没有修改经济系数，没有 Seed 特判，没有以容差膨胀代替求解；
- 版本、Schema、正式文档和固定基线一致；
- 工作区没有新增无说明的临时文件。

遇到以下任一情况必须停止并报告“阻塞”，而不是继续扩大改动：

- 在不修改经济系数的约束下，调参集或留出集仍无法在硬上限内收敛；
- 需要人类决定容差的经济含义；
- scenario 原有语义无法从现有测试和文档中确定；
- 跨进程不确定性来自本任务范围外且会影响验收；
- 必须改变输出缺口、利率、美元、信用或油价公式才能继续。

阻塞报告必须列出最小复现、已尝试策略、失败 Seed、逐字段 delta、建议的人类决策，不得只写“模型复杂”或“测试失败”。

#### 2.10 执行模型最终报告模板

```text
状态：完成 / 阻塞 / 未完成

改动：
- 文件与职责
- 选择的求解策略及原因
- 明确未改动的经济系数

数值结果：
- 调参集：x/40
- 留出集：x/40
- 迭代次数分布
- delta bounce 数量
- 最差 Seed 与最差逐字段 delta

测试：
- 定向测试命令与结果
- 完整测试命令与结果
- PYTHONHASHSEED=1/2/3 结果

版本与文档：
- 版本变化
- Schema/API/digest 变化原因

工作区：
- git diff --stat
- 新增临时文件
- 未提交、未打 Tag、未推送确认

成本：
- 墙钟时间
- 模型调用轮数或 turns
- 输入/输出/缓存 Token（仅在工具真实提供时填写）
- 若无法获得精确 Token，明确写“不可获得”，不得估算成精确值

剩余风险：
- 无 / 逐项列出
```

## 子 Goal 3–6 通用执行协议

后续四个子 Goal 共用以下规则，具体章节可以直接交给执行模型：

1. 每次会话只执行一个子 Goal，不把 3–6 合并为一次修改。
2. 开始时读取当前 `git status --short`、目标章节、相关正式文档、核心实现和测试；当前工作区是 dirty 状态，不覆盖用户改动。
3. 先复现章节中的基线，再写测试和实现；没有复现证据不得直接更新固定 Seed baseline。
4. 数值修改必须先产生诊断，再改变公式，最后才更新版本、Schema、fixture 和文档。
5. 不提交、不打 Tag、不推送；不使用 `git reset --hard`、`git checkout --`，不删除无法确认归属的未跟踪文件。
6. 触发章节停止条件时输出阻塞报告，不擅自跨入下一个 Goal 寻找绕路。
7. 最终报告沿用子 Goal 2 的 2.10 模板，必须包含调参集、留出集、测试、差异解释、Git 状态、墙钟时间和工具真实提供的 Token 数据。
8. 推荐入口提示词只需要写：“严格执行本文件的子 Goal N 及通用执行协议；不要进入其它 Goal；完成后按 2.10 报告。”

### 子 Goal 3（已实施）：输出缺口口径与增长斜率护栏

#### 3.0 前置条件与执行结论

只有子 Goal 2 已通过验收，当前默认宏观路径能够稳定收敛，才允许实施本 Goal。若收敛契约仍失败，立即停止；不能在一个不稳定求解器上校准 GDP 口径。

本阶段预先采用以下口径，避免让执行模型自行做经济学二选一：

- `output_gap_pct` 保留为模型估计的周期缺口状态，政策层、区域层和现有 Viewer 继续读取它；
- 新增严格水平诊断 `gdp_level_gap_pct = 100 × ln(real_gdp_index / potential_gdp_index)`；
- 新增 `output_gap_measurement_residual_pct = output_gap_pct - gdp_level_gap_pct`；
- 正式文档必须明确两者不同：前者是平滑、带冲击记忆的不可观测状态估计，后者是由两个已发布水平严格反推的会计诊断；
- 本阶段不把 `output_gap_pct` 强制赋值成水平缺口，也不删除现有字段。

选择这一方案是为了避免一次性重写政策、区域和航空层，同时让玩家和开发者能看见两个口径的偏差。若审计证明估计状态没有独立解释力，应停止并由上游另行决定是否在未来正式废弃它。

#### 3.1 当前基线

执行者必须从提交 `64c7a1e` / 标签 `v0721b` 复现并记录以下基线。每组包含 40 个 Seed、2440 个年度观测和 2400 个年度转换：

| 指标 | 调参集 `20261001..20261040` | 留出集 `20262001..20262040` |
| --- | ---: | ---: |
| 收敛 Seed | 40/40 | 40/40 |
| `output_gap_pct` 全样本均值 | `-1.6723%` | `-1.7055%` |
| 严格水平缺口均值 | `-2.0716%` | `-2.1058%` |
| 平均估计缺口为负的 Seed | 40/40 | 40/40 |
| 最后十年平均估计缺口低于 `-2%` | 14/40 | 16/40 |
| 两种缺口最大绝对偏差 | `4.2443pp` | `3.4327pp` |
| 绝对偏差超过 `1pp` / `2pp` 的观测 | 494 / 92 | 507 / 129 |
| 精确命中增长变化 `±1.025pp` | 106/2400 | 106/2400 |
| 至少命中一次的 Seed | 35/40 | 33/40 |
| 单个 Seed 最长连续命中 | 5 年 | 4 年 |

调参集用于定位和校准；留出集只能在候选方案形成后用于验收，不得根据留出结果反复调参。`year_index=0` 当前仍可能出现严格水平缺口为零而估计缺口非零，这是已知的起点语义问题，留给子 Goal 5；Goal 3 不得借机修改随机消费顺序或初始行契约。

#### 3.2 允许修改范围

核心文件：

- `macro_layers/global_gdp_annual_sim.py`
- `macro_layers/global_macro_feedback_calibration_sim.py`
- `macro_layers/global_policy_rate_layer_sim.py`
- `macro_layers/regional_macro_layer_sim.py`
- `macro_layers/macro_run_orchestrator_sim.py`

字段发布与 Viewer：

- `web/static/js/global-gdp/data-client.js`
- `web/static/js/global-gdp/renderers.js`
- 对应 Header、Schema、Manifest、API fixture 和正式宏观文档

测试建议独立新增 `tests/test_global_gdp_gap_and_growth_contract.py`，同时更新长期路径、固定 Seed、区域守恒与 Viewer 数据契约测试。不得借本 Goal 修改收益率、美元、信用、能源或贷款公式；它们只能因新的 GDP 路径产生可解释的下游变化。

#### 3.3 不可违反的约束

1. `global_gdp_trillion_usd`、`real_gdp_index`、`potential_gdp_index` 和 `realized_growth_pct` 的恒等关系必须继续成立。
2. `gdp_level_gap_pct` 必须由已发布实际和潜在指数直接计算，误差只允许来自统一的输出舍入。
3. 不通过把估计缺口整体加常数来消除负均值；必须定位负偏来自反馈、冲击、持久性还是增长追赶机制。
4. 不简单删除增长安全边界或把 `max_growth_step_pct` 提到极大值。
5. 不把硬斜率从 `1.025pp` 平移成另一个经常命中的固定斜率。
6. 不为了使均值接近零而强制每个 Seed 对称；长期危机路径可以偏负，但基准分布不能全部单向。
7. 不改政策反应系数、区域弹性或航空需求系数；只验证这些下游收到的输入变化。
8. 不在同一修改中处理 `year_index=0`，该语义属于子 Goal 5。

#### 3.4 必须新增的 GDP 诊断

每个年度至少发布：

```text
gdp_level_gap_pct
output_gap_measurement_residual_pct
unclamped_output_gap_target_pct
output_gap_floor_applied
output_gap_cap_applied
unclamped_target_growth_pct
growth_step_limit_pct
growth_step_cap_applied
growth_step_cap_direction
growth_step_cap_consecutive_years
```

`growth_step_limit_pct` 必须记录本年实际使用的安全限制。若最终采用软限制，还应区分软限制生效和外层硬安全边界生效，避免 Viewer 把两者混为一谈。

#### 3.5 分阶段执行

##### 阶段 A：只加诊断，不改路径

先新增纯诊断字段和审计测试，证明数值路径与子 Goal 2 完成版逐行一致。输出调参集和留出集的缺口偏差、增长斜率命中、连续命中和反馈正负贡献分布。

##### 阶段 B：定位长期负偏

至少分解并报告：

- output gap persistence；
- cycle 与 shock loading；
- feedback output-gap impulse；
- 由潜在 GDP 产生的追赶增长；
- direct cycle/shock growth；
- feedback growth impulse；
- 信用和金融压力经反馈回到 GDP 的路径。

对相关项做离线消融或影子计算，但不能把消融结果直接发布为正式路径。回答负偏是结构性单向棘轮、恢复速度不足，还是危机分布本身造成。

##### 阶段 C：修复增长限制动力学

优先考虑“平滑软限制 + 极端硬安全边界”：正常变化通过连续函数压缩，只有极端异常才触发外层硬边界。允许选择其它可解释策略，但必须满足：

- 正常衰退和复苏不形成长串等斜率；
- 危机年份仍有最大安全变化；
- 复苏方向不会因限制器天然弱于衰退方向；
- 相同 Seed 完全确定；
- 限制器参数与经济冲击参数分开版本化。

##### 阶段 D：校准估计缺口的恢复与支持/拖累

只修改与估计缺口、增长追赶和宏观反馈对 GDP 的直接关系有关的最小参数。每次只改变一个参数集并生成前后分布。禁止同时调整政策、收益率、美元、信用或油价层来抵消结果。

##### 阶段 E：下游与文档验收

验证政策层明确读取 `output_gap_pct`，区域层同时可追踪估计缺口与严格水平缺口，Viewer 明确标注两个口径。比较全球增长、政策、区域份额、区域增长和中国航空需求的差异，但不在此 Goal 调整下游公式。

#### 3.6 验收标准

- 调参集和留出集各 40 Seed、60 年全部通过 GDP 恒等式；
- `gdp_level_gap_pct` 与公式逐行一致；
- 精确命中增长硬安全斜率的年度转换低于 `2%`，单个 Seed 连续命中不超过 2 年；
- 正常年份不出现另一个高频固定斜率平台；
- 调参集与留出集的长期估计缺口不再全部同向负偏；若仍明显偏负，必须有与冲击分布一致的证据，而不是一句“长期增长较弱”；
- 最后十年平均估计缺口低于 `-2%` 的 Seed 数量相较 `30/40` 明显下降，推荐目标不高于 `8/40`，留出集不得明显恶化；
- 估计缺口和严格水平缺口的残差已有正式语义、分布报告和 Viewer 标签；
- 子 Goal 2 的 80 Seed 收敛契约继续全部通过；
- 全球—区域 GDP 守恒、固定 Seed、长期路径和完整 Python 3.13 测试通过；
- 所有数值变化可归因于 GDP/反馈参数，不夹带其它模型系数变化。

#### 3.7 停止条件

以下情况停止并报告：必须修改输出缺口的经济身份；负偏只能通过调整政策/信用/油价公式消除；增长软限制破坏危机安全边界；留出集相较调参集明显反向恶化；或任何改动使宏观反馈重新不收敛。

建议入口提示词：严格执行本文件通用协议和子 Goal 3 的 3.0–3.7；不要进入收益率、美元、次级饱和或贷款实现；完成后按 2.10 报告。


#### 3.8 实施记录（2026-07-21）

本阶段按 A–E 顺序完成，未进入子 Goal 4–6。纯诊断阶段对 80 个审计 Seed 的原 231 个全球字段逐行做规范化哈希，修改前后完全一致；随后才冻结动力学候选。

根因分解显示，周期项长期均值接近零，负偏主要来自危机 shock 与金融反馈的同向负载。旧反馈把 `feedback_growth_impulse_pct` 既直接送入 GDP，又在 `feedback_output_gap_impulse_pct` 中重复写入增长和 HY 压力；较高缺口持久性把这些负冲击保留为单向棘轮，而只在压力高于 45 时工作的旧 stress drag 对平静期恢复几乎没有帮助。

冻结候选只改 GDP/反馈最小参数集：

- `output_gap_persistence: 0.68 → 0.35`；
- stress 通道由 `-0.018 × max(stress-45, 0)` 改为围绕 35 的对称 `-0.030 × (stress-35)`；
- `feedback_output_gap_impulse_pct` 不再重复加入增长和 HY，保留居中的银行放贷意愿、信用损伤和风险偏好信号；
- 增长目标步长采用膝点 `1.30pp`、尺度 `1.80pp` 的连续对数软限制，实际增长步长外层硬边界为 `1.45pp`。

正式审计结果：

| 指标 | 调参集（前 → 后） | 留出集（前 → 后） |
| --- | ---: | ---: |
| 收敛 Seed | `40/40 → 40/40` | `40/40 → 40/40` |
| 估计缺口全样本均值 | `-1.6723% → -0.3824%` | `-1.7055% → -0.3945%` |
| 严格水平缺口均值 | `-2.0716% → -1.0711%` | `-2.1058% → -1.0854%` |
| 平均估计缺口为负的 Seed | `40 → 35` | `40 → 39` |
| 末十年均值低于 `-2%` | `14 → 2` | `16 → 3` |
| 旧固定 `±1.025pp` / 新硬边界命中 | `106 → 2` | `106 → 0` |
| 硬边界最长连续命中 | `5 → 2` | `4 → 0` |
| 最大非零斜率重复率 | — → `4/2400` | — → `4/2400` |

测量残差没有被伪装成应为零的误差：最终最大绝对残差为调参集 `4.4202pp`、留出集 `3.9377pp`，Viewer 和正式文档均公开两种口径及其残差。留出集只在候选冻结后运行一次，没有据此回调参数。

#### 3.9 本地合入与最终验收（2026-07-22）

GPT Pro 交付补丁经校验后合入当前工作区；本地额外增加了 stress 通道围绕锚点方向对称、输出缺口反馈不再直接重复注入增长/HY 的契约测试。最终验收结果如下：

- Python 3.13 完整测试 `438/438` 通过；Goal 3 定向测试 `10/10` 通过；
- 59 份配置、13 个配置族通过 Schema/交叉引用校验，117 份 Markdown 的 758 个本地链接无失效；
- 相关前端 JavaScript 语法检查、JSON 解析和 `git diff --check` 通过；
- 额外盲测 `20263001..20266040` 四组共 160 个未参与调参的 Seed，全部通过宏观反馈收敛契约；四组末十年缺口均值低于 `-2%` 的 Seed 数分别为 `7/4/7/3`，旧 `±1.025pp` 固定斜率平台合计只出现 2 次，没有形成新的高频平台；
- 使用当前活动 Seed `20261943` 重建 60 年真实缓存后，浏览器成功读取 61 行全球数据；GDP 面板可切换，“模型估计缺口”“严格水平缺口”“测量残差”均可见，无 `undefined` 或控制台错误；
- 交付工具没有提供精确 Token 统计，因此成本记录为“不可获得”；本轮只进行一次外部实现交付，本地未重新进行核心公式重写，可视为流程上减少了重复编码，但不填写伪精确节省比例。

当前状态已由本地提交与标签 `v0721c` 固化，尚未推送 GitHub。下一阶段应从子 Goal 4 开始，不再回调本阶段冻结参数，除非后续出现可复现的契约回归。

### 子 Goal 4（已完成）：全球收益率曲线—美元触底修复

#### 4.0 前置条件与预先决策

子 Goal 2 必须完成；若子 Goal 3 改变了 GDP 或 `output_gap_pct` 动力学，也必须先完成并冻结子 Goal 3。否则本阶段校准会建立在继续变化的政策输入上。

本阶段预先采用两项语义决策：

1. `expected_short_rate_10y_pct` 表示未来十年可观察政策短端的平滑预期，其下限原则上不低于名义政策利率下限；
2. QE 的负利率效果另增 `expected_shadow_short_rate_10y_pct`，它可以有限为负，但必须有独立边界、未裁剪目标和进入 2Y/10Y 的显式权重；
3. 当前 `global_dollar_index` 第一版正式定义为“美元资金条件代理”，不是严格 DXY。Viewer 文案应显示“美元资金条件指数”；暂不引入北美相对其它区域的同期反馈，以避免全球—区域循环依赖。

如果执行者发现下游或产品必须把 `global_dollar_index` 当作真实 DXY，停止并报告，不得在本 Goal 临时拼接区域相对利差。

#### 4.1 当前基线

执行者必须复现原 40 Seed、2440 Seed-年份审计：

| 字段 | 触底 Seed | 触底年份 | 最长连续触底 |
|---|---:|---:|---:|
| 全球 2Y | 37/40 | 473 | 26 年 |
| 全球 10Y | 25/40 | 274 | 21 年 |
| 美元指数 | 34/40 | 341 | 16 年 |
| 全球 FCI 下限 `-4` | 28/40 | 218 | 18 年 |

同时记录政策利率、预期短端、影子短端、期限溢价、QE、实际 10Y、曲线斜率、避险压力和风险偏好。调参集使用 `20261001..20261040`，留出集使用 `20262001..20262040`，均为 60 年默认路径；不得只验证现存正式 Seed。

#### 4.2 允许修改范围

核心实现：

- `macro_layers/global_policy_rate_layer_sim.py`
- `macro_layers/global_yield_curve_layer_sim.py`
- `macro_layers/global_dollar_liquidity_layer_sim.py`
- `macro_layers/global_macro_feedback_calibration_sim.py`
- `macro_layers/regional_macro_layer_sim.py`
- `macro_layers/regional_macro_reconciliation_sim.py`
- `macro_layers/macro_run_orchestrator_sim.py`

Viewer 和契约：

- `web/static/js/global-gdp/data-client.js`
- `web/static/js/global-gdp/formatters.js`
- `web/static/js/global-gdp/renderers.js`
- 对应 Schema、Header、Manifest、API fixture、缓存依赖和宏观正式文档

建议新增 `tests/test_global_yield_dollar_contract.py`，并扩展收敛、区域对账、长期路径和固定 Seed 测试。本 Goal 不修改贷款定价，也不把 `input_policy_rate_pct` 贯通城市层；该工作属于子 Goal 6。

#### 4.3 不可违反的约束

1. 不通过降低收益率下限或美元下限把平台移到更低位置。
2. 不移除所有边界；极端异常仍需要硬安全范围。
3. 不让同一 QE/宽松信号以高度相关形式在预期短端、期限溢价、10Y 和美元中重复全额计价。
4. 不把美元资金条件代理描述为美国对贸易伙伴的真实汇率指数。
5. 不引入全球层读取同年区域结果的循环依赖。
6. 不破坏 `real_10y = 10y - inflation_expectation`、`term_spread = 10y - 2y` 等恒等式。
7. 不靠 40 个已知 Seed 的硬编码、分段特判或事件识别表调参。
8. 不在本 Goal 修改输出缺口、增长限制、信用、资产、油价或贷款的内部系数。
9. 子 Goal 2 的收敛契约必须在每次候选校准后重跑；不能用不收敛路径统计触底率。

#### 4.4 必须新增的未裁剪诊断

至少发布：

```text
unclamped_short_rate_target_pct
unclamped_expected_short_rate_10y_target_pct
unclamped_expected_shadow_short_rate_10y_target_pct
unclamped_2y_yield_target_pct
unclamped_10y_yield_target_pct
unclamped_term_premium_target_pct
unclamped_dollar_target_index
unclamped_financial_conditions_target_index
short_rate_floor_applied / cap_applied
expected_short_rate_floor_applied / cap_applied
shadow_short_rate_floor_applied / cap_applied
yield_2y_floor_applied / cap_applied
yield_10y_floor_applied / cap_applied
dollar_floor_applied / cap_applied
financial_conditions_floor_applied / cap_applied
*_consecutive_boundary_years
```

诊断值必须是裁剪前公式真实目标，不能在裁剪之后反推。每个字段的边界和语义应来自版本化参数，而不是散落常数。

#### 4.5 分阶段执行

##### 阶段 A：只增加观测，不改变路径

先把未裁剪目标、边界命中和连续命中诊断加入现有路径。证明新增字段外的固定 Seed 数值不变，随后复现调参集与留出集的边界统计。

##### 阶段 B：建立渠道消融报告

用影子计算或测试辅助逐项关闭以下渠道，比较 2Y、10Y、美元和 FCI 的方向及幅度：

- QE 对可观察短端预期；
- QE 对影子短端；
- QE 对期限溢价；
- 政策立场与实际利率；
- output gap 与增长预期；
- 曲线形态对美元条件；
- 避险压力；
- 风险偏好和流动性。

报告必须识别重复计价链，而不只是给出相关系数。禁止把消融开关永久留在正式运行路径。

##### 阶段 C：拆分可观察与影子短端

实现两种状态和各自边界。2Y 应主要锚定可观察短端；10Y 可以有限吸收影子短端与期限溢价，但权重必须显式、方向测试充分。QE 退出时影子短端应平滑回归可观察预期，不能永久留在负区间。

##### 阶段 D：重新校准 2Y、10Y、美元和 FCI

每次只修改一个渠道集并生成前后差异。优先减少重复放大和改善均值回归，再考虑边界宽度。美元代理应主要反映全球美元资金松紧、实际利率、避险和流动性，Viewer 与文档不得继续写成严格 DXY。

##### 阶段 E：区域传播与反向检查

重新生成 14 区政策和 10Y，检查：

- 区域政策与 10Y 裁剪数量；
- 对账前后软残差；
- 低利率、倒挂、危机和复苏方向；
- 中国区域宏观与航空输入的幅度；
- 未来贷款基准需要的字段是否稳定，但不在此阶段改贷款。

##### 阶段 F：版本、Viewer 与完整回归

统一参数版本、接口版本、Schema、字段清单和 Viewer 标签。对旧 `global_dollar_index` 字段是否保留名称必须形成唯一决定；若暂时保留字段名，正式文档和界面必须明确其代理身份，不能同时新增第二套同义数据。

#### 4.6 方向性测试矩阵

| 场景 | 必须满足的方向 |
|---|---|
| 正常扩张、无 QE | 2Y 跟随政策，10Y 由预期短端与期限溢价共同决定 |
| 降息周期 | 2Y 通常先下行，10Y 下行幅度不机械复制 2Y |
| 曲线倒挂 | `2Y > 10Y` 合法，恒等式仍成立 |
| QE 启动 | 影子短端与期限溢价下行，但可观察政策预期不越过其语义下限 |
| QE 退出 | 影子短端回归，长端不出现一次性跳变 |
| 通胀冲击 | 长端和期限溢价方向合理，不被宽松项完全吞掉 |
| 危机避险 | 美元资金条件代理偏强、风险压力偏紧 |
| 流动性修复 | 美元条件和 FCI 从极端状态平滑退出 |

#### 4.7 验收标准

- 调参集与留出集各 40 Seed、60 年均通过子 Goal 2 收敛；
- 2Y、10Y、美元代理和 FCI 在两个集合中的精确贴边行数分别低于 `1%`；
- 默认路径中任何单次连续贴边不超过 2 年；极端 scenario 可以更长，但必须有未裁剪目标和显式状态；
- 可观察短端预期不无说明地低于名义政策下限；影子短端的负值范围、持续时间和退出均有测试；
- 所有收益率恒等式逐行成立；
- 方向性矩阵全部通过；
- 区域政策与 10Y 不出现新的大规模裁剪簇，GDP 守恒和软对账诊断保持有效；
- Viewer 不再把代理字段描述为严格美元指数；
- 固定 Seed 差异报告能把变化归因到具体渠道；
- 定向测试、跨进程确定性和完整 Python 3.13 测试通过。

#### 4.8 停止条件

以下情况停止：必须引入同年区域相对数据才能定义美元；收益率触底只能通过修改 GDP/输出缺口解决；子 Goal 2 再次不收敛；影子短端身份无法被现有下游接受；或留出集出现调参集没有的大规模新边界簇。

#### 4.9 实施记录（2026-07-22）

本阶段在 `v0721c` 基线上完成。先只增加 33 个诊断字段并对三个固定 Seed 证明原有 227 个字段除版本字符串外逐值不变；随后使用 tuning Seed `20261001..20261040` 完成渠道消融并冻结唯一候选，候选冻结后只运行一次 holdout `20262001..20262040`。

根因是 QE/宽松信号在当前短端、可观察短端预期、2Y、10Y、期限溢价、曲线美元 impulse、美元目标和 FCI 中多次相关计价。完成版拆分可观察与影子短端，2Y 仅有限读取影子差，10Y 通过显式影子权重和期限溢价吸收 QE；美元曲线 impulse 只保留曲线形态，FCI 的宽松方向由流动性状态表达。未修改 GDP/缺口、信用、资产、能源、机场经营、贷款或 `year_index=0` 语义。

最终 tuning/holdout 均为 `40/40` 收敛。2Y 精确边界分别为 `2/2440`（最长 2 年）和 `1/2440`（最长 1 年）；10Y、美元资金条件代理和 FCI 在两组均为零贴边。正式字段契约升级为 `airport-model-output-v3`，Viewer 明确使用“美元资金条件指数/代理”。完整测试与区域结果以本阶段 `CHANGE_REPORT.md` 和 `RESULT_METRICS.json` 为准。

#### 4.10 本地合入与最终验收（2026-07-22）

GPT Pro 交付包经路径安全、SHA-256 清单和补丁一致性检查后合入当前工作区；21 份候选文件与交付内容一致。本地额外补充持续 QE 退出后的影子/可观察短端缺口收敛测试，避免只验证单年或固定样例。

- Python 3.13 完整测试 `449/449` 通过，收益率—美元定向测试 `11/11` 通过；
- 59 份配置、13 个配置族通过 Schema/交叉引用校验，281 份 Markdown 的 1770 个本地链接无失效；相关前端 JavaScript 语法检查和 `git diff --check` 通过；
- 额外盲测 `20270001..20270040` 共 40 个未参与调参的 Seed，全部收敛；2440 行中 2Y、10Y、美元资金条件代理和 FCI 均为零贴边，可观察短端没有跌破其下界，影子短端保留了 6 行负值；
- 使用活动 Seed `20261106` 重建 60 年真实缓存后，浏览器成功读取 61 行数据；10Y 面板同时显示“可观察短端预期”“影子短端预期”和“美元资金曲线冲击”，没有 `undefined` 或页面错误；
- 外部交付工具仍不提供精确 Token 数。本轮按任务规模、21 文件实现量和本地剩余审查量估算，相比完全由本地 Codex 从诊断、实现到校准独立完成，约节省 `3.5万—5.5万` 本地模型 Token，节省比例约 `50%—65%`；该数字是区间估算，不是计费记录。

当前改动尚未提交或打新标签；若后续建立 `v0721d`，应先保留本段验收结果并从子 Goal 5 继续，不再回调本阶段冻结参数，除非出现可复现的契约回归。

建议入口提示词：严格执行通用协议和子 Goal 4 的 4.0–4.8；不要进入次级饱和或贷款；完成后按 2.10 报告。

### 子 Goal 5（待实施）：次级饱和与 `year_index=0` 统一

#### 5.0 前置条件和范围拆分

子 Goal 2–4 必须完成并冻结。该 Goal 内部按两个不可颠倒的检查点执行：

- **5A：次级饱和诊断与最小修复**；
- **5B：所有全球层的统一起点语义**。

5A 与 5B 可以在同一工作会话完成，但必须分别生成差异报告，不能把“边界修复”和“随机序列因起点变化而整体平移”混在一张 baseline 更新里。

本阶段预先决定：`year_index=0` 是真正的配置起点。所有全球层在第 0 行输出配置初值和中性/初始诊断，不执行年度状态转移；第一次随机冲击和第一次状态更新发生在 `year_index=1`。

#### 5.1 当前基线

执行者先复现 40 Seed 次级饱和统计：

| 字段与边界 | 命中 Seed | 命中年份 | 最长连续命中 |
|---|---:|---:|---:|
| 股票风险溢价上限 `12%` | 28/40 | 265 | 17 年 |
| 能源成本压力上限 `100` | 28/40 | 172 | 9 年 |
| 全球信用利差指数上限 `100` | 16/40 | 136 | 16 年 |
| 信贷可得性下限 `0` | 11/40 | 54 | 11 年 |
| 信用减值存量上限 `100` | 7/40 | 34 | 11 年 |
| 股票盈利指数上限 `460` | 4/40 | 18 | 7 年 |
| Brent 下限 `18 USD` | 4/40 | 13 | 4 年 |

同时复现第 0 行不一致：GDP 实际与潜在指数为 `100`、政策率为配置初值，但 10Y、美元、HY、盈利和部分商品状态已经发生一次带 Seed 的更新。

调参集和留出集沿用前两个 Goal 的各 40 Seed。5A 使用 60 年完整路径；5B 还必须对 `years=0`、`1`、`2` 做微型测试，确保起点与第一次转移清楚。

#### 5.2 边界分类与预定处理原则

| 类型 | 示例 | 默认处理 |
|---|---|---|
| 物理/契约指数 | 能源压力、信用可得性等 `0–100` | 保留硬边界，增加未裁剪目标、命中与持续时间；先重标内部压力或修复速度 |
| 风险刻度 | 股票风险溢价、信用利差严重度 | 优先软饱和，保留极端排序；外层仍有异常安全边界 |
| 价格水平 | Brent | 保留可解释价格下限，避免长期粘在下限；修复目标和均值回归 |
| 长期增长水平指数 | 盈利指数等 | 不使用固定常数上限限制 60 年增长；改为无固定上限或随趋势变化的安全约束 |

执行者不得把所有字段统一替换成同一个 `tanh`，也不得仅把上限乘二。每类边界需要不同解释和测试。

#### 5.3 允许修改范围

5A 核心文件：

- `macro_layers/global_credit_spread_layer_sim.py`
- `macro_layers/global_asset_price_layer_sim.py`
- `macro_layers/global_oil_commodity_layer_sim.py`
- 必要时 `global_dollar_liquidity_layer_sim.py` 和 `global_macro_feedback_calibration_sim.py`，但只处理这些字段的反馈接口

5B 核心文件：

- `macro_layers/global_gdp_annual_sim.py`
- `macro_layers/global_inflation_annual_sim.py`
- `macro_layers/global_policy_rate_layer_sim.py`
- `macro_layers/global_yield_curve_layer_sim.py`
- `macro_layers/global_dollar_liquidity_layer_sim.py`
- `macro_layers/global_credit_spread_layer_sim.py`
- `macro_layers/global_asset_price_layer_sim.py`
- `macro_layers/global_oil_commodity_layer_sim.py`
- `macro_layers/global_macro_feedback_calibration_sim.py`

还需更新编排、字段清单、Viewer 起点展示、Schema、fixture 和正式文档。建议新增 `tests/test_global_boundary_and_initial_state_contract.py`。不修改区域、航空、经营或贷款内部公式；它们只接受新的全球路径。

#### 5.4 不可违反的约束

1. 不取消物理/契约边界。
2. 不让软饱和失去严重程度排序，例如两个远超上限的危机仍输出完全相同值。
3. 不用随时间增长的上限去约束本来就应固定为 `0–100` 的指数。
4. 不为消除贴边而降低危机冲击本身，除非消融证明同一压力被重复计价。
5. `year_index=0` 不消费随机数、不更新状态、不应用年度冲击、不运行危机阶段转移。
6. 第 0 行不是全字段强制为零；利率、价格和指数应输出各自配置初值，中性流量/变化字段才为零。
7. 不通过在第 0 行运行旧逻辑后再覆盖输出值伪造起点；内部 state 也必须仍是初始状态。
8. 起点修复会改变之后的随机消费顺序时，必须明确选择并记录。推荐从第 1 行才开始消费该层随机数，不保留“为了旧 digest 偷跑一次 RNG”的兼容动作。
9. 不把 5A 与 5B 的版本和差异说明混成无法归因的一次 baseline 刷新。

#### 5.5 必须新增的边界诊断

每个目标字段使用一致命名语义：

```text
unclamped_<field>_target
<field>_floor_applied
<field>_cap_applied
<field>_boundary_state       # none / floor / cap / soft_floor / soft_cap
<field>_consecutive_boundary_years
```

至少覆盖：

- `equity_risk_premium_pct`
- `energy_cost_pressure_index`
- `global_credit_spread_index`
- `credit_availability_index`
- `credit_impairment_stock_index`
- `equity_earnings_index`
- `brent_oil_price_usd`

诊断字段可以按模块前缀微调，但 Schema、文档和 Viewer 必须一一对应，不能同一概念出现三种名称。

#### 5.6 5A 执行流程

##### 阶段 A：只加诊断

新增未裁剪目标与命中状态，证明原数值路径不变。对调参集和留出集报告命中率、连续长度、未裁剪目标超界幅度和相关上游压力。

##### 阶段 B：逐类修复

依次处理信用、资产、能源三个模块，每次只处理一类：

1. 判断是尺度设计、均值回归、修复速度、长期趋势还是重复压力造成；
2. 先修内部目标动力学，再决定硬边界或软饱和；
3. 运行子 Goal 2 收敛和前四层回归；
4. 输出该类字段的前后分布，再进入下一类。

##### 阶段 C：严重程度与场景检查

构造普通、严重、灾难三级压力，验证指标保持严格或至少非退化排序；极端场景允许命中外层硬边界，但必须保留未裁剪目标用于区分强度。

#### 5.7 5B 执行流程

##### 阶段 D：定义统一初始行构造器

每个全球层应有明确的初始行路径，直接从配置和上游第 0 行构造，不调用普通年度转移。初始行至少满足：

- `year_index=0`、`year=start_year`；
- stock/level 等于参数初值；
- change/yoy/flow 为零或明确的基期定义；
- event/scenario phase 为 initial/none；
- floor/cap applied 为 false，除非配置初值本身非法，此时应在参数校验阶段失败；
- 不消费 RNG。

##### 阶段 E：验证第一次年度转移

`year_index=1` 必须从第 0 行 state 开始，消费第一次随机数并执行一次完整更新。使用 `years=0/1/2` 测试证明没有漏更或双更。

##### 阶段 F：跨层、Viewer 与下游

验证全球八层第 0 行语义一致，区域第 0 行读取同一组初值，Viewer 时间轴将其显示为“起点”而不是“第一年结果”。初始贷款报价最终应读取这组起点值，但具体贷款字段贯通留给子 Goal 6。

#### 5.8 验收标准

- 调参集与留出集各 40 Seed、60 年全部满足子 Goal 2 收敛；
- 非结构性风险指标在默认路径的精确硬边界命中率低于 `2%`，单次连续命中不超过 3 年；
- 极端场景命中边界时保留严重程度排序或未裁剪强度；
- 60 年增长水平指数不再被固定常数上限截平；
- `year_index=0` 在八个全球层均为真实配置起点，不消费随机数、不执行年度转移；
- `years=0` 只产生一个起点，`years=1` 只产生一次转移；
- 不同 `PYTHONHASHSEED` 进程的规范化结果一致；
- Viewer、区域起点和未来贷款起点读取同一宏观状态；
- 5A 与 5B 各有独立差异报告和版本说明；
- 固定 Seed、长期路径、scenario、区域守恒及完整 Python 3.13 测试通过。

#### 5.9 停止条件

以下情况停止：次级饱和只能通过重写信用/能源经济机制解决；统一起点需要改变 `start_year` 或年份数量公共契约；某层无法在不消费 RNG 的情况下构造初始行；子 Goal 2 收敛回归；或下游把第 0 行明确当成第一年结束且无法在本范围统一。

建议入口提示词：严格执行通用协议和子 Goal 5 的 5.0–5.9；按 5A、5B 分别报告；不要进入贷款实现；完成后按 2.10 报告。

### 子 Goal 6（待实施）：贷款利率 v0.3——短端与长端基准分离

#### 6.0 前置条件、当前基线与权威决策

子 Goal 1、2、4 必须完成；子 Goal 3 若改变 GDP 路径也必须完成。子 Goal 5 的 `year_index=0` 统一必须在首个正式贷款 v0.3 发布前完成，避免初始报价使用混合起点。

执行者先复现当前事实：

- 所有自动贷款统一读取 `input_10y_yield_pct`；
- 短期产品只靠 `short_term_reference_adjustment_pct` 模拟短端差异；
- 城市年度、季度经营和北京经营 API 尚未贯通 `input_policy_rate_pct`；
- Python 在提款时锁定最终利率，JavaScript 在浏览器中另算候选报价；
- 前端把 `macroTenYearYieldPct <= 0` 当作缺失，会错误丢弃合法的零或负宏观基准；
- 当前 UI 只突出最终报价、期限/宽限和杠杆，不能完整解释基准、产品、信用与边界。

本阶段预先决定：

1. 短期周转贷款使用同年、同季度上下文中的**区域对账后政策利率**；
2. 长期和宽限期建设贷款使用**区域对账后 10 年期收益率**；
3. 两种基准必须来自同一个 regional reconciled 权威链，不能一端读 raw、一端读 reconciled；
4. Python 的纯函数报价分解是最终权威，提款后保存锁定利率和锁定时分解；
5. 浏览器可以为交互即时计算候选报价，但必须消费服务端提供的同一输入和参数，并通过共享测试向量验证；真实提款结果始终以服务端为准；
6. 本 Goal 不新增违约、浮息、再融资、提前还款或银行审批概率。

#### 6.1 权威基准选择

| 产品 | 基准 | 保持不变的部分 |
|---|---|---|
| 短期周转贷款 | 当季对应年度的区域政策利率 | 产品、期限、信用、杠杆利差；1%–9.5%；提款时锁定 |
| 长期建设贷款 | 当季对应年度的区域 10 年期收益率 | 同上 |
| 宽限期建设贷款 | 当季对应年度的区域 10 年期收益率 | 同上，另保留宽限利差 |

第一版不借机切换长期贷款目前使用的 10 年期字段权威来源。短期政策利率应沿与现有 10 年期字段相同的区域宏观路径传递，避免短端读 reconciled、长端读 raw 等隐藏口径分裂；若要统一 raw/reconciled 权威来源，应另列为宏观接口变更并单独比较结果。

负值和零值的处理必须明确：

- `0%` 或负政策利率是可能存在的有效宏观输入，不能仅因 `<= 0` 就触发回退；
- 只有字段缺失、空值、非有限数值或来源身份不匹配时才使用产品回退利率；
- 最终贷款报价仍由 `1.0%` 下限保护。

#### 6.2 补齐政策利率字段链

需要沿以下路径增加并验证 `input_policy_rate_pct`：

```text
regional_macro_layer_sim.py
  regional_policy_rate_pct
    -> city_airport_market_demand_layer_sim.py
       input_policy_rate_pct
    -> city_airport_quarterly_operations_layer_sim.py
       input_policy_rate_pct
    -> city_airport_financial_state_layer_sim.py
       短期贷款基准
    -> airport_sim/server/beijing_operations.py
       macroPolicyRatePct
    -> web/static/js/seed-explorer/operations-actions.js
       短期报价展示
```

同时更新：

- CSV/JSON 字段顺序和接口版本；
- 季度经营参数模板；
- 北京经营 API 映射；
- 缓存指纹或任何显式字段清单；
- 固定 Seed Header/Semantic Digest；
- 正式模型和参数文档。

#### 6.3 统一贷款报价分解

服务端应把贷款报价从“只返回最终浮点数”提升为可测试的报价分解对象。建议字段：

```text
benchmark_type
benchmark_rate_pct
benchmark_fallback_used
product_spread_bps
term_and_grace_spread_bps
credit_spread_bps
leverage_spread_bps
unclamped_annual_rate_pct
annual_rate_pct
rate_floor_applied
rate_cap_applied
```

展示口径：

```text
基准利率
+ 产品利差
+ 期限 / 宽限利差
+ 信用利差
+ 杠杆利差
= 未裁剪报价
-> 1.0%–9.5% 边界
= 提款锁定年利率
```

现有 `short_term_reference_adjustment_pct`、`long_term_reference_adjustment_pct`、产品类型利差和城市风险利差应合并计入“产品利差”，但服务端内部仍可保留各自配置来源。界面不能漏项，也不能让前端与服务端各自形成不同公式。

如果前端继续本地计算候选报价，必须使用与 Python 相同的测试向量验证每个组成项和最终裁剪结果。最终提款利率仍以服务端锁定结果为权威。

#### 6.4 界面变更

融资事务区应：

1. 把“统一使用 10 年利率”改成短期政策利率、长期 10 年期利率的明确说明。
2. 三种产品在同一季度、同一融资额和同一提款后负债率假设下可横向比较。
3. 每张报价卡展示五个组成部分及最终锁定利率。
4. 触及利率下限或上限时明确显示“已应用 1% 下限”或“已应用 9.5% 上限”。
5. 宏观收益率曲线倒挂时，不把“短期总报价高于长期”误报为错误；解释基准和产品利差共同决定结果。
6. 回退发生时显示所用回退基准，不能静默伪装成真实宏观报价。

#### 6.5 必要测试

至少增加以下测试：

1. **同季度产品横向比较**：三个产品使用相同季度和杠杆上下文，各自选中正确基准与产品利差。
2. **正常收益率曲线**：政策利率低于 10 年期时，短期读取政策、长期读取 10 年期。
3. **收益率曲线倒挂**：政策利率高于 10 年期时，基准选择不互换；最终报价按真实组成计算。
4. **零或负政策利率**：视为有效短端基准，最后由贷款利率下限裁剪。
5. **缺失短端基准**：短期仅回退到 `fallback_short_term_rate_pct`。
6. **缺失长端基准**：长期和宽限产品仅回退到 `fallback_long_term_rate_pct`。
7. **提款锁定**：后续政策利率、10 年期利率或 HY 利差变化，不改变已提款贷款利率。
8. **组成项守恒**：未裁剪报价等于五项之和，最终报价等于上下限裁剪结果。
9. **前后端一致性**：同一组输入的 Python 锁定报价与浏览器候选报价一致。
10. **旧产品契约**：期限、还本方式、宽限期、金额范围、每季一笔和 80% 拒绝线保持不变。

#### 6.6 允许修改范围与字段清单

宏观到城市字段链：

- `macro_layers/regional_macro_layer_sim.py`
- `macro_layers/regional_macro_reconciliation_sim.py`
- `macro_layers/city_airport_market_demand_layer_sim.py`
- `macro_layers/city_airport_quarterly_operations_layer_sim.py`
- `macro_layers/macro_run_orchestrator_sim.py` 及必要的 variant/output 字段清单

融资权威实现与配置：

- `macro_layers/city_airport_financial_state_layer_sim.py`
- `config/city_airport_finance/beijing_airport_group_financial_state_v1.json`
- `schemas/city-airport-financial-state-config.schema.json`
- 季度经营模板和中国 reference defaults 中的输入字段清单

API 与前端：

- `airport_sim/server/beijing_operations.py`
- 必要的 API envelope/schema/fixture
- `web/static/js/seed-explorer/operations-actions.js`
- 对应融资事务区 HTML/CSS 或浏览器测试文件，仅在展示确有需要时修改

文档与测试：

- `docs/models/Finance_Contracts_and_Projects.md`
- `docs/reference/Finance_and_Valuation_Parameters.md`
- `docs/reference/API_and_Data_Contracts.md`
- 建议新增 `tests/test_loan_rate_v03_contract.py`
- 扩展季度经营、服务端 API、固定 Seed、长期路径和前端语法/浏览器测试

超出清单的估值、现金流、项目、合同和玩家存档逻辑默认不修改。

新增字段至少包括：

```text
input_policy_rate_pct
input_policy_rate_source
input_10y_yield_source
```

最终 API 至少提供：

```text
macroPolicyRatePct
macroTenYearYieldPct
```

字段来源必须可追踪到同一年度的区域对账后记录。季度值沿当前年度到季度的既有映射传递，不在本 Goal 发明月度或季度宏观插值。

#### 6.7 Python 权威报价对象

把当前只返回一个浮点数的 `loan_interest_rate_pct()` 重构为无副作用的报价函数，例如 `build_loan_rate_quote()`。最终名称可按项目风格调整，但返回结构必须包含：

```text
loan_type
benchmark_type                  # policy_rate / ten_year_yield
benchmark_source
benchmark_rate_pct
benchmark_fallback_used
benchmark_fallback_reason
product_reference_adjustment_bps
product_type_spread_bps
product_spread_bps
term_spread_bps
grace_spread_bps
term_and_grace_spread_bps
hy_credit_spread_bps
city_credit_spread_bps
credit_spread_bps
leverage_spread_bps
unclamped_annual_rate_pct
annual_rate_pct
rate_floor_applied
rate_cap_applied
rate_model_version
```

守恒公式：

```text
product_spread_bps
  = product_reference_adjustment_bps
  + product_type_spread_bps

term_and_grace_spread_bps
  = term_spread_bps
  + grace_spread_bps

credit_spread_bps
  = hy_credit_spread_bps
  + city_credit_spread_bps

unclamped_annual_rate_pct
  = benchmark_rate_pct
  + product_spread_bps / 100
  + term_and_grace_spread_bps / 100
  + credit_spread_bps / 100
  + leverage_spread_bps / 100

annual_rate_pct
  = clamp(unclamped_annual_rate_pct, 1.0, 9.5)
```

任何现有配置分项都必须映射到上述唯一类别，不能漏算，也不能在两个类别重复计入。手工指定 `annual_interest_rate_pct` 的旧静态贷款继续作为显式覆盖，但要返回 `benchmark_type=manual_override` 和可解释分解，不能绕过对象契约。

提款时应在 loan state 保存至少最终锁定利率、benchmark type/rate、各聚合 spread 和模型版本。后续宏观变化不得重新计算存量贷款。

#### 6.8 缺失、零值、负值与边界语义

合法基准：

- `0.0`；
- 有限负数；
- 有限正数；
- 明确来源为目标年度 regional reconciled 字段。

仅以下情况触发回退：

- 字段不存在；
- `null`、空字符串；
- `NaN` 或无穷；
- 来源类型或年度上下文不匹配。

回退必须按产品隔离：短期只用 `fallback_short_term_rate_pct`，长期和宽限只用 `fallback_long_term_rate_pct`。回退原因进入报价对象和界面；不能把 `<=0`、Python truthiness 或 JavaScript `||` 当作缺失判断。

最终 `1%–9.5%` 边界不改变宏观基准本身。负政策利率可以在分解中显示为负基准，最后由贷款总报价下限保护。

#### 6.9 不可违反的约束

1. 不改变三种贷款的期限、还本方式、宽限规则、金额范围、每季一笔和 80% 拒绝线。
2. 不改变 HY 捕获、城市信用、杠杆曲线和已有产品 spread 的经济含义，除非只是无损拆分命名。
3. 不把短期与长期基准互换来保证某种固定报价排序；曲线倒挂时短期总价可以高于长期。
4. 不在前端和 Python 各自发明不同的 fallback、舍入或边界顺序。
5. 不用默认值掩盖跨层字段遗漏；缺失测试必须能够主动触发回退并显示原因。
6. 不重定价已提款贷款，不根据后来宏观数据刷新锁定分解。
7. 不把候选报价误写进正式存档；只有确认提款后才形成 loan state。
8. 不修改估值折现率、自由现金流、净现金流或其它财务报表公式。
9. 不引入兼容旧 `input_10y_yield_pct` 作为短期静默备用链；正式 v0.3 短期基准缺失时只能显式 fallback。

#### 6.10 分阶段执行

##### 阶段 A：贯通字段但不改贷款公式

把 `input_policy_rate_pct` 和来源从 regional reconciled 传到城市年度、季度经营和北京 API。先证明除新增字段外，经营、财务、估值和固定 Seed 数值不变。验证 60 年、所有季度均有正确年度映射。

##### 阶段 B：建立 Python 报价对象

先为当前长期逻辑建立等价报价分解，证明最终利率逐样例不变；再让短期选择政策基准。把提款锁定从“保存一个 rate”扩展为保存必要分解和版本。

##### 阶段 C：配置与 Schema 统一

明确每个旧配置字段属于 product、term/grace、credit 或 leverage 哪一项。更新配置 design note、Schema required 字段和范围校验。禁止同时保留两套同义参数。

##### 阶段 D：API 与前端候选报价

API 提供当前季度两个宏观基准、来源、产品参数和已锁定贷款分解。JavaScript 候选报价必须：

- 使用 `Number.isFinite` 判断基准；
- 选择正确产品基准；
- 与 Python 相同的单位、相加顺序、边界顺序；
- 展示基准、产品、期限/宽限、信用、杠杆、未裁剪与最终报价；
- 显示 fallback、下限和上限状态。

构建一组 JSON 共享测试向量，由 Python 和 JavaScript 分别执行并比较；若当前测试设施不便直接调用浏览器函数，至少把报价逻辑提取为无 DOM 依赖纯函数并用 Node 运行。

##### 阶段 E：真实提款和锁定验证

在同一季度分别测试三个产品，随后推进季度并改变宏观利率/HY/杠杆，确认：

- 新贷款使用新季度报价；
- 旧贷款仍使用提款时利率；
- 还本、利息和现金流不因新增分解字段改变；
- 存档重载后锁定利率和分解保持一致。

##### 阶段 F：版本、文档和浏览器验收

统一参数、输出、API 和前端版本；更新正式融资文档、字段表、配置说明、fixture 和 digest。真实浏览器检查正常曲线、倒挂、负政策率、回退、上下限以及三个产品的横向比较。

#### 6.11 验收矩阵

| 场景 | 短期 | 长期 | 宽限期 |
|---|---|---|---|
| 正常曲线 | 区域政策率 | 区域 10Y | 区域 10Y |
| 曲线倒挂 | 仍读政策率 | 仍读 10Y | 仍读 10Y |
| 政策率为 0/负数 | 合法输入，最后裁剪总价 | 不受影响 | 不受影响 |
| 缺失政策率 | 仅短期 fallback | 不受影响 | 不受影响 |
| 缺失 10Y | 不受影响 | 长期 fallback | 长期 fallback |
| HY 上升 | 信用分项上升 | 信用分项上升 | 信用分项上升 |
| 杠杆上升 | 杠杆分项上升或触发拒绝 | 同左 | 同左 |
| 后续宏观变化 | 已提款利率不变 | 已提款利率不变 | 已提款利率不变 |

所有场景都必须验证分项守恒、最终边界、API 字段和浏览器文案。

#### 6.12 完成标准与停止条件

只有以下条件全部满足，才能报告贷款 v0.3 完成：

- `input_policy_rate_pct` 从区域对账后记录贯通到季度经营和 API；
- 三种产品选择正确基准，零/负值不被误判为缺失；
- Python 权威报价对象字段完整且分项守恒；
- 浏览器候选报价通过共享向量，与 Python 最终结果一致；
- 提款锁定、存档重载、还本和现金流回归通过；
- 曲线倒挂、分别缺失、fallback、上下限和拒绝线均有测试；
- API、Schema、配置、缓存指纹、fixture、正式文档和版本一致；
- 前端 JS 语法检查、定向 Python 测试、完整 Python 3.13 测试和真实浏览器验收通过；
- 没有引入阶段外玩法或兼容性静默回退。

以下情况停止：区域政策率权威来源不唯一；需要改变贷款产品经济参数；玩家存档无法保存锁定分解且会破坏现有存档；前端无法复用或验证权威公式；或宏观 v0.3 基准本身仍未通过前序 Goal。

难度：中—高。规划已明确，适合强执行编码模型；主要风险是跨层字段遗漏、前后端公式漂移和锁定状态回归。

建议入口提示词：严格执行通用协议和子 Goal 6 的 6.0–6.12；不要增加违约、浮息、再融资或估值功能；完成后按 2.10 报告。

## 明确不在本阶段做

- 违约、破产和强制处置；
- 提前还款；
- 浮动利率和定期重定价；
- 再融资或贷款展期；
- 银行竞价、授信额度和贷款审批概率；
- 贷款与具体建设项目强绑定；
- 改变现有产品期限、还本方式、金额范围和每季一笔限制；
- 改变 HY 信用压力公式、杠杆加点曲线、80% 拒绝线或 1%–9.5% 利率边界；
- 借贷款子 Goal 全面重做全球政策利率、收益率曲线、美元或区域利率模型；这些变化必须在各自宏观 Goal 中单独完成；
- 把输出缺口公式修改混入贷款提交。

## 建议任务矩阵

| 顺序 | 任务集群 | 难度 | 建议模型水准 | 主要风险 |
|---:|---|---|---|---|
| 1 | 反馈诊断字段保留（已完成） | 低—中 | 较强编码模型 | 情景与宏观反馈合并语义 |
| 2 | 区域对账后边界与诊断（已完成） | 中 | 较强编码模型 | 裁剪后加权残差、下游字段契约 |
| 3 | 反馈迭代收敛契约与发布拒绝线 | 高 | 强执行编码模型 + 最强推理验收 | 非单调迭代、宽松容差、结果依赖 pass 数 |
| 4 | 输出缺口、反馈负偏与增长硬斜率 | 高 | 强执行编码模型 + 最强推理验收 | 政策和增长含义、重复冲击、长期棘轮 |
| 5 | 2Y/10Y/美元/FCI 未裁剪诊断与消融 | 中—高 | 强执行编码模型 + 最强推理验收 | 相关宽松渠道重复计价 |
| 6 | 收益率—美元重新校准与区域回归 | 高 | 强执行编码模型 + 最强推理验收 | 只移动边界、过拟合固定 Seed |
| 7 | 次级饱和与 `year_index=0` 统一 | 中—高 | 强执行编码模型 + 推理验收 | 风险刻度压平、起点契约变化 |
| 8 | 政策利率字段贯通 | 中 | 强执行编码模型 | CSV/API/缓存/Header 字段遗漏 |
| 9 | 服务端贷款报价分解与锁定 | 中 | 强执行编码模型 | 回退、负利率、上下限 |
| 10 | 前端五项报价、横向比较与浏览器验收 | 中 | 强执行编码模型 + 浏览器验收 | 与 Python 公式漂移 |
| 11 | 80 Seed 调参/留出分布、契约和 Release 验收 | 中—高 | 强执行编码模型 + 最强推理验收 | 只验证调参样例而漏掉留出集或未收敛路径 |

整组若一次完成属于高难度，并且无法解释数值来源；按六个子 Goal 执行则每一步都可审查和回退。

## 完成标准

只有以下条件全部满足，整个阶段 Goal 才算完成：

- 宏观反馈强度和 raw 诊断不再被编排器清零；
- 区域对账后字段遵守公开边界，诊断记录裁剪后的真实残差；
- 调参集和留出集共 80 个固定 Seed 满足版本化反馈收敛契约，未收敛 Run 不会成为活动 Release；
- 输出缺口有唯一、明确、可测试的经济口径；
- 增长变化硬斜率不再主导默认路径，反馈支持与拖累不存在未经解释的长期单向棘轮；
- 2Y、10Y、美元和 FCI 的默认路径不再长时间贴边，极端情景触边有未裁剪目标和显式状态；
- 美元字段究竟是相对美元指数还是美元资金条件代理已有唯一、正式定义；
- 股票风险溢价、能源、信用和长期水平指数的饱和已有诊断和处理决定；
- `year_index=0` 在所有全球层使用一致的起点语义；
- 短期贷款只使用区域政策利率，长期和宽限贷款只使用区域 10 年期收益率；
- 缺失基准、负政策利率、曲线倒挂和提款锁定均有测试；
- 报价界面展示五项组成、回退和上下限状态；
- Python 3.13 完整测试通过，固定 Seed 的预期变化有差异说明；
- 真实浏览器验证短期、长期、宽限期三种报价及实际提款；
- API、Schema、配置、缓存指纹和正式文档同步；
- 提交记录把收敛、输出缺口、收益率—美元、次级饱和和贷款 v0.3 分开说明；
- 最终删除本临时文档，并由 `Roadmap.md` 和正式专题文档保存剩余事实。
