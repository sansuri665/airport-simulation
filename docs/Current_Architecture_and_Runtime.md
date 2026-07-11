# Airport 当前架构与运行方式

## 1. 这份文档解决什么问题

这是一份只描述**当前已经能够运行的结构**的说明，面向不熟悉计算机项目的使用者。

它主要回答：

- 应该从哪里启动。
- 浏览器页面和 Python 后端各自负责什么。
- Seed、Run、Viewer 发布、缓存和存档有什么区别。
- 各模型模块按什么顺序连接。
- 为什么生成了 Run，页面不一定马上变化。
- 哪些功能已经是正式计算，哪些仍只是预览或实验功能。

未来的界面合并方向另见 `Post_Refactor_UI_Consolidation_Plan.md`，模型设计和长期游戏规划不写入本文。

## 2. 最简单的启动方式

非技术用户在 `airport` 文件夹中双击：

```text
start_airport_ui.bat
```

macOS、Linux，或希望从终端启动的 Windows 用户可以在 `airport` 根目录运行：

```powershell
python -m airport_sim serve
```

这是当前推荐的跨平台入口。`python -m airport_ui` 暂时保留为兼容薄包装，Windows BAT 也调用同一个 `airport_sim serve` 实现。

服务启动后打开：

```text
http://127.0.0.1:8776/
```

这是统一首页，可以进入：

| 地址 | 页面 | 当前用途 |
|---|---|---|
| `/` | 机场模拟工作台 | 查看服务、Viewer 发布、缓存和存档状态 |
| `/seed-explorer` | Seed 动态测试 | 生成世界线、查看城市、推进北京经营并执行玩家行动 |
| `/global-gdp` | 全球宏观 Viewer | 查看全球、区域宏观和区域航空结果 |
| `/beijing-operations` | 北京机场经营 Viewer | 查看已生成的北京经营、财务和实验估值结果 |
| `/beijing-forecast` | 有效客流预测 Viewer | 查看不同质量和报告期的客流预测 |

首页还会读取 `/api/workspace-status`，显示当前 Viewer 的发布模式、Run、变体、Seed、模型版本和发布时间，以及缓存和存档数量。这里展示的是当前 release Manifest 的状态，不是根据输出目录名称猜测出来的结果。

停止服务可以关闭启动窗口、按 `Ctrl+C`，或者双击：

```text
stop_airport_ui.bat
```

服务默认只绑定本机回环地址 `127.0.0.1`。`8776` 是正式本地入口端口；如果该端口被其它程序占用，启动脚本只会提示，不会擅自结束来源不明的进程。

默认模式还会检查请求的 `Host` 和 `Origin` 是否来自回环地址。启动到非回环地址时必须显式传入 `--allow-non-loopback`；这会放宽本地来源检查，只适合使用者明确了解局域网暴露风险的场景，不是普通启动方式。

旧入口 `dynamic_tests/seed_explorer/start_seed_explorer.bat` 仍可使用，但它现在调用同一个统一服务，并直接打开动态测试页。

## 3. 前端和后端分别做什么

可以把系统理解成“页面、服务、模型、数据”四层。

```text
浏览器页面
  -> 本地 Python 服务
  -> Python 模型链
  -> Run、缓存、存档和 Viewer 数据
```

### 3.1 浏览器页面

HTML 页面负责摆放界面结构，`static/css/` 负责样式，`static/js/` 负责页面状态、请求、图表和交互。

页面的主要职责是：

- 读取已经生成的数据。
- 让用户选择 Run、区域、报告、Seed 和季度。
- 绘制图表和表格。
- 把动态测试操作提交给本地 Python API。

浏览器不应成为正式经营、财务或税务账本。玩家合同、项目、融资和季度经营结果由 Python 重算后返回。

全球宏观页面仍保留一套浏览器宏观模拟，用于快速查看不同 Seed 的大致变化。它已经明确标为“浏览器近似预览”，不会写入正式 Run，也不能与 Python 正式结果混为一谈。

### 3.2 本地 Python 服务

本地服务入口是：

```text
dynamic_tests/seed_explorer/seed_explorer_server.py
```

它同时负责：

- 托管统一首页、四个页面和静态资源。
- 提供健康状态、工作区状态和 JSON Schema。
- 由 Python 生成正式随机 Seed。
- 启动完整模型 Run 或读取有效缓存。
- 重算北京经营、财务和玩家行动。
- 读写缓存与玩家存档。
- 返回任务进度和结构化运行状态。

常用接口包括：

```text
GET  /api/health
GET  /api/workspace-status
GET  /api/random-seed
GET  /api/task-status?seed=<seed>&years=<years>
GET  /api/jobs/<jobId>
GET  /api/schema
POST /api/run
POST /api/run-job
POST /api/beijing-operations
POST /api/player-simulation
POST /api/sim-save
```

服务公共职责已经分离为：

```text
seed_explorer_storage.py    文件、JSON、配置缓存和原子写入
seed_explorer_progress.py   结构化日志和任务进度
seed_explorer_run_locks.py  每 Run 锁和缓存维护预留
seed_explorer_http.py       JSON 响应、请求体和静态文件响应
seed_explorer_jobs.py       可选后台 Job 登记与执行
seed_explorer_repository.py 玩家存档 SaveRepository：路径、迁移、读取、清理和摘要
seed_explorer_serializers.py 城市结果汇总 serializers
```

HTTP 路由、运行/玩家编排、其余 API 序列化，以及项目、合同和融资领域规则仍有一部分集中在 `seed_explorer_server.py`。上述公共模块、玩家存档仓储和城市结果汇总 serializers 已经拆出，但不能据此声称服务端 routes/services/domain 分层已经全部完成。

POST 请求只接受 UTF-8 `application/json`，请求体上限为 2 MiB。常见错误分别返回 400、403、404、409、413、415、500、503 或 504，并带稳定的 `errorCode`；服务端记录具体异常，普通 500 响应不会把完整内部异常直接暴露给页面。

`POST /api/run` 继续同步返回，保证旧页面和调用方兼容。需要避免一个 HTTP 请求长时间等待时，可以使用 `POST /api/run-job`，取得 `jobId` 后轮询 `GET /api/jobs/<jobId>`。后台任务会按 Run 和 `force` 语义去重，排队与运行总数有 16 项硬上限；后台 Job 改善等待方式，不改变一个 Run 内部的模型执行顺序。

### 3.3 Python 模型

正式计算位于 `macro_layers/`。总调度器是：

```text
macro_layers/macro_run_orchestrator_sim.py
```

总调度器负责让所有层使用同一个 Seed、同一条上游世界线和同一个 Run 目录。单层脚本仍保留给开发调试，但单独运行时的默认参数可能与总调度器不同，因此不能仅凭 Seed 相同就认为结果来自同一口径。

## 4. 模块关系

当前正式主链可以简化为：

```text
Seed 和运行参数
  -> 全球 GDP、通胀、利率、流动性、信用、资产和油价反馈
  -> 14 区区域宏观
  -> 区域 GDP 对账
  -> 14 区航空需求
  -> 14 区航空供给与满足率
  -> 中国大陆 47 城市机场市场
       ├-> 有效客流预测报告（玩家看到的信息）
       └-> 北京季度经营（使用隐藏真实城市输入）
             -> 北京财务状态
             -> 北京估值观察
```

这里最容易误解的一点是：

> 有效客流预测是城市市场之后的“信息分支”，不是季度经营的输入。

预测报告模拟玩家在不同研究水平下能看到什么；季度经营使用同一世界线中的真实城市客流和航司供给。这样才能比较“玩家当时看到的预测”和“后来真实发生的结果”。

### 4.1 全球宏观层

全球层生成 GDP、通胀、政策利率、收益率曲线、美元流动性、信用利差、资产价格、石油与商品状态，并进行反馈校准。可选分岔情景会形成另一条完整变体，而不只是给 baseline 加一个标签。

### 4.2 区域宏观与航空层

全球结果传入 14 个区域。区域对账层检查区域 GDP 与全球口径的一致性，然后航空需求层计算五类旅客需求，航空供给层计算航司运力和满足率。

### 4.3 城市机场市场层

当前已配置中国大陆 47 个城市机场市场。城市层把区域需求、航司供给和城市 Seed 势能组合起来，得到城市潜在客流、可服务客流和瓶颈状态。

### 4.4 北京经营、财务和动态测试

北京是当前完整经营样板。季度经营接入容量、航站楼项目、服务质量、航空性收入、自营商业、合同和成本；财务层继续计算现金、资产、折旧、贷款、利息、税务和所有者权益。

动态测试提供两种用途不同的模式：

- “加载历史”读取已经生成的完整结果，只用于查看。
- “模拟运营”从玩家可操作季度开始记录合同、项目和融资行动，并由服务端重算经营和财务结果。

玩家存档主要保存当前季度和行动日志，不复制一整套长期报表。相同 Seed、相同年份和相同行动日志可以复用已生成的模拟结果。

## 5. Seed、Run、变体和 Viewer 发布

### 5.1 Seed

Seed 是一条世界线的随机起点。相同 Seed 只有在模型版本、运行参数和配置也相同时，才代表相同结果。

Seed Explorer 的随机按钮通过本地 Python 服务生成 Seed；完整 Run 的随机 Seed 也由 Python 生成。全球宏观页面中的“浏览器预览 Seed”只存在于当前页面内，不属于正式 Run。

### 5.2 正式 Run

正式 Run 是一次完整模型计算的归档：

```text
output/macro_runs/<run_id>/
```

一个 Run 通常包含：

```text
baseline/
可选的 scenario 变体/
manifest.json
```

`manifest.json` 记录 Run ID、Seed、年份、模型和 Schema 版本、Python 版本、参数、变体和校验结果。

总调度器先在隐藏 staging 目录中生成全部结果。当前校验不仅比较总行数，还检查 CSV 表头非空且无重复、每行列宽、Seed、一致的年份与 `year_index` 范围，以及区域宏观、协调、航空需求和供给的 14 区完整性。通过后才把整个目录原子改名为正式 Run，因此失败的计算不会留下一个看似完整的正式目录。

### 5.3 变体

同一个 Run 可以有多条变体：

- `baseline` 是基础世界线。
- `occurred`、`counterfactual` 或 `probabilistic` 情景会形成额外世界线。

变体共享同一个起始 Seed，但情景路径不同。Viewer 的 Run 选择器可以读取归档 Run 和变体。

### 5.4 Viewer 发布

生成正式 Run 不等于立即改变首页上的静态 Viewer。

只有命令包含：

```text
--publish-viewer baseline
```

或：

```text
--publish-viewer scenario
```

才会把指定变体发布给三个静态 Viewer。

发布数据位于：

```text
output/viewer_releases/<release_id>/
output/current_viewer_manifest.json
output/current_viewer_manifest.js
```

新发布先写入 staging 版本目录，完成并计算哈希后，再切换当前 Manifest 指针。页面因此只会看到完整旧版本或完整新版本。

当前 release Manifest 会记录 release、Run 和变体标识，以及 Seed、起始年、运行年数、模型版本、输出 Schema 版本和生成时间；同时记录三个 Viewer 发布包的路径和 SHA-256。它由独立的 `schemas/viewer-release-manifest.schema.json` 约束并接受自动化 Schema 验证。统一首页通过工作区状态接口展示其中的 Run、变体、Seed、模型版本和发布时间。

`output/global_macro/`、`output/city_airport_quarterly_operations/` 等 canonical 路径仍会生成，用于旧页面和外部工具兼容；新 Viewer 优先读取版本化 release，没有有效 Manifest 时才回退 canonical 数据。

## 6. 缓存、正式归档和玩家存档

这三类目录不能混为一谈。

| 数据 | 目录 | 用途 | 是否自动清理 |
|---|---|---|---|
| Seed Explorer 临时 Run 缓存 | `output/seed_explorer_runs/` | 避免同一模型和配置重复计算 | 默认保留最近 2 个有效 Run，可固定或安全清理 |
| 正式 Macro Run | `output/macro_runs/` | 保存正式世界线和变体 | 不应被普通缓存清理删除 |
| Viewer 发布 | `output/viewer_releases/` | 给三个静态 Viewer 提供一致数据 | 当前保留历史版本，后续再制定策略 |
| 玩家存档 | `saves/seed_explorer/` | 保存当前季度和玩家行动日志 | 普通缓存清理不会删除 |

缓存包含模型脚本、配置和 Python 环境指纹。代码或配置变化后，相同 Seed 的旧缓存会自动失效并重算。读取缓存列表时只计算一次当前指纹，再复用于每个条目；指纹依赖文件的字节内容按路径、`mtime_ns` 和大小缓存，未变化文件不会在同一服务生命周期内被反复读取。

玩家存档已经与缓存分离。强制重算或清理旧缓存不会删除独立存档；服务还会把发现的旧缓存内存档迁移到新目录，并暂时保留旧文件用于兼容。

## 7. Viewer 当前的数据加载方式

三个静态 Viewer 都保留旧数据回退，同时减少了首屏加载量：

- 有效客流预测按报告加载 JSON 数据块。
- 全球宏观首屏加载全球主链和区域对账，切换区域时再加载该区域的宏观、航空需求和运力供给。
- 北京经营首屏加载季度经营和财务，打开估值曲线时才加载估值数据。

HTML、CSS 和 JavaScript 已经分离，并进一步按职责拆分：

- 各 Viewer 已有独立 `bootstrap.js` 和 `state.js`。
- 全球 Viewer 已分成 data client、格式化、浏览器预览模型、控件和 Renderer。
- 北京经营 Viewer 已分成 data client、Renderer、状态和页面装配。
- Seed Explorer 已接入共享 API client，并把状态、核心工具、财务、设施、债务、商业、行动、经营渲染和城市渲染拆成九类职责脚本；`page.js` 只保留剩余装配和尚未拆出的交互。
- 有效客流预测已完成 bootstrap/state/page 边界，内部 Renderer 仍可继续细分。

本轮拆分已经通过资源 Smoke Test、固定 Seed 回归和实际浏览器验收；统一首页及四个页面能够加载，关键切换和按需数据请求保持工作。五个页面关键 DOM `id` 的存在性与唯一性已有自动化契约测试；该测试不检查颜色、尺寸或布局，截图视觉基线可在确有视觉风险时按需补充。

## 8. 常用命令

以下命令假设当前目录是 `airport`。

跨平台启动统一工作台：

```powershell
python -m airport_sim serve
```

固定 Seed 生成 baseline：

```powershell
python -m airport_sim run --seed 20261324
```

生成并发布 baseline：

```powershell
python -m airport_sim run --seed 20261324 --publish-viewer baseline
```

生成随机 Seed 的正式 Run：

```powershell
python -m airport_sim run --random-seed
```

生成一条发生分岔的世界线：

```powershell
python -m airport_sim run --seed 20260630 --scenario-state occurred --scenario-branch-id auto
```

运行回归与契约测试：

```powershell
py -3 -B -m unittest discover -s tests -v
```

默认输出路径基于 `airport` 根目录计算，不依赖命令执行时所在的当前目录。显式传入 `--output-root` 或 `--viewer-output-root` 时，才使用用户给定路径。

## 9. 当前已知边界

- 全球 Viewer 的浏览器宏观模型只是近似预览；正式世界线来自 Python。
- 总调度器和部分单层 CLI 的旧默认参数尚未统一，单层运行主要用于调试。
- 北京之外的城市尚未配置完整季度经营、财务、项目、合同和融资。
- 估值仍是观察和实验输出，不是已经完成的正式游戏定价系统。
- 动态测试当前仍会把完整季度结果作为 `allQuarters` 返回浏览器，以支持本地季度推进；正式游戏界面未来应只暴露当期允许看到的信息。
- Viewer release 的历史保留策略、严格 HTTP 缓存头和更细的展示字段裁剪仍待完善。
- 区域与城市并行、玩家行动增量重算已经完成第一轮技术评估，但实施暂缓。确定性、Windows 进程开销和经营财务路径依赖的判断见 `Performance_and_Incremental_Evaluation.md`。

## 10. 三个容易混淆的结论

1. **生成 Run 后页面没变，不一定是错误。** 只有执行 Viewer 发布，三个静态 Viewer 才切换到新数据。
2. **清理缓存不等于删除存档。** 临时 Run 缓存位于 `output/`，玩家存档位于 `saves/`。
3. **预测不决定经营。** 预测是玩家信息，经营使用同一世界线中的真实城市输入。

## 11. 相关文档

- `Game_Overview.md`：游戏机制与当前产品边界。
- `API_and_JSON_Schema.md`：API 和 JSON Schema。
- `macro/Macro_Run_Orchestration.md`：完整 Run 和 Viewer 发布细节。
- `Forecast_Viewer_Lazy_Loading.md`：预测 Viewer 按报告加载。
- `Global_Viewer_Lazy_Loading.md`：全球 Viewer 按区域加载。
- `Operations_Viewer_Lazy_Loading.md`：经营 Viewer 估值按需加载。
- `Performance_and_Incremental_Evaluation.md`：区域/城市并行和玩家增量重算为什么评估完成但暂缓实现。
- `Project_Slimming_and_Python_Entry_Unification_Plan.md`：输出清理、缓存保留和 Python 入口统一的后续实施路径。
- `Post_Refactor_UI_Consolidation_Plan.md`：完成当前整理后的界面合并计划。
