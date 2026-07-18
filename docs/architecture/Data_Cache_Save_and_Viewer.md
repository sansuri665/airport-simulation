# Run、缓存、存档与 Viewer 数据

## 1. 先区分六个概念

| 名称 | 含义 | 典型位置 |
|---|---|---|
| Seed | 随机世界线的起点，不是结果文件 | 请求参数或 Manifest |
| 正式 Run | 一次完整、可追溯的模型归档 | `output/macro_runs/<run_id>/` |
| 变体 | 同一 Run 下的 baseline 或情景世界线 | Run 内的变体目录 |
| Seed 缓存 | 为动态测试避免重复计算的临时结果 | `output/seed_explorer_runs/` |
| Viewer 发布 | 三个只读 Viewer 当前读取的数据包 | `output/viewer_releases/` |
| 玩家存档 | 当前季度和玩家行动日志 | `saves/seed_explorer/` |

Seed 相同不保证结果相同；年数、参数、配置、模型版本和 Python 环境也必须一致。

## 2. 正式 Run 的生命周期

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

`macro_layers/orchestrator_variant_outputs.py` 负责单个 baseline/情景变体的产物写入顺序：全球、区域、协调、航空、运力、城市、预测、季度经营、财务、估值，最后写 downstream skip Manifest。它按原 `REGION_ORDER` 或来源字典插入顺序迭代；空市场继续跳过，缺少 `region_id` 继续落到 `unknown_region`。只有 `artifact_profile == "full"` 时才生成 Viewer JS/懒加载资产并读取 Viewer 配置，`seed-cache` 和其他非 full 值只写 CSV、摘要 JSON 与 skip Manifest。

`macro_layers/orchestrator_run_lifecycle.py` 负责顶层 Run 生命周期：参数组合拒绝与 `index-only` 短路、Seed/时间戳/Run ID 和 staging 命名、重复 Run 拒绝、构建与 staged 校验、目录原子替换、越界保护下的失败清理、可选 Viewer 发布、Run 索引刷新和最终 Manifest 写入。构建、校验、发布和所有 IO 都由原编排器在调用时注入；发布时先写发布信息、再刷新索引并写最终 Manifest 的既有顺序没有改变。

宏观编排器继续保留 `execute_run`、`write_variant_outputs`、`validate_staged_run`、`build_run_manifest`、`build_run_index`、`write_run_index`、`publish_variant_to_viewer` 及 Viewer 资产辅助函数等兼容入口。Run 索引由 `macro_layers/orchestrator_run_index.py` 实现；高层 Viewer 发布生命周期由 `macro_layers/orchestrator_viewer_release.py` 实现；canonical/Release 资产协议由 `macro_layers/orchestrator_viewer_assets.py` 实现。原编排器当前只负责兼容装配、情景选择和模型层调用；模型调用与变体执行没有移动。

## 3. Seed Explorer 缓存

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

依赖清单自动包含全部 `airport_sim/server/*.py`，所以只读的 `forecast_candidates.py` 与 `workspace_service.py` 也会进入既有 Run 缓存指纹；没有为候选报告或工作区状态新增第二种缓存、Manifest 或磁盘产物。

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

## 4. 玩家存档

玩家存档独立位于：

```text
saves/seed_explorer/<seed_and_years>/dynamic_test_save.json
```

存档主要保存当前季度和行动日志，而不是复制一整套季度报表。读取时，服务按同一 Seed、年数和行动重新取得经营结果；对应缓存不存在或已失效时可以重算。

存档路径和迁移由 `server/repository.py` 管理；请求校验、行动日志清洗后的存档序列化，以及玩家模拟的配置生成、模型命令顺序和季度响应装配由 `server/player_service.py` 管理。经营/财务 CSV 到北京季度 JSON 的字段映射、财务行配对、警告和读取模式由 `server/beijing_operations.py` 管理。`server/app.py` 保留原函数入口，旧路由和测试调用方式不变。

磁盘上的 `seed-explorer-simulation-save-v0.3` 由 `simulation-save.schema.json` 描述；`POST /api/sim-save` 及旧别名 `/api/sim-save-slot` 共用 `sim-save-response.schema.json`；已弃用的 `GET /api/sim-save-slots` 使用只允许空 slots 的兼容 Schema。`status` 无存档时的 `save: null` 和 `clear` 不返回 `save` 的差异继续保留。

玩家模拟产物仍位于对应 Seed 缓存的 `simulation_default/` 下，`action_cache_manifest.json` 仍只保存一个 SHA-256 指纹。指纹来源继续包括行动日志、经营/财务配置、两层模型脚本和服务实现；服务实现摘要按稳定文件名与内容计算，不包含工作区绝对路径。`app.py`、`beijing_operations.py` 及所有 `player_*.py` 服务/领域模块都属于依赖，因此这些实现变化后已有行动缓存会在下一次真正请求玩家模拟时安全重建一次，但缓存目录、Manifest 格式和模型结果不变。Seed Run 缓存本身继续自动覆盖全部 `server/*.py`，因此新模块也进入其既有指纹协议。

因此：

- 强制重算不会删除存档；
- 普通缓存清理不会删除存档；
- 删除 `output/seed_explorer_runs/` 不等于删除玩家进度；
- 直接删除 `saves/` 会丢失玩家数据，不能当作“清缓存”。

服务启动时会识别旧缓存目录中的 `dynamic_test_save.json`，将其复制迁移到独立存档目录，并暂时保留旧文件供兼容。

## 5. Viewer 发布

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

新 release 先在 staging 目录完成数据包、SHA-256 和 JSON/JavaScript gzip 旁车，再正式化 release 目录、复制 canonical 兼容数据，最后原子替换当前 Manifest 指针。压缩或复制失败时旧 Manifest 不切换，页面因此只会看到完整旧版本或完整新版本。

该高层顺序由 `orchestrator_viewer_release.py` 单独控制：三个 bundle 的文件名与写入顺序保持不变，JSON Manifest 仍先写，`current_viewer_manifest.js` 仍是最后的原子指针。`orchestrator_viewer_assets.py` 负责被它调用的低层资产协议，包括平面/递归/精确树复制、数据块先于兼容索引、bundle 内容与缺失文件回退、路径 URL、SHA-256，以及 `mtime=0`、空文件名、level 9 的确定性 gzip。精确树裁剪在删除前解析目标路径，拒绝越出目标 Viewer 树。

原编排器保留全部同名包装器，并逐项注入现有复制、路径、哈希、gzip 和原子写入函数，因此既有测试 mock 点、直接脚本入口、公开 URL 和字节协议不变。两个拆出模块分别管理高层生命周期与低层资产规则，避免日后修改保留策略时误碰 bundle 内容，或修改资产内容时误碰 Manifest 切换顺序。

Manifest 记录 release、Run、变体、Seed、起始年、年数、模型与输出 Schema 版本、生成时间，以及三个 Viewer 数据包的路径、数量和哈希；新发布还记录 gzip 文件数、原始字节数和压缩字节数。首页通过 `/api/workspace-status` 展示发布信息。

## 6. 版本化发布与 canonical 指针

全球与预测 Viewer 的读取顺序是：

```text
有效 current_viewer_manifest
  -> 版本化 release 数据
  -> 若 Manifest 不存在，再读取 canonical 的当前索引
```

canonical 目录包括 `output/global_macro/`、`output/city_airport_quarterly_operations/`、`output/city_airport_potential_passenger_forecast/` 等。它们是当前发布的兼容指针，不代表又有一套正式模型。有效客流预测的 canonical 入口也是轻量索引；不再生成或读取完整预测 JS。

城市市场 Viewer 不使用跨 release 回退。当前 release 在索引中保存 47 城各年的轻量排名点，只在用户选择城市时读取 `city_market_viewer_chunks/c_<market_id>.json` 的完整客群与供给状态。页面不生成 47 城合计。

预测发布缺少玩家轻量索引时视为不完整，release 构建会失败；页面也会明确报错，不能静默混用旧整包数据。

## 7. 三个 Viewer 的按需加载边界

### 7.1 有效客流预测：按报告

```text
<market_id>_forecast_index.js
<market_id>_forecast_chunks/
  r_<report_id>.json
<market_id>_forecast_audit_index.js
<market_id>_audit_forecast_chunks/
  r_<report_id>.json
```

页面默认只加载玩家目录，其中包含 12 份普通报告的叙事、预测路径、区间和修订，不包含隐藏真值、完整评分和神级报告。选择报告时只读取对应玩家块。显式切换“开发审计”后，页面才加载独立审计索引和审计块；审计共 13 份报告，并包含真实路径与评分拆解。审计字段也使用显式白名单，旧滞后曲线等 CSV 兼容列不会进入浏览器。两个目录都记录默认报告、稳定顺序、行数、字节数和 SHA-256。canonical 与 release 先复制两组数据块和审计索引，最后切换玩家索引或 Manifest 指针。

### 7.2 全球宏观：按区域

```text
global_viewer_index.js
global_viewer_chunks/
  r_<region_id>.json
```

首屏只载入全球主链、区域协调结果和轻量区域目录。切换区域时，一个数据块同时提供区域宏观、航空需求和运力供给；同一页面会话再次访问会复用内存数据。release 与 canonical 都先准备 14 个区域块，再切换索引。旧历史 Run 若没有新版区域目录会显示需要重新运行或发布，不再回退逐脚本加载。

### 7.3 城市市场：按城市

```text
city_market_viewer_bundle.js
city_market_viewer_chunks/
  c_<market_id>.json
```

索引包含按所选年份排序所需的需求与航司供给口径；城市块包含完整 60 年潜在客流、航司供给、供给约束后需求、五类客群分配与航司供给状态。页面在城市标题下提供“总客流 + 五客群”六个口径，摘要、轨迹、供给解读和年度表共用同一选择。机场容量和最终经营承接不进入该 Viewer 协议。切换城市时按需读取并在当前页面会话中复用。

### 7.4 北京经营：经营/财务为核心，估值延迟

```text
<market_id>_operations_index.js
<market_id>_operations_chunks/
  d_valuation.json
```

季度经营和财务状态共同组成首屏核心包，因为损益、现金、折旧和资产负债表需要一起就绪。估值只在首次打开“估值曲线”时加载，并在当前会话复用。canonical 发布先复制估值块，最后复制轻量目录；没有新目录时回退三个完整 JS。

## 8. 数据安全原则

1. 不手工把一个 Run 目录覆盖到另一个 Run。
2. 不在服务运行时直接删除其缓存目录。
3. 不把 `output/` 和 `saves/` 放进同一清理动作。
4. 不手改 current Viewer Manifest 指向一个未完成目录。
5. 发布、缓存和存档字段变化时同步 Schema 与契约测试。
6. 需要释放空间时先运行 `cache list` 和 `cache plan`，再确认清理。

API 与 Manifest 的结构见 [API 与数据契约](../reference/API_and_Data_Contracts.md)。
