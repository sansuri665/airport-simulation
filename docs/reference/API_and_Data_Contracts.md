# API 与数据契约

## 1. 范围

8776 本地服务使用 JSON API 连接网页、模型、缓存和玩家存档。`schemas/` 中的 JSON Schema 2020-12 用于固定必需字段、类型、协议版本和基础约束；Schema 不定义模型公式，也不会替代固定 Seed 数值回归。

正式服务：

```text
airport_sim/server/app.py
```

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
  "apiSchemaVersion": "seed-explorer-api-v1",
  "modelVersion": "airport-model-v0.8",
  "outputSchemaVersion": "airport-model-output-v1",
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
| `GET /api/random-seed` | 用 Python `secrets` 生成正式随机 Seed | `random-seed-response.schema.json` |
| `GET /api/task-status?seed=&years=` | 同步 Run 的内存进度 | `task-progress-response.schema.json` |
| `GET /api/jobs/<jobId>` | 后台任务状态与完成结果 | `background-job-response.schema.json` |
| `GET /api/schema` | Schema 目录及关键 API 映射 | 目录自身带版本 |
| `GET /api/cached-runs` | Seed 缓存清单与保留信息 | 当前仅共享公共元数据 |
| `GET /api/sim-save-slots` | 已弃用的多槽位兼容响应 | 无；始终提示使用 `/api/sim-save` |

后台 Job 状态为 `queued`、`running`、`complete` 或 `failed`。相同 Seed、年数和 `force` 语义的活动任务会复用同一个 Job；普通请求和强制重算不会错误去重。队列与运行中任务合计最多 16 个，执行 worker 为 2。

## 4. POST 接口

所有 POST 都要求 `Content-Type: application/json`，UTF-8 JSON 对象，大小不超过 2 MiB。

### 4.1 运行城市市场

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

### 4.2 北京经营历史

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

### 4.3 玩家模拟运营

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

### 4.4 玩家存档

```text
POST /api/sim-save
```

公共定位字段是 `seed` 与 `years`，`action` 可为：

- `status`：检查当前 Seed 是否有存档；
- `load`：读取存档；
- `save`：写入当前季度和玩家行动。

`POST /api/sim-save-slot` 是旧名称兼容入口，使用同一处理逻辑。存档接口目前只共享 API 公共元数据，尚无独立响应 Schema。

### 4.5 开发审计候选报告

```text
GET  /api/forecast-candidate-catalog
POST /api/forecast-candidate
```

目录接口返回 4 个正式等级、8 种普通基础风格、15 个修饰标签、矛盾标签组合、最低分数区间宽度，以及当前正式 Viewer 发布的 Seed 和数据终点。生成接口最小请求示例：

```json
{
  "seed": 424242,
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

接口只读取 `current_viewer_manifest.json` 指向的正式城市市场数据，Seed 不一致或自然预测期越过数据终点会拒绝请求。v2 生成器使用与正式报告相同的总量和五类客群预测链路；响应携带完整审计行、实际评分、总量结果分、分项结果分、四个分项子分、是否命中目标范围和搜索次数，但不执行任何文件写入。Schema：`forecast-candidate-catalog-response.schema.json` 与 `forecast-candidate-response.schema.json`。

## 5. Schema 清单

### 版本、Run 与发布

- `airport-version-record.schema.json`
- `macro-run-manifest.schema.json`
- `viewer-release-manifest.schema.json`

### API 公共结构与响应

- `api-envelope.schema.json`
- `api-error-response.schema.json`
- `health-response.schema.json`
- `workspace-status-response.schema.json`
- `random-seed-response.schema.json`
- `task-progress-response.schema.json`
- `background-job-response.schema.json`
- `seed-explorer-run-response.schema.json`
- `beijing-operations-response.schema.json`
- `player-simulation-response.schema.json`
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
