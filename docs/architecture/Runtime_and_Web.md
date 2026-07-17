# 运行与 Web 架构

## 1. 一个进程、一个端口、五个页面

当前正式服务实现位于：

```text
airport_sim/server/app.py
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
  app.py          路由、Run/玩家编排和仍待拆出的领域规则
  http.py         JSON、错误、请求体、文件与重定向响应
  jobs.py         有界后台任务
  progress.py     任务进度与结构化日志
  run_locks.py    每 Run 锁与缓存维护预留
  storage.py      文件、配置缓存与原子写入
  repository.py   玩家存档仓储
  serializers.py  城市结果摘要
  validation.py   输入与结果验证
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

## 5. 页面数据来自哪里

### Seed Explorer

Seed Explorer 通过 `/api/run`、`/api/beijing-operations`、`/api/player-simulation` 和 `/api/sim-save` 与后端交互。正式随机 Seed 来自 `/api/random-seed`。

### 三个只读 Viewer

三个 Viewer 优先读取：

```text
output/current_viewer_manifest.js
output/viewer_releases/<release_id>/
```

全球和预测 Viewer 在没有有效 Manifest 时可读取 `output/` 下的 canonical 当前索引；预测 canonical 仍是同一套轻量索引与按报告分块，不存在完整预测 JS 回退。城市市场 Viewer 只读取同一版本化 release 内的城市索引与分块，避免混用不同发布。它们不会因为 Seed Explorer 新建了临时缓存而自动切换。

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

API JSON 使用 `Cache-Control: no-store`，HTML 使用 `no-cache`。当前静态资源尚未配置精细 ETag、压缩和长期缓存策略。

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
