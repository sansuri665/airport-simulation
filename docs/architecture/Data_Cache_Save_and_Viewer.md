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

## 3. Seed Explorer 缓存

动态测试缓存的目的只有一个：同样的计算依赖没有变化时，不重复跑完整模型。

```text
output/seed_explorer_runs/<seed_and_years>/
```

缓存 Manifest 包含模型脚本、配置、服务代码和 Python 环境指纹。代码或配置变化后，旧目录可以仍然存在，但服务会把它判定为失效并重算，不会仅凭目录名称复用。

默认保留最近 2 个有效缓存。缓存策略位于 `saves/cache_policy.json`，它影响保留数量，不参与模型数值指纹。

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
```

## 4. 玩家存档

玩家存档独立位于：

```text
saves/seed_explorer/<seed_and_years>/dynamic_test_save.json
```

存档主要保存当前季度和行动日志，而不是复制一整套季度报表。读取时，服务按同一 Seed、年数和行动重新取得经营结果；对应缓存不存在或已失效时可以重算。

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

新 release 先在 staging 目录完成数据包和 SHA-256，再复制 canonical 兼容数据，最后原子替换当前 Manifest 指针。页面因此只会看到完整旧版本或完整新版本。

Manifest 记录 release、Run、变体、Seed、起始年、年数、模型与输出 Schema 版本、生成时间，以及三个 Viewer 数据包的路径、数量和哈希。首页通过 `/api/workspace-status` 展示这些信息。

## 6. 版本化发布与 canonical 回退

三个 Viewer 的读取顺序是：

```text
有效 current_viewer_manifest
  -> 版本化 release 数据
  -> 若不存在或不适用，再读取 canonical 兼容数据
```

canonical 目录包括 `output/global_macro/`、`output/city_airport_quarterly_operations/`、`output/city_airport_potential_passenger_forecast/` 等。它们用于旧页面、旧归档和外部工具兼容，不代表又有一套正式模型。

在兼容窗口结束前，不应只删除旧完整 JS。必须先确认当前页面、旧归档和外部工具都已切换到轻量协议，并由自动化测试保护回退移除。

## 7. 三个 Viewer 的按需加载边界

### 7.1 有效客流预测：按报告

```text
<market_id>_forecast_index.js
<market_id>_forecast_chunks/
  r_<report_id>.json
<market_id>_potential_passenger_forecast_viewer_data.js  # 旧完整回退
```

页面先加载报告目录，只在选择报告时读取对应 JSON 块。目录记录默认报告、报告顺序、行数、字节数和 SHA-256；切换报告时释放上一份解析结果。canonical 发布先复制数据块，最后复制目录指针，避免索引指向尚未就绪的文件。

### 7.2 全球宏观：按区域

```text
global_viewer_index.js
global_viewer_chunks/
  r_<region_id>.json
```

首屏只载入全球主链、区域协调结果和轻量区域目录。切换区域时，一个数据块同时提供区域宏观、航空需求和运力供给；同一页面会话再次访问会复用内存数据。release 与 canonical 都先准备 14 个区域块，再切换索引；旧目录不存在时回退逐脚本加载。

### 7.3 北京经营：经营/财务为核心，估值延迟

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
