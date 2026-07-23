# Run、缓存、存档与 Viewer 数据

## 1. 先区分七个概念

| 名称 | 含义 | 典型位置 |
|---|---|---|
| Seed | 随机世界线的起点，不是结果文件 | 请求参数或 Manifest |
| Seed 槽位 | 对 `Seed + 年数` 的轻量选择记录，不复制结果或玩家进度 | `saves/seed_workspace.json` |
| 正式 Run | 一次完整、可追溯的模型归档 | `output/macro_runs/<run_id>/` |
| 变体 | 同一 Run 下的 baseline 或情景世界线 | Run 内的变体目录 |
| Seed 缓存 | 为动态测试避免重复计算的临时结果 | `output/seed_explorer_runs/` |
| Viewer 发布 | 三个只读 Viewer 当前读取的数据包 | `output/viewer_releases/` |
| 玩家存档 | 当前季度和玩家行动日志 | `saves/seed_explorer/` |

Seed 相同不保证结果相同；年数、参数、配置、模型版本和 Python 环境也必须一致。

## 2. 统一 Seed 工作区

`GET /api/seed-workspace` 提供统一 Seed 的读取层。服务按 `(seed, years)` 合并四类来源：

1. `saves/seed_workspace.json` 中的轻量槽位；
2. 当前 Viewer Release；
3. `output/seed_explorer_runs/` 中的有效或过期缓存；
4. `saves/seed_explorer/` 中的玩家存档，包括没有对应缓存的存档。

槽位 ID 使用 `seed_<seed>_years_<years>`。它只是工作区身份，不等于正式 Run ID；正式发布 Run 可以使用另一名称。注册表只保存当前槽位、可选标签和时间，不保存缓存状态、字节数、发布状态或玩家存档内容，这些事实每次从磁盘重新发现。

服务正式启动时，注册表不存在会按当前发现结果原子初始化；注册表已存在则保留其活动槽位和 revision。损坏或不受支持的注册表不会被自动覆盖，API 会带警告并临时使用磁盘发现结果。普通 GET 不写注册表、不运行模型，也不删除缓存、存档、Release 或正式 Run。

`POST /api/seed-workspace` 把创建、导入、激活、空草稿移除、缓存/存档独立删除和缓存保留策略封装在 `seed_workspace_actions.py`。注册表每次写入先验证完整快照再原子替换，并使用 revision 拒绝陈旧标签页；删除先返回只读计划，再以 `planId + confirm` 执行。服务端从槽位 ID重建路径、验证根目录边界并取得非阻塞 Run 锁。服务端仍拒绝直接删除活动槽位、当前 Release 和 pinned 缓存；首页的“删除 Seed”只在一次用户确认后先切换活动槽位，再组合这些现有安全操作，不增加绕过保护的新接口。

没有有效注册表选择时，活动槽位依次选择最近有效缓存、当前 Viewer Release、最近玩家存档或最近注册槽位。首页、经营页、全球页、城市页和预测页已经使用工作区接口：入口携带 `seed + years`，页面只在 URL 完全缺失上下文时补入活动槽位，此后固定该联合身份。有效缓存是经营操作以及非发布 Seed 的全球、城市、预测 Viewer 数据基础；缓存缺失或过期时页面要求明确生成，不会隐式回退到另一个 Seed。

工作区响应会分别给出缓存、存档、发布、保护原因、实际缓存字节和页面能力。清除缓存与删除玩家存档仍是两种独立服务端语义；首页可在一次确认后把切换槽位、两类安全删除和空槽位移除串成“删除 Seed”。没有新增写入或删除 HTTP 接口。

## 3. 正式 Run 的生命周期

正式入口：

```powershell
py -3.13 -m airport_sim run --seed 20261324
```

默认生成 60 年 baseline，并写入：

```text
output/macro_runs/<run_id>/
  baseline/
  可选情景变体/
  manifest.json
```

总调度器先在同一输出根下建立隐藏 staging 目录。所有层完成后，会校验核心 CSV 的表头、列宽、Seed、年份、`year_index`、行数和 14 区覆盖；通过后才把整个目录原子改名为正式 Run。失败会清理本次 staging，已存在的同名正式 Run 不会被合并覆盖。

`manifest.json` 记录 Run ID、Seed、起始年、年数、运行参数、变体、Python/模型/Schema 版本和校验摘要。

`macro_layers/orchestrator_run_validation.py` 负责核心 CSV 检查、按稳定路径和表头生成 SHA-256 摘要、区域覆盖、变体行数摘要、顶层 Run Manifest 装配，以及同一 staging Manifest 的“写入 staging 状态—校验—写入 complete 状态”顺序。既有年份上界、错误文本、字段顺序、摘要字节和 `airport-run-validation-v1` 格式均由直接特征测试保护。

`macro_layers/orchestrator_variant_outputs.py` 负责单个 baseline/情景变体的产物写入顺序：全球、区域、协调、航空、运力、城市、预测、季度经营、财务、估值，最后写 downstream skip Manifest。它按原 `REGION_ORDER` 或来源字典插入顺序迭代；空市场继续跳过，缺少 `region_id` 继续落到 `unknown_region`。只有 `artifact_profile == "full"` 时才生成发布器仍会消费的 Viewer 源资产：全球主数据、区域协调主数据、全球/预测/经营轻量索引与分块。47 城和 14 区逐对象 JS，以及经营、财务、估值完整 JS 已停止生成；`seed-cache` 和其他非 full 值仍只写 CSV、摘要 JSON 与 skip Manifest。

`macro_layers/orchestrator_run_lifecycle.py` 负责顶层 Run 生命周期：参数组合拒绝与 `index-only` 短路、Seed/时间戳/Run ID 和 staging 命名、重复 Run 拒绝、构建与 staged 校验、目录原子替换、越界保护下的失败清理、可选 Viewer 发布、Run 索引刷新和最终 Manifest 写入。构建、校验、发布和所有 IO 都由原编排器在调用时注入；发布时先写发布信息、再刷新索引并写最终 Manifest 的既有顺序没有改变。

宏观编排器继续保留当前仍有调用方的 `execute_run`、`write_variant_outputs`、`validate_staged_run`、`build_run_manifest`、`build_run_index`、`write_run_index`、`publish_variant_to_viewer` 及 Viewer 资产辅助入口。Run 索引由 `macro_layers/orchestrator_run_index.py` 实现；高层 Viewer 发布生命周期由 `macro_layers/orchestrator_viewer_release.py` 实现；Release 资产与下游 CSV 导出协议由 `macro_layers/orchestrator_viewer_assets.py` 实现。旧 canonical 浏览器复制和精确树裁剪门面已随回退链一起删除；模型调用与变体执行没有移动。

## 4. Seed Explorer 缓存

动态测试缓存的目的只有一个：同样的计算依赖没有变化时，不重复跑完整模型。

```text
output/seed_explorer_runs/<seed_and_years>/
```

缓存 Manifest 包含模型脚本、配置、服务代码和 Python 环境指纹。代码或配置变化后，旧目录可以仍然存在，但服务会把它判定为失效并重算，不会仅凭目录名称复用。

实现边界现在分为：

- `airport_sim/server/run_cache.py`：缓存文件名、依赖文件清单、指纹字节协议、缓存读写/清单和保留；
- `airport_sim/server/run_service.py`：缓存命中、同 Run 加锁、锁内复查、模型调用、城市聚合、缓存保存、保留执行和进度状态顺序；
- `airport_sim/server/beijing_operations.py`：北京需求 CSV 默认化、季度经营/财务行聚合，以及 replay/默认模拟读取编排；
- `airport_sim/server/app.py`：保留同名兼容函数，并把当前路径、锁和函数注入上述服务。

指纹字节顺序继续是缓存协议版本、Python 实现、完整 `sys.version`、平台，再按稳定相对路径顺序加入每个服务/模型脚本和配置文件的路径与内容；每段以 NUL 分隔。它不依赖文件时间或大小，也没有因模块拆分改成另一种算法。

依赖清单自动包含全部 `airport_sim/server/*.py`、`macro_layers/*.py` 和 `config/**/*.json`，所以服务拆分、模型公式和配置变化都会让旧缓存失效；只读的 `forecast_candidates.py`、`forecast_viewer.py` 与工作区服务也进入既有 Run 缓存指纹。系统没有为候选报告或三个 Viewer 的缓存适配新增第二种缓存、Release、Manifest 或磁盘分块。

`seed_workspace.py` 同样按既有规则进入指纹。因此首次接入统一工作区后，旧 Seed 缓存目录可能被标为过期；目录和对应玩家存档不会被这次状态判断删除，下一次明确请求同一 Seed 运行时才会按当前代码安全重建。

`GET /api/cached-runs` 的顶层路径、保留数、指纹版本，以及有效/失效条目的可空 Seed/年数和状态字段由 `cached-runs-response.schema.json` 描述。Schema 只固定现有清单，不参与缓存命中、指纹或保留计算。

默认保留最近 2 个有效缓存。Viewer Release 也默认保留 2 个版本：当前 Manifest 指向的版本和最近一个已完成的备份版本。缓存策略位于 `saves/cache_policy.json`，它影响保留数量，不参与模型数值指纹。

常用只读命令：

```powershell
py -3.13 -m airport_sim cache list
py -3.13 -m airport_sim cache plan
```

安全清理：

```powershell
py -3.13 -m airport_sim cache clean
py -3.13 -m airport_sim cache clean --confirm
```

`clean` 默认只显示计划或要求输入确认。清理会保护当前 Viewer 发布及来源 Run、活动或 staging Run、固定 Run 和 `saves/`；8776 服务正在运行时拒绝破坏性清理。

普通已完成 Macro Run 会标为需要人工复核，不会仅因“比较旧”就进入自动候选；只有名称和状态明确属于历史 test/smoke 的产物才可能进入清理计划。过期 Viewer release 可以清理，但当前 release 始终受保护。

固定重要缓存或调整保留数：

```powershell
py -3.13 -m airport_sim cache pin RUN_ID
py -3.13 -m airport_sim cache unpin RUN_ID
py -3.13 -m airport_sim cache retention 2
py -3.13 -m airport_sim cache viewer-retention 2
```

## 5. 玩家存档

玩家存档独立位于：

```text
saves/seed_explorer/<seed_and_years>/dynamic_test_save.json
```

存档主要保存当前季度和行动日志，而不是复制一整套季度报表。经营页的存档状态、保存、读取和清除都从固定页面上下文构造同一 `Seed + 年数` 请求；服务按该身份和行动重新取得经营结果。对应缓存不存在或已失效时，页面保留存档并要求先生成或重建计算缓存。

存档路径和读写由 `server/repository.py` 管理；请求校验、行动日志清洗后的存档序列化，以及玩家模拟的配置生成、模型命令顺序和季度响应装配由 `server/player_service.py` 管理。经营/财务 CSV 到北京季度 JSON 的字段映射、财务行配对、警告和读取模式由 `server/beijing_operations.py` 管理。

磁盘上的 `seed-explorer-simulation-save-v0.3` 由 `simulation-save.schema.json` 描述；唯一存档接口 `POST /api/sim-save` 使用 `sim-save-response.schema.json`。`status` 无存档时的 `save: null` 和 `clear` 不返回 `save` 的差异继续保留。

玩家模拟产物仍位于对应 Seed 缓存的 `simulation_default/` 下，`action_cache_manifest.json` 仍只保存一个 SHA-256 指纹。指纹来源继续包括行动日志、经营/财务配置、两层模型脚本和服务实现；服务实现摘要按稳定文件名与内容计算，不包含工作区绝对路径。`app.py`、`beijing_operations.py` 及所有 `player_*.py` 服务/领域模块都属于依赖，因此这些实现变化后已有行动缓存会在下一次真正请求玩家模拟时安全重建一次，但缓存目录、Manifest 格式和模型结果不变。Seed Run 缓存本身继续自动覆盖全部 `server/*.py`，因此新模块也进入其既有指纹协议。

因此：

- 强制重算不会删除存档；
- 普通缓存清理不会删除存档；
- 删除 `output/seed_explorer_runs/` 不等于删除玩家进度；
- 直接删除 `saves/` 会丢失玩家数据，不能当作“清缓存”。

## 6. Viewer 发布

生成正式 Run 不会自动改变只读 Viewer。要发布 baseline：

```powershell
py -3.13 -m airport_sim run --seed 20261324 --publish-viewer baseline
```

发布情景变体时使用：

```powershell
py -3.13 -m airport_sim run --seed 20260630 --scenario-state occurred --scenario-branch-id auto --publish-viewer scenario
```

发布生成：

```text
output/viewer_releases/<release_id>/
output/current_viewer_manifest.json
output/current_viewer_manifest.js
```

新 release 先在 staging 目录完成数据包、SHA-256 和 JSON/JavaScript gzip 旁车，再正式化 release 目录、刷新独立模型命令需要的下游 CSV，最后原子替换当前 Manifest 指针。压缩或下游 CSV 同步失败时旧 Manifest 不切换，页面因此只会看到完整旧版本或完整新版本。发布器不再向 canonical 目录复制任何浏览器 JS、索引或分块。

该高层顺序由 `orchestrator_viewer_release.py` 单独控制：三个 bundle 的文件名与写入顺序保持不变，JSON Manifest 仍先写，`current_viewer_manifest.js` 仍是最后的原子指针。`orchestrator_viewer_assets.py` 负责低层 Release 资产、下游 CSV 白名单、路径 URL、SHA-256，以及 `mtime=0`、空文件名、level 9 的确定性 gzip。全球 bundle 缺少全球主数据、协调主数据或轻量区域索引时会直接拒绝发布，不再构造逐区域旧脚本回退包。

原编排器只保留当前发布协议所需的包装器，并逐项注入复制、路径、哈希、gzip 和原子写入函数。两个拆出模块分别管理高层生命周期与低层资产规则，避免日后修改保留策略时误碰 bundle 内容，或修改资产内容时误碰 Manifest 切换顺序。

Manifest 记录 release、Run、变体、Seed、起始年、年数、模型与输出 Schema 版本、生成时间，以及三个 Viewer 数据包的路径、数量和哈希；v2 新发布还记录下游 CSV 同步数量、gzip 文件数、原始字节数和压缩字节数。Schema 继续接受已经存在的 v1 Manifest，但新发布只写 `airport-viewer-release-manifest-v2`。首页通过 `/api/workspace-status` 展示发布信息。

## 7. Release、缓存适配与下游 CSV 导出

三个只读 Viewer 的正式发布读取边界是：

```text
有效 current_viewer_manifest
  -> 版本化 release 数据
Manifest 缺失、无对应脚本或 Release 不完整
  -> 明确报告发布不可用
```

浏览器不再读取 `output/global_macro/`、`output/city_airport_potential_passenger_forecast/` 等 canonical 路径。发布器只继续刷新独立模型命令会读取的下游 CSV，例如全球、区域、航空、城市市场、季度经营和财务 CSV；这些表格是命令串联输入，不是第二套 Viewer 发布。

新增下游导出文件必须先指出真实命令消费者并补契约测试。正式发布数据只能加入版本化 Release；普通 Seed 的页面数据只能由显式工作区上下文从有效缓存只读适配，不能恢复“Manifest 不可用就尝试旧目录”或“缓存不可用就显示当前 Release”的隐式混用。

城市市场 Viewer 不使用跨 Release 或跨 Seed 回退。当前发布槽位的索引保存 47 城各年的轻量排名点，选择城市时读取 `city_market_viewer_chunks/c_<market_id>.json`；其它有效缓存槽位通过只读 API 从相同权威 CSV 生成同构索引与单城块。两条路径共用纯序列化器，页面不生成 47 城合计，也不在磁盘新增分块。

全球 Viewer 采用同一双来源规则：当前发布槽位读取 Release，普通有效缓存槽位通过只读 API 生成全球主链、14 区目录和单区域分块。区域块同时包含区域宏观、航空需求和运力供给。两条路径共用纯序列化器；响应带 `Seed + 年数 + slotId + cacheRunId`，浏览器内存键带完整槽位身份，因此不会串用另一个 Seed 的区域对象。

预测发布缺少玩家轻量索引、全球发布缺少轻量区域索引时都视为不完整，release 构建会失败；页面也会明确报错，不能静默混用旧整包或 canonical 数据。

## 8. 三个 Viewer 的按需加载边界

### 8.1 有效客流预测：按报告

```text
<market_id>_forecast_index.js
<market_id>_forecast_chunks/
  r_<report_id>.json
<market_id>_forecast_audit_index.js
<market_id>_audit_forecast_chunks/
  r_<report_id>.json
```

页面默认只加载玩家目录，其中包含 12 份普通报告的叙事、预测路径、区间和修订，不包含隐藏真值、完整评分和神级报告。选择报告时只读取对应玩家块。显式切换“开发审计”后，页面才加载独立审计索引和审计块；审计共 13 份报告，并包含真实路径与评分拆解。审计字段也使用显式白名单，旧滞后曲线等 CSV 兼容列不会进入浏览器。两个目录都记录默认报告、稳定顺序、行数、字节数和 SHA-256；Release 先准备数据块和审计索引，最后通过 Manifest 切换玩家 bundle。

### 8.2 全球宏观：按区域

```text
global_viewer_index.js
global_viewer_chunks/
  r_<region_id>.json
```

首屏只载入全球主链、区域协调结果和轻量区域目录。切换区域时，一个数据块同时提供区域宏观、航空需求和运力供给；同一页面会话再次访问会复用当前槽位的内存数据。Release 先准备 14 个区域块，再通过 Manifest 切换 bundle；普通缓存槽位使用 `GET /api/global-viewer/index` 和 `GET /api/global-viewer/region`，读取期间持有对应 Run 锁。旧历史 Run 或过期缓存若没有可验证目录会明确显示不可用，不回退逐脚本、canonical 或当前 Release。

### 8.3 城市市场：按城市

```text
city_market_viewer_bundle.js
city_market_viewer_chunks/
  c_<market_id>.json
```

索引包含按所选年份排序所需的需求与航司供给口径；城市块包含完整 60 年潜在客流、航司供给、供给约束后需求、五类客群分配与航司供给状态。页面在城市标题下提供“总客流 + 五客群”六个口径，摘要、轨迹、供给解读和年度表共用同一选择。机场容量和最终经营承接不进入该 Viewer 协议。切换城市时按需读取并在当前页面会话中复用。

缓存来源使用 `GET /api/city-market-viewer/index` 和 `GET /api/city-market-viewer/chunk`。响应包装 `Seed + 年数 + slotId + cacheRunId`，只接受工作区中 `cacheStatus=ready` 且 Run 身份一致的槽位；读取期间持有同 Run 锁。浏览器内存键使用 `slotId:cityId`，因此即使以后同会话切换上下文，也不会复用另一个 Seed 的城市对象。

### 8.4 北京经营源资产

```text
<market_id>_operations_index.js
<market_id>_operations_chunks/
  d_valuation.json
```

`full` Run 暂时保留经营轻量索引和估值分块，供以后恢复独立经营数据客户端时使用；当前公开北京经营页面已退役，Seed Explorer 通过 API 读取经营和财务 CSV。经营、财务和估值完整 JS 已停止生成，也不会发布到 canonical。若以后重新引入经营 Viewer，应直接进入版本化 Release，不恢复三个完整 JS 回退。

## 9. 数据安全原则

1. 不手工把一个 Run 目录覆盖到另一个 Run。
2. 不在服务运行时直接删除其缓存目录。
3. 不把 `output/` 和 `saves/` 放进同一清理动作。
4. 不手改 current Viewer Manifest 指向一个未完成目录。
5. 发布、缓存和存档字段变化时同步 Schema 与契约测试。
6. 需要释放空间时先运行 `cache list` 和 `cache plan`，再确认清理。

API 与 Manifest 的结构见 [API 与数据契约](../reference/API_and_Data_Contracts.md)。
