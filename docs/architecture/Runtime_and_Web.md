# 运行与 Web 架构

## 1. 一个进程、一个端口、五个页面

当前正式服务入口和路由实现位于：

```text
airport_sim/server/app.py
airport_sim/server/routes.py
airport_sim/server/api_contract.py
```

公开入口是：

```powershell
py -3.13 -m airport_sim serve --host 127.0.0.1 --port 8776
```

它使用 Python 标准库的多线程 HTTP 服务，同时提供页面、静态资源、Viewer 输出、Schema 和 JSON API。普通用户不需要分别启动“前端”和“后端”；`start_airport_ui.bat` 启动的就是这一个统一进程。

`airport_sim/paths.py` 依据包文件位置统一解析 `config/`、`output/`、`saves/`、`schemas/` 和 `web/`，默认路径不依赖启动时的当前工作目录。只有命令显式传入 `--output-root` 或 `--viewer-output-root` 时，才使用调用者给出的路径。

## 2. 稳定浏览器地址

| 正式地址 | 物理页面 | 用途 |
|---|---|---|
| `/` | `web/pages/airport_home.html` | 工作台首页 |
| `/seed-explorer` | `web/pages/seed_explorer_viewer.html` | 动态测试与玩家经营 |
| `/global-gdp` | `web/pages/global_gdp_viewer.html` | 全球/区域宏观与航空 Viewer |
| `/city-markets` | `web/pages/city_market_viewer.html` | 中国大陆城市航空市场 Viewer |
| `/beijing-forecast` | `web/pages/beijing_potential_passenger_forecast_viewer.html` | 叙事化客流预测报告与开发审计 |

旧的 `/beijing-operations` 与 `beijing_airport_operations_viewer.html` 重定向到 `/city-markets`；其它兼容地址仍映射到对应页面。正式地址末尾多出的 `/` 会重定向到无斜杠地址。

页面必须通过 8776 服务访问，不建议双击 HTML 使用 `file://`。页面依赖 `/static/`、`/output/` 和 `/api/`，脱离服务后这些路径不能保持相同含义。

## 3. 前端文件如何组织

```text
web/
  pages/                 HTML 页面骨架
  static/
    css/                 页面样式
    js/
      shared/            共用 API client
      home/              首页
      seed-explorer/     动态测试与经营模块
      global-gdp/        全球 Viewer
      city-markets/      城市市场 Viewer
      beijing-forecast/  预测 Viewer
```

HTML 负责稳定 DOM 结构，CSS 负责展示，JavaScript 负责页面状态、请求和图表。前端可以：

- 选择 Seed、Run、变体、区域、报告和季度；
- 请求 Python API；
- 对服务端数据做展示性筛选和汇总；
- 绘制图表与表格；
- 在无新行动时复用已加载季度。

前端不应自行维护正式经营账本，也不应重新实现合同、项目、融资、税务、现金和资产负债表公式。

## 4. 服务端职责

```text
airport_sim/server/
  app.py          兼容装配和进程入口
  routes.py       页面/API 路由、Host/Origin 与安全文件路径
  api_contract.py API 版本元数据、Schema 文件和端点目录
  beijing_operations.py 北京城市需求默认化、季度经营/财务序列化和读取编排
  forecast_candidates.py 正式发布上下文、审计候选目录和生成请求装配
  http.py         JSON、错误、请求体、文件与重定向响应
  jobs.py         有界后台任务
  player_service.py 玩家存档命令、模拟配置/命令、行动缓存和响应装配
  player_actions.py 有序行动日志协调、槽位改名和季度换算
  player_contracts.py 合同行动规范化与同周期替换
  player_financing.py 融资产品、贷款规范化和模型贷款转换
  player_projects.py 项目目录、槽位状态机、冷却期和模型事件转换
  progress.py     任务进度与结构化日志
  run_cache.py    Seed 缓存路径、指纹、读写、清单和保留
  run_service.py  缓存复用、Run 加锁/执行、城市聚合和进度顺序
  run_locks.py    每 Run 锁与缓存维护预留
  storage.py      文件、配置缓存与原子写入
  repository.py   玩家存档仓储
  serializers.py  城市结果摘要
  validation.py   输入与结果验证
  workspace_service.py Viewer 状态、缓存/存档计数和页面目录
```

一次请求通常依次经过：

```text
Host/Origin 本机检查
  -> 路由匹配
  -> JSON、Seed、年数与行动校验
  -> Run 锁、缓存或模型执行
  -> 序列化与版本元数据
  -> JSON 响应
```

`POST /api/run` 是兼容的同步接口。`POST /api/run-job` 会先返回 `jobId`，调用方再轮询 `/api/jobs/<jobId>`；它改善等待方式，但不会把单个 Run 的模型层自动并行化。

Seed Run 的固定调用顺序是：

```text
首次缓存检查
  -> 未命中时取得同 Run 锁
  -> 锁内再次检查缓存
  -> 执行 seed-cache Profile
  -> 聚合城市结果
  -> 原子写入缓存摘要
  -> 按保护规则清理过期 Seed 缓存
  -> 更新完成或失败进度
```

该顺序由 `run_service.py` 统一实现，`app.py` 保留同名兼容函数并在调用时注入现有根目录、锁、进度和缓存函数。这样测试与旧调用方仍可在 `app.py` 替换依赖，同时 Run 服务不再依赖路由实现。

玩家模拟在取得同 Run 锁后使用固定顺序：

```text
取得或复用 Seed Run
  -> 清洗玩家行动日志
  -> 检查行动、配置、模型脚本和服务代码指纹
  -> 未命中时依次重建城市需求、季度经营和财务产物
  -> 两层命令都成功后写入行动缓存 Manifest
  -> 聚合北京季度结果
  -> 裁剪当前季度可见历史并装配玩家响应
```

该顺序及玩家存档命令由 `player_service.py` 实现。行动日志保持原输入顺序，由 `player_actions.py` 协调 `player_contracts.py`、`player_financing.py` 与 `player_projects.py`：同槽位改名和同合同周期采用最后一项，同季度融资采用第一项，项目按已接受行动维护槽位尺寸、完成时间、冷却期和拆除净空。`app.py` 继续暴露原函数名并注入当前配置读取函数，因此路由和旧测试入口不变。

北京经营产物由 `beijing_operations.py` 在同一 Run 锁内读取。它负责城市需求缺失字段默认化、季度经营与按年/季度配对的财务行映射、警告和 `playerStartIndex`，并区分 replay 与 `simulate_default` 两种产物目录；replay 缺少必需产物时只按既有规则执行一次强制重试。字段名、字段顺序、舍入、空值和经营 CapEx 回退仍是既有 API 契约。`app.py` 保留所有同名兼容包装器和 mock 点，不复制第二套序列化逻辑。

开发审计候选由 `forecast_candidates.py` 装配。它只读取当前正式 Manifest 记录的来源目录和北京城市市场 CSV，校验 Release/Seed 一致性，然后把原始行与规范化请求交给既有预测候选层；不复制预测公式、评分或叙事逻辑，也不写入候选文件。等级顺序、数据起止年、请求默认值和错误顺序属于现有 API 契约。

`workspace_service.py` 只把当前 Viewer Manifest、缓存清单、递归存档数量和固定页面地址装配为工作区状态。无 Manifest 或 Manifest 不可读时仍报告 `legacy_canonical`；路径继续相对于工作区根并使用 POSIX 表达。`app.py` 对这两个服务继续保留同名兼容函数，使路由和测试 patch 点不变。

路由清单由 `routes.route_contract()` 统一记录，并由 `test_server_routes.py` 固定。当前分层如下：

| 路由族 | 处理职责 | 响应 | 缓存 |
|---|---|---|---|
| 首页与 Viewer 正式/兼容地址 | `routes.py` 页面映射 | HTML 文件 | `no-cache` |
| 尾斜杠和旧北京经营地址 | `routes.py` 重定向映射 | 302 空响应 | `no-store` |
| `/static/<path>` | 固定 Web 根、安全路径和扩展名 | 静态文件 | `no-cache` |
| `/schemas/<name>.schema.json` | 单层 Schema 白名单路径 | JSON Schema | `no-cache` |
| `/output/<path>` | 固定输出根、安全路径和扩展名 | Viewer 文件 | 当前资源 `no-cache`；版本化 Release 可 `immutable` |
| GET/POST `/api/*` | `routes.py` 分发到 `app.py` 暴露的现有服务函数 | 带版本元数据的 JSON | `no-store` |

HTTP 分发仍只由 `routes.py` 负责。业务函数由 `app.py` 兼容暴露并委托给独立服务，使现有调用方、测试 mock 和旧入口保持有效；`app.py` 现在主要承担兼容装配和进程入口，不再作为新增领域规则的落点。

## 5. 页面数据来自哪里

### Seed Explorer

Seed Explorer 通过 `/api/run`、`/api/beijing-operations`、`/api/player-simulation` 和 `/api/sim-save` 与后端交互。正式随机 Seed 来自 `/api/random-seed`。

### 三个只读 Viewer

三个 Viewer 优先读取：

```text
output/current_viewer_manifest.js
output/viewer_releases/<release_id>/
```

全球和预测 Viewer 在没有有效 Manifest 时可读取 `output/` 下的 canonical 当前索引；两者的 canonical 入口仍是轻量索引和按需分块，不存在完整数据或逐脚本回退。城市市场 Viewer 只读取同一版本化 release 内的城市索引与分块，避免混用不同发布。三个 Viewer 缺少必需索引时都会显示发布数据不可用，而不会静默拼接旧数据。它们不会因为 Seed Explorer 新建了临时缓存而自动切换。

### 全球浏览器预览

全球宏观页保留一套近似预览模型，用于快速观察页面内 Seed。它不调用正式 Run、不写盘，也不能作为 Python 结果来源。

## 6. HTTP 文件边界

服务只允许从固定根目录读取受支持类型：

| URL 前缀 | 物理根目录 | 用途 |
|---|---|---|
| `/static/` | `web/static/` | CSS、JavaScript、图片和 JSON |
| `/output/` | `output/` | 已生成的 Viewer 数据 |
| `/schemas/` | `schemas/` | `*.schema.json` |

所有路径都会解析后再次确认仍位于对应根目录，拒绝 `..` 等目录穿越。`/schemas/` 只允许单层 Schema 文件名；`/static/` 和 `/output/` 还限制扩展名。

所有文件响应都按 64 KiB 分块流式发送，并以所发送表示的 SHA-256 作为 ETag；客户端传回匹配的 `If-None-Match` 时返回 `304`。当前不实现 Range 请求。

缓存与压缩按资源身份分层：

| 资源 | `Cache-Control` | gzip |
|---|---|---|
| `viewer_releases/<release_id>/` 中的 JSON/JavaScript | `public, max-age=31536000, immutable` | 发布期预生成，按 `Accept-Encoding` 选择 |
| 当前 Manifest、HTML、普通静态资源、canonical 输出和 Schema | `no-cache` | 不使用旁车 |
| API JSON | `no-store` | 不使用文件旁车 |

gzip 表示还会发送 `Content-Encoding: gzip` 与 `Vary: Accept-Encoding`，原文件继续保留供不支持 gzip 的客户端使用。旧 Release 不原地修改；只有采用新发布器生成的 Release 才带旁车。

## 7. 本机安全边界

默认只绑定 `127.0.0.1`，并检查请求的 `Host` 和 `Origin` 是否属于回环地址。POST 请求还必须：

- 使用 UTF-8 `application/json`；
- 顶层是 JSON 对象；
- 请求体不超过 2 MiB。

绑定局域网地址必须显式使用：

```powershell
py -3.13 -m airport_sim serve --host 0.0.0.0 --port 8776 --allow-non-loopback
```

这会放宽本机来源检查，不是推荐的日常方式，也不等同于经过鉴权的公网服务。

## 8. 兼容入口的定位

以下入口仍可调用同一正式服务：

```text
py -3.13 -m airport_ui
dynamic_tests/seed_explorer/start_seed_explorer.bat
dynamic_tests/seed_explorer/seed_explorer_server.py
```

它们的作用只是兼容旧习惯。新增命令、路由和服务逻辑应写入 `airport_sim`，不要在旧入口再建立第二套实现。
