# Airport API 与 JSON Schema

## 目的

`airport` 使用 JSON Schema 2020-12 描述当前正式 Run Manifest、Viewer release Manifest 和 Seed Explorer 的关键 API 响应。

Schema 的作用是固定字段名称、基础类型、必需字段和协议版本。它不会改变模型公式、随机数、数值精度或现有页面行为。

## Schema 目录

Schema 文件位于：

```text
schemas/
```

当前覆盖：

- `airport_versions.json` 版本记录。
- 完成状态的 Macro Run `manifest.json`。
- Viewer release Manifest。
- API 公共版本元数据和错误响应。
- 本地服务健康状态与工作区状态。
- Seed Explorer 城市市场 Run 响应。
- 北京机场经营历史响应。
- 玩家模拟运营响应。
- Python 随机 Seed 响应。
- 任务进度响应。
- 后台 Run Job 提交与状态响应。
- 有效客流预测 Viewer 的轻量目录和报告数据块。
- 全球 Viewer 的区域轻量目录和区域数据块。
- 北京经营 Viewer 的轻量目录和估值数据块。

## 本地访问

启动统一工作台后访问：

```text
http://127.0.0.1:8776/api/schema
```

该接口返回 Schema 目录和 API 路径对应关系。单个 Schema 可以通过以下形式读取：

```text
http://127.0.0.1:8776/schemas/seed-explorer-run-response.schema.json
```

Schema 文件只允许从固定的 `schemas/` 根目录读取，不能通过路径跳转访问项目中的其他文件。

## Viewer release Manifest

发布 Viewer 时会生成：

```text
output/current_viewer_manifest.json
output/current_viewer_manifest.js
```

Manifest 当前包含 release ID、Run ID、变体、Seed、起始年、运行年数、模型版本、输出 Schema 版本和生成时间，并记录三个 Viewer 发布包的路径、SHA-256 和数量。其正式结构位于：

```text
schemas/viewer-release-manifest.schema.json
```

`GET /api/workspace-status` 会把当前 Manifest 转成 `viewerRelease` 状态。统一首页显示发布模式、Run、变体、Seed、模型版本和发布时间，使页面使用的数据版本可以直接核对。

## Seed Explorer 当前拆分边界

玩家存档路径、旧存档迁移、读取、清理和摘要已经委托给 `seed_explorer_repository.py` 中的 `SaveRepository`；城市市场的 CAGR、瓶颈和城市结果汇总已经委托给 `seed_explorer_serializers.py`。原服务继续保留兼容调用边界，因此这些机械拆分不会改变现有 API 字段或结果。

HTTP 路由、运行/玩家服务、其余 API 序列化以及项目、合同和融资领域规则仍有一部分位于 `seed_explorer_server.py`；当前事实是“仓储与部分 serializers 已拆出”，不是完整 routes/services/domain 分层已经完成。

## 同步 Run 与可选后台 Job

旧同步接口继续保留：

```text
POST /api/run
```

需要先返回、再轮询的调用方可以使用：

```text
POST /api/run-job
GET  /api/jobs/<jobId>
```

`POST /api/run-job` 返回 HTTP 202 和 `jobId`。相同 Run、相同 `force` 语义的任务已经在排队或运行时会复用活动 Job；普通缓存请求与强制重算不会互相去重。排队和运行中的任务合计最多 16 个，超过上限时立即返回 503，避免线程池等待队列无限增长。Job 状态为 `queued`、`running`、`complete` 或 `failed`；完成时 `result` 包含原 Run 响应，失败时只返回简化错误信息，完整错误写入服务端日志。

后台 Job 只改变 HTTP 等待方式，不改变模型公式、随机数、计算顺序或 Run 输出。

## HTTP 请求边界

本地 API 的 POST 请求必须：

- 使用 `Content-Type: application/json`。
- 使用 UTF-8 JSON 对象作为顶层数据。
- `Content-Length` 不超过 2 MiB。

常见错误分类：

| HTTP 状态 | `errorCode` | 含义 |
|---:|---|---|
| 400 | `invalid_request` | 参数、JSON、编码或 Content-Length 不合法 |
| 403 | `non_local_request` | 默认本地模式拒绝非回环 Host/Origin |
| 404 | `resource_not_found` / `job_not_found` | 数据、存档或 Job 不存在 |
| 409 | `resource_conflict` | 目标 Run 或资源状态冲突 |
| 413 | `request_too_large` | 请求体超过 2 MiB |
| 415 | `unsupported_media_type` | POST 不是 `application/json` |
| 500 | `internal_error` | 未分类的服务内部错误，细节查看服务端日志 |
| 503 | `job_queue_full` | 后台任务队列达到上限，请稍后重试 |
| 504 | `task_timeout` | 同步模型运行超时 |

服务默认只绑定 `127.0.0.1`，并检查回环 `Host` 和 `Origin`。非回环地址必须在启动时显式使用 `--allow-non-loopback`；该选项会放宽本地来源检查，不应作为普通默认配置。

## API 公共元数据

所有 JSON API 响应都会保留原有字段，并增加：

```json
{
  "apiSchemaVersion": "seed-explorer-api-v1",
  "modelVersion": "airport-model-v0.5",
  "outputSchemaVersion": "airport-model-output-v1",
  "pythonVersion": "...",
  "schemaCatalog": "/api/schema"
}
```

这些字段用于判断缓存、页面和 API 是否来自同一套模型与数据协议。

## 兼容规则

同一个 Schema 主版本内：

- 可以增加可选字段。
- 不能删除必需字段。
- 不能改变已有字段类型和含义。
- 不能静默改变单位、数值口径或排序规则。

如果必须做不兼容修改，应同时更新：

1. `config/airport_versions.json`。
2. 对应 Schema 的 `$id` 或版本文件名。
3. 固定 Seed API 快照。
4. 前端读取逻辑和迁移说明。

## 验证

项目不依赖第三方 `jsonschema` 包。测试目录提供了覆盖当前 Schema 关键字的轻量验证器，因此仍可直接运行：

```powershell
py -3 -B -m unittest discover -s tests -v
```

测试会验证固定 Seed API、玩家模拟响应、随机 Seed、任务进度、后台 Job、Viewer release Manifest、三个 Viewer 的按需加载协议、版本记录、错误响应和真实 complete Macro Run Manifest。

前端还有独立的关键 DOM 契约：自动解析统一首页和四个主要页面，检查 JavaScript 依赖的关键 `id` 都存在且没有重复。这个自动化保护已经完成；它不等同于截图视觉回归，截图基线只需在确有布局风险时按需增加。

玩家存档、缓存列表等次要接口目前只共享 API 公共元数据，后续在这些接口需要独立演化前再补专用 Schema。
