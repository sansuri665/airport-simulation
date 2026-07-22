# API 与数据契约

## 1. 范围

8776 本地服务使用 JSON API 连接网页、模型、缓存和玩家存档。`schemas/` 中的 JSON Schema 2020-12 用于固定必需字段、类型、协议版本和基础约束；Schema 不定义模型公式，也不会替代固定 Seed 数值回归。

正式装配、路由与协议目录：

```text
airport_sim/server/app.py
airport_sim/server/routes.py
airport_sim/server/api_contract.py
```

`routes.route_contract()` 是 HTTP 方法、公开路径、响应类型和缓存层级的机器可读清单；`api_contract.py` 是 Schema 文件及关键端点映射的权威来源。`app.py` 暂时继续兼容暴露原函数和 Handler 名称。

Schema 目录：

```text
http://127.0.0.1:8776/api/schema
```

单个 Schema：

```text
http://127.0.0.1:8776/schemas/seed-explorer-run-response.schema.json
```

## 2. 公共响应元数据

JSON 响应会附加当前协议与运行环境：

```json
{
  "apiSchemaVersion": "seed-explorer-api-v3",
  "modelVersion": "airport-model-v0.12",
  "outputSchemaVersion": "airport-model-output-v4",
  "pythonVersion": "3.13.x",
  "schemaCatalog": "/api/schema"
}
```

统一版本记录位于 `config/airport_versions.json`。这些字段用于判断页面、缓存和结果是否来自同一套协议，不应由前端写死为另一套值。

## 3. GET 接口

| 接口 | 作用 | 专用 Schema |
|---|---|---|
| `GET /api/health` | 服务身份、PID、缓存/存档根与指纹版本 | `health-response.schema.json` |
| `GET /api/workspace-status` | 当前 Viewer 发布、缓存与存档数量、页面地址 | `workspace-status-response.schema.json` |
| `GET /api/seed-workspace` | 按 `Seed + 年数` 合并注册槽位、Release、缓存和玩家存档 | `seed-workspace-response.schema.json` |
| `GET /api/city-market-viewer/index?seed=&years=` | 从有效 Seed 缓存读取城市轻量索引 | `city-market-context-index-response.schema.json` |
| `GET /api/city-market-viewer/chunk?seed=&years=&city=` | 从同一缓存按需读取单城分块 | `city-market-context-chunk-response.schema.json` |
| `GET /api/global-viewer/index?seed=&years=` | 从有效 Seed 缓存读取全球主链与 14 区目录 | `global-viewer-context-index-response.schema.json` |
| `GET /api/global-viewer/region?seed=&years=&region=` | 从同一缓存按需读取单区域宏观、航空需求与运力供给 | `global-viewer-context-region-response.schema.json` |
| `GET /api/forecast-viewer/index?seed=&years=&mode=` | 从有效 Seed 缓存分别读取玩家或审计预测索引 | `forecast-viewer-context-index-response.schema.json` |
| `GET /api/forecast-viewer/report?seed=&years=&mode=&report=` | 从同一缓存按需读取单份预测报告分块 | `forecast-viewer-context-report-response.schema.json` |
| `GET /api/random-seed` | 用 Python `secrets` 生成正式随机 Seed | `random-seed-response.schema.json` |
| `GET /api/task-status?seed=&years=` | 同步 Run 的内存进度 | `task-progress-response.schema.json` |
| `GET /api/jobs/<jobId>` | 后台任务状态与完成结果 | `background-job-response.schema.json` |
| `GET /api/schema` | Schema 目录及关键 API 映射 | 目录自身带版本 |
| `GET /api/cached-runs` | Seed 缓存清单与保留信息 | `cached-runs-response.schema.json` |

后台 Job 状态为 `queued`、`running`、`complete` 或 `failed`。相同 Seed、年数和 `force` 语义的活动任务会复用同一个 Job；普通请求和强制重算不会错误去重。队列与运行中任务合计最多 16 个，执行 worker 为 2。

### 3.1 统一 Seed 工作区

`GET /api/seed-workspace` 是首页 Seed 中心的数据基础。槽位使用 `seed_<seed>_years_<years>`，响应包含：

- 当前槽位、选择来源和工作区 revision；
- 注册表是否缺失、有效、部分降级或损坏；
- 缓存有效性、实际字节、文件数和 pinned 状态；
- 玩家存档是否有效及其独立路径；
- 是否对应当前 Viewer Release；
- 经营、全球、城市、玩家预测和审计预测当前是否可打开；
- 活动槽位、当前 Release 和 pinned 缓存等保护原因。

注册表磁盘契约是 `seed-workspace.schema.json`，只保存槽位元数据；组合后的 HTTP 响应使用 `seed-workspace-response.schema.json`。GET 仍严格只读，不创建 Seed、不运行模型、不删除数据，也不把一个 Seed 的页面请求回退到另一个 Seed。统一 Seed 四页迁移完成后 API 升级为 v3；模型版本和输出 Schema 版本没有变化。

经营页的浏览器上下文由 URL 中成对出现的 `seed` 与 `years` 确定。两项都缺失时，前端只读取一次 `activeSlot` 并用 `history.replaceState` 补成可复现 URL；只缺一项、值非法或槽位未注册都会阻止继续请求。`/api/run-job`、`/api/beijing-operations`、`/api/player-simulation`、玩家行动接口和 `/api/sim-save` 共用该上下文，并校验成功响应中的 Seed 与年数。这里没有新增第二套服务端 Session，也不会把请求隐式改写为当前 Release。

### 3.2 城市 Viewer 缓存读取

城市页对当前发布槽位继续直接读取 Manifest 指向的版本化 bundle 和分块。只有非发布且缓存有效的槽位才调用：

```text
GET /api/city-market-viewer/index?seed=20260716&years=60
GET /api/city-market-viewer/chunk?seed=20260716&years=60&city=beijing_airport_system
```

两个接口严格只读，只接受已注册、`cacheStatus=ready`、`cacheRunId` 与 `(seed, years)` 一致的槽位；过期缓存返回 409，槽位或城市不存在返回 404，非法参数返回 400。响应的 `context` 包含 `seed`、`years`、`slotId`、`source=seed_cache`、工作区 revision 和 `cacheRunId`。索引与块仍分别复用现有 v2 Viewer 协议，包装 Schema 只增加来源身份，不加入机场运营字段。

### 3.3 全球 Viewer 缓存读取

全球页对当前发布槽位继续直接读取 Manifest 指向的版本化 bundle 和 14 个区域分块。只有非发布且缓存有效的槽位才调用：

```text
GET /api/global-viewer/index?seed=20260716&years=60
GET /api/global-viewer/region?seed=20260716&years=60&region=china_mainland
```

两个接口同样严格只读并要求注册槽位、`ready` 缓存和一致的 `cacheRunId`。索引返回全球主链、区域协调和轻量区域目录；单区域响应返回区域宏观、航空需求和运力供给。服务会验证各组行的 Seed / 年数，在读取期间持有同一 Run 锁，并以 409 `global_viewer_context_unavailable` 拒绝过期缓存。响应上下文与城市接口一致，浏览器还会把槽位身份纳入区域内存缓存键，不会静默改读当前 Release。

### 3.4 预测 Viewer 缓存读取

预测页对当前发布槽位继续读取 Manifest 指向的玩家索引、独立审计索引和报告分块。非发布且缓存有效的槽位改用：

```text
GET /api/forecast-viewer/index?seed=20260716&years=60&mode=player
GET /api/forecast-viewer/report?seed=20260716&years=60&mode=player&report=public_consensus
```

`mode` 只能是 `player` 或 `audit`。服务在同一 Run 锁内读取现有预测 CSV，并调用与正式发布器相同的纯索引/报告序列化器；不生成临时 Release 或落盘分块。玩家模式只投影玩家字段，排除神级报告、真实未来与评分字段；审计模式由单独请求取得。响应上下文包含 `seed`、`years`、`slotId`、`source=seed_cache`、`dataMode`、工作区 revision 和 `cacheRunId`。过期缓存返回 409，缺少槽位或报告返回 404，且不会隐式改读当前 Release。


### 3.5 GDP 缺口与增长护栏字段

`airport-model-output-v2` 在全球年度行增加并版本化以下字段：

```text
gdp_level_gap_pct
output_gap_measurement_residual_pct
output_gap_measurement_version
unclamped_output_gap_target_pct
output_gap_floor_applied
output_gap_cap_applied
unclamped_target_growth_pct
soft_limited_target_growth_pct
growth_step_limit_pct
growth_soft_limit_applied
growth_step_cap_applied
growth_step_cap_direction
growth_step_cap_consecutive_years
growth_step_limiter_version
```

`output_gap_pct` 的协议身份不变，仍是政策层和区域层消费的模型估计周期缺口。`gdp_level_gap_pct` 必须由同一已发布行的 `real_gdp_index` 和 `potential_gdp_index` 按 `100 × ln(real/potential)` 计算；测量残差等于估计缺口减严格水平缺口。`unclamped_*` 字段来自真实裁剪前候选，边界布尔值不能从最终输出反推。

区域宏观行新增 `global_gdp_level_gap_anchor_pct`、`global_output_gap_measurement_residual_anchor_pct` 和 `global_output_gap_measurement_version`。它们只传播全球锚的两种口径，不改变区域增长、政策或对账公式。Viewer 必须明确显示“模型估计周期缺口”和“严格 GDP 水平缺口”，不能都简称为“产出缺口”。

### 3.6 收益率、影子短端与美元资金条件字段

`airport-model-output-v3` 在保留 v2 GDP 字段的基础上新增：

```text
yield_curve_boundary_version
expected_shadow_short_rate_10y_pct
unclamped_short_rate_target_pct
unclamped_expected_short_rate_10y_target_pct
unclamped_expected_shadow_short_rate_10y_target_pct
unclamped_2y_yield_target_pct
unclamped_10y_yield_target_pct
unclamped_term_premium_target_pct
short_rate_floor_applied / short_rate_cap_applied
expected_short_rate_floor_applied / expected_short_rate_cap_applied
shadow_short_rate_floor_applied / shadow_short_rate_cap_applied
yield_2y_floor_applied / yield_2y_cap_applied
yield_10y_floor_applied / yield_10y_cap_applied
term_premium_floor_applied / term_premium_cap_applied
short_rate_consecutive_boundary_years
expected_short_rate_consecutive_boundary_years
shadow_short_rate_consecutive_boundary_years
yield_2y_consecutive_boundary_years
yield_10y_consecutive_boundary_years
term_premium_consecutive_boundary_years
dollar_liquidity_boundary_version
unclamped_dollar_target_index
dollar_floor_applied / dollar_cap_applied
dollar_consecutive_boundary_years
unclamped_financial_conditions_target_index
financial_conditions_floor_applied / financial_conditions_cap_applied
financial_conditions_consecutive_boundary_years
```

`expected_short_rate_10y_pct` 是可观察名义政策短端预期，默认下限 `0.05%`；`expected_shadow_short_rate_10y_pct` 是可有限为负的 QE 影子状态。`global_dollar_index` 字段名为兼容保留，唯一正式定义是“美元资金条件指数/代理”，不是严格 DXY。全球 Viewer lazy index 与 region chunk 协议同步升级到 v2。

边界布尔值来自真实裁剪点：最终状态边界使用平滑后的未裁剪候选，目标边界使用公式目标候选。连续年数按实际边界应用连续累计，脱离边界即归零。

### 3.7 次级饱和诊断字段

信用、资产与能源层对以下七个字段统一发布真实未裁剪目标、floor/cap applied、`boundary_state` 和连续边界年数：`global_credit_spread_index`、`credit_availability_index`、`credit_impairment_stock_index`、`equity_earnings_index`、`equity_risk_premium_pct`、`brent_oil_price_usd`、`energy_cost_pressure_index`。`boundary_state` 的正式枚举为 `none`、`floor`、`cap`、`soft_floor`、`soft_cap`。软边界保留未裁剪目标用于区分严重程度；固定 0–100 指数仍有外层安全边界；盈利指数没有固定常数上限。

### 3.8 统一宏观起点与前缀契约

`airport-model-output-v4` 保留 v3 的收益率—美元和次级饱和字段，并统一全球八层的 `year_index=0` 语义。第 0 行是配置起点，不是第一年结束值：stock/level 字段直接等于版本化参数初值，change/yoy/flow 为零或明确的基期定义，事件与风险状态为 `initial`/`none`，边界布尔值为 false。第一次年度转移和第一次随机 draw 都发生在 `year_index=1`；不得为兼容旧 digest 在起点预抽样或丢弃随机数。

同一 Seed 和参数下，`years=0/1/2/60` 的较短结果必须是较长结果的逐字段严格前缀。`years=0` 返回 1 行，`years=1` 返回 2 行；公共年份数量契约没有改变。全球行中的 `macro_feedback_*` 行级收敛字段是该年度达到逐字段固定点的前缀稳定诊断，Run/Manifest 中的收敛摘要仍是发布授权的权威 run-level 结论。区域第 0 行只读消费相同的全球增长、缺口、通胀、政策率、10Y 和 HY 起点锚，不改写区域公式。Viewer 时间轴将第 0 行标为“起点”。贷款字段贯通不属于本版本。

## 4. POST 接口

所有 POST 都要求 `Content-Type: application/json`，UTF-8 JSON 对象，大小不超过 2 MiB。

### 4.1 Seed 工作区写操作

```text
POST /api/seed-workspace
```

同一路径按 `action` 支持：

- `create-random`：创建未占用的随机 `Seed + 年数` 槽位；
- `import`：导入指定 Seed，重复导入复用槽位；
- `activate`：切换活动槽位；
- `remove-slot`：只移除非活动、没有缓存/存档/Release 的空草稿；
- `plan-delete` / `delete`：分别预览和执行单槽位缓存或玩家存档删除；
- `plan-retention` / `apply-retention`：分别预览和执行 Seed 缓存保留计划；
- `set-retention`：只保存 1–50 的缓存上限，不立即删除文件。

除只读预览外，写操作必须携带 GET 返回的 `expectedRevision`。revision 过期返回 409，前端应刷新后重新操作。删除执行还必须携带同一次预览返回的 `planId` 和 `confirm: true`；目标字节、文件数、修改时间、revision 或 Run 锁发生变化都会拒绝执行。服务端只根据规范槽位 ID重新构造路径，不接受前端传入的任意文件路径。

活动槽位、当前 Viewer Release 和 pinned 缓存会在 `protectedReasons` / `blockers` 中说明。清缓存明确保留玩家存档，删存档明确保留 Seed 缓存；本接口不删除版本化 Release 或正式源 Run。响应使用 `seed-workspace-action-response.schema.json`。

首页的“删除 Seed”不是新的 API action：它在一次明确确认后，必要时先激活当前 Release 或其它备用槽位，再对目标缓存和存档分别取得新鲜 `plan-delete`，逐项执行 `delete`，最后以当时的 revision 调用 `remove-slot`。任何一步发生并发变化都会由既有校验拒绝，页面随后重新读取真实工作区状态。

### 4.2 运行城市市场

```text
POST /api/run
POST /api/run-job
```

最小请求：

```json
{
  "seed": 20261324,
  "years": 60,
  "force": false
}
```

`/api/run` 同步返回城市市场汇总；`/api/run-job` 返回 HTTP 202 与 `jobId`，完成后的 `result` 使用同一 Run 响应结构。Schema：`seed-explorer-run-response.schema.json` 与 `background-job-response.schema.json`。

### 4.3 北京经营历史

```text
POST /api/beijing-operations
```

```json
{
  "seed": 20261324,
  "years": 60,
  "force": false,
  "mode": "replay"
}
```

当前 `mode` 的正式只读值是 `replay`。响应包含季度经营、财务、项目、合同和展示所需摘要。Schema：`beijing-operations-response.schema.json`。

`quarters[].finance` 中的现金流展示字段均以百万元人民币计：`operatingCashFlow` 是“经营利润减现金税”的简化经营现金流，`investingCashFlow` 是资本开支与重建拆除支出的负数，`freeCashFlowBeforeFinancing` 是融资前自由现金流，`financingCashFlow` 是贷款提款减本金偿还，`cashNetChange` 是期末现金减期初现金。利息仍由正值字段 `interestExpense` 表示，现金勾稽为：

```text
cashNetChange
  = freeCashFlowBeforeFinancing + financingCashFlow - interestExpense
```

### 4.4 玩家模拟运营

```text
POST /api/player-simulation
```

```json
{
  "seed": 20261324,
  "years": 60,
  "force": false,
  "playerActions": [],
  "currentQuarterIndex": 20
}
```

服务端校验行动类型、字段和时点，并以行动日志作为经营重算来源。响应 Schema：`player-simulation-response.schema.json`。当前响应含 `allQuarters` 供本地季度切换；它是调试/原型接口边界，不应直接当作正式游戏的信息权限设计。

### 4.5 玩家存档

```text
POST /api/sim-save
```

公共定位字段是 `seed` 与 `years`，`action` 可为：

- `status`：检查当前 Seed 是否有存档；
- `load`：读取存档；
- `save`：写入当前季度和玩家行动；
- `clear`：清除当前 Seed 的单一存档。

`status` 在没有存档时返回 `save: null`，`clear` 响应不含 `save`；两种当前响应形态都由 `sim-save-response.schema.json` 描述。实际写入的 `seed-explorer-simulation-save-v0.3` 对象由 `simulation-save.schema.json` 固定字段和类型。

### 4.6 开发审计候选报告

```text
GET  /api/forecast-candidate-catalog?seed=&years=&source=
POST /api/forecast-candidate
```

目录接口返回 4 个正式等级、8 种普通基础风格、15 个修饰标签、矛盾标签组合、最低分数区间宽度，以及请求来源上下文和数据终点。生成接口最小请求示例：

```json
{
  "seed": 424242,
  "years": 60,
  "source": "viewer_release",
  "asOfYear": 2030,
  "tierProfileId": "initial_v1",
  "narrativeProfileId": "public_consensus_v2",
  "modifierMode": "auto",
  "modifierIds": [],
  "scoreMin": 70,
  "scoreMax": 80,
  "generationNonce": 0
}
```

接口装配位于 `server/forecast_candidates.py`。调用方必须明确传入 `viewer_release` 或 `seed_cache`；服务校验注册槽位、Seed、年数和精确来源后，读取同一来源的北京城市市场数据，绝不在来源不可用时回退当前 Release。目录和生成响应都携带同一个审计 `context`，浏览器会比较 Release ID 或缓存 Run ID 与工作区 revision。v2 生成器算法本身不变，继续使用与正式报告相同的总量和五类客群预测链路；响应含完整审计行、实际评分和各分项结果，但不执行文件写入。Schema：`forecast-candidate-catalog-response.schema.json` 与 `forecast-candidate-response.schema.json`。

## 5. Schema 清单

### 版本、Run 与发布

- `airport-version-record.schema.json`
- `macro-run-manifest.schema.json`
- `viewer-release-manifest.schema.json`

Viewer Manifest v2 使用 `downstream_csv_copy_count` 记录发布后刷新的独立模型 CSV 数量，不再记录或生成浏览器 canonical 副本。当前正式 Manifest 已完成 v2 实际发布；Schema 继续接受历史 v1 Manifest，新发布只写 v2。`workspace-status-response.schema.json` 的 Viewer 状态只有 `versioned_release` 与 `unavailable`，后者不会触发浏览器回退。

新生成的 Macro Run Manifest 会为每个 variant 保存版本化反馈收敛摘要，包括完整 `pass_diagnostics[]`、常量反馈更新策略和 `fixed_point_residual_diagnostic`。发布 baseline 或 scenario 时，服务端要求至少 3 次回跑、最后两个相邻 Pass 逐字段通过，并要求候选路径的无松弛影子 Pass 同样通过八字段门槛。旧 Manifest 仍可作为归档读取，但缺少当前残差验证、诊断链或版本标识时不得重新发布；`--publish-viewer none` 可保留未收敛诊断 Run。

### API 公共结构与响应

- `api-envelope.schema.json`
- `api-error-response.schema.json`
- `health-response.schema.json`
- `workspace-status-response.schema.json`
- `seed-workspace.schema.json`
- `seed-workspace-response.schema.json`
- `seed-workspace-action-response.schema.json`
- `city-market-context-index-response.schema.json`
- `city-market-context-chunk-response.schema.json`
- `global-viewer-context-index-response.schema.json`
- `global-viewer-context-region-response.schema.json`
- `forecast-viewer-context-index-response.schema.json`
- `forecast-viewer-context-report-response.schema.json`
- `random-seed-response.schema.json`
- `task-progress-response.schema.json`
- `background-job-response.schema.json`
- `cached-runs-response.schema.json`
- `seed-explorer-run-response.schema.json`
- `beijing-operations-response.schema.json`
- `player-simulation-response.schema.json`
- `simulation-save.schema.json`
- `sim-save-response.schema.json`
- `forecast-candidate-catalog-response.schema.json`
- `forecast-candidate-response.schema.json`

### Viewer 按需加载

- `forecast-viewer-lazy-index.schema.json`
- `forecast-viewer-report-chunk.schema.json`
- `global-viewer-lazy-index.schema.json`
- `global-viewer-region-chunk.schema.json`
- `operations-viewer-lazy-index.schema.json`
- `operations-viewer-chunk.schema.json`
- `city-market-viewer-lazy-index.schema.json`
- `city-market-viewer-chunk.schema.json`

### 预测配置目录

- `forecast-config.schema.json`
- `forecast-tier-catalog.schema.json`
- `forecast-narrative-catalog.schema.json`

`/api/schema` 映射核心 API 和服务启动所需的 Schema；`schemas/` 中的 Viewer 分块 Schema 也由测试直接验证，即使它们不是独立 HTTP API 响应。

## 6. Viewer 分块协议的共同规则

轻量索引至少承担以下职责：

- 声明索引和数据块 Schema 版本；
- 给出默认项与稳定顺序；
- 记录相对文件名、行数、字节数和 SHA-256；
- 让页面在加载块后校验身份与数量；
- 缺少必需索引或数据块时明确失败，不静默切换到另一份整包数据。

发布时必须先准备数据块，最后切换索引或 Manifest 指针，不能让浏览器短暂读取一个指向缺失块的新目录。

### 客流预测的玩家与审计边界

客流预测使用同一套 v2 索引和分块 Schema，但按 `dataMode` 分成两个独立发布入口：

| 数据模式 | 索引 | 内容 |
| --- | --- | --- |
| `player` | `<market_id>_forecast_index.js` | 12 份普通报告的叙事、总量与客群预测路径、区间和修订 |
| `audit` | `<market_id>_forecast_audit_index.js` | 13 份报告的隐藏真值、神级报告、原始信号和评分拆解 |

玩家块不包含 `debug_*`、`realized_*`、旧隐藏曲线字段或生成器内部能力分。玩家报告会包含基础风格的中文名称、方法说明和典型盲点，以及修饰标签的 ID、中文名称、分类、作用和代价；还会携带五类潜在需求、计划投放、有效供给、满足率、缺口和边际区间。前端不需要维护另一套标签翻译表。预测页面默认只加载玩家索引；用户显式切换“开发审计”后才加载审计索引和对应报告块。审计块使用独立白名单加入隐藏真值、信号和评分；旧 `forecast_lag_years` 与 `lagged_hidden_curve_*` 只暂留 CSV 兼容协议，不进入浏览器。完整预测 JS 已退出生成、发布和页面加载链。

候选报告 API 不属于 Viewer 发布块。页面只在开发审计模式加载候选目录和调用生成接口，候选行保存在浏览器内存中；退出候选、刷新页面或离开审计模式即丢弃，不会进入玩家索引和审计静态分块。

## 7. 错误响应

使用统一错误响应的接口会返回 `ok: false`、`error`、`errorCode` 和公共版本元数据。少数兼容 GET 路由（例如非法 task-status 查询或未知路径）目前仍只返回 `ok` 与 `error`，这是尚未完全统一的协议边界，调用方不应假定每个非 2xx 响应都已有 `errorCode`。

| HTTP | `errorCode` | 典型原因 |
|---:|---|---|
| 400 | `invalid_request` | JSON、Seed、年数、行动或编码不合法 |
| 403 | `non_local_request` | 默认模式拒绝非回环 Host/Origin |
| 404 | `resource_not_found` / `job_not_found` | 输出、存档或 Job 不存在 |
| 409 | `resource_conflict` | Run 或资源状态冲突 |
| 413 | `request_too_large` | 请求体超过 2 MiB |
| 415 | `unsupported_media_type` | POST 不是 JSON |
| 500 | `internal_error` | 未分类内部错误；细节只写服务日志 |
| 503 | `job_queue_full` | 后台任务已达活动上限 |
| 504 | `task_timeout` | 同步模型运行超时 |

## 8. 兼容与变更规则

同一 Schema 主版本内：

- 可以增加可选字段；
- 不得删除必需字段；
- 不得改变已有字段的类型、单位或含义；
- 不得静默改变排序、舍入和空值语义。

不兼容修改至少要同步：

1. `config/airport_versions.json`；
2. 对应 Schema 版本或文件名；
3. 固定 Seed API 快照；
4. 前端读取逻辑；
5. 存档或发布数据的迁移/回退说明。

项目使用测试目录中的轻量 Schema 验证器，不要求额外安装 `jsonschema`。完整验证命令见 [测试与安全修改](../development/Testing_and_Safe_Changes.md)。
