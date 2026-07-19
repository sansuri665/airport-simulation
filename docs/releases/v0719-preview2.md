# v0719 Preview2 交接说明

本文记录 `v0719-preview2` 阶段快照的发布边界。该版本建立在 `v0719-preview` 之上，保存兼容边界退役和 API v2 收敛结果；它仍是快速迭代的 Preview，不代表预测系统已经完成独立正式产品验收。

## 1. Git 边界

- 发布分支：`agent/forecast-system-0719-preview2`。
- 发布标签：`v0719-preview2`。
- 上一个阶段版本继续由 `agent/forecast-system-0719-preview` 与 `v0719-preview` 保存。
- 远端默认分支从旧 `main` 切换为本发布分支后删除 `main` 分支指针；`main` 的祖先提交仍存在于两个 Preview 分支历史中，不做历史改写。
- 本次不创建合并请求，也不把 Preview2 解释为已批准合并或正式发布。

以后发布和处理 GitHub 传输故障时遵循 [GitHub 发布与故障恢复](../development/GitHub_Publishing_and_Recovery.md)，不依赖本交接说明还原临时操作过程。

## 2. 本阶段完成内容

- `airport_sim` 成为唯一 Python 命令与本地服务入口；删除无消费者的 `airport_ui`、`dynamic_tests` 旧包和 `airport-ui` 控制台命令。
- 页面只保留五个正式短地址；旧 HTML 地址和北京经营页面别名返回 HTTP 404。
- 玩家存档统一使用 `POST /api/sim-save`；旧 `/api/sim-save-slot` 与 `/api/sim-save-slots` 退出公开契约。
- 删除启动期旧动态测试存档迁移、缓存清理前迁移和旧嵌套输出审计；现有 `saves/seed_explorer/` 内容未改写。
- API Schema 升级为 `seed-explorer-api-v2`，Schema 目录、固定响应快照、API 文档和 CI 同步更新。
- 原临时重构文档归档为 [v0719 Preview 交接说明](v0719-preview.md)；未来任务只保留在 [Roadmap](../plans/Roadmap.md)。

## 3. 验收快照

- Python 3.13 完整回归：302 项通过。
- 配置契约：59 份 JSON、13 个配置族通过。
- 文档：29 份 Markdown、233 个本地链接通过。
- 浏览器 JavaScript：30 个文件语法通过。
- Python 编译、统一 CLI、宏观编排器帮助入口和 `git diff --check` 通过。
- 8776 服务重新加载后报告 `seed-explorer-api-v2`；五个正式页面返回 HTTP 200，退役页面/API 返回 HTTP 404，统一存档状态请求返回 HTTP 200。
- 固定 Seed 数值、模型版本、现有 3 个玩家存档和生成输出未因本阶段修改。

## 4. 不属于本次发布的工作

- 不执行 Release-only、canonical 回退、Run Viewer 产物或备份 Release 清理。
- 不修改玩家信息可见性边界、预测公式、随机数消费顺序或季度经营计算。
- 不继续机械拆分 `app.py`、宏观编排器或季度经营主函数。

下一轮若继续压缩输出，应先完成 Release-only 消费者审计与真实浏览器验证，再生成只读删除计划；当前和上一个 Viewer Release 在该验收完成前都应保留。

## 5. 标签后的 Release-only 维护进度

以下工作发生在 `v0719-preview2` 标签和远端阶段快照之后，不改写该标签所代表的提交。源代码、测试和本文更新应在下一次统一提交中作为 Preview2 的后续维护记录；`output/` 被 Git 忽略，清理结果不会靠 Git 提交恢复。

2026-07-19 已完成上一节规划的 Release-only 收敛：

- 全球、城市和预测浏览器只接受 `current_viewer_manifest` 指向的版本化 Release；缺失时工作区报告 `unavailable`，页面明确报错，不再读取 canonical。
- Viewer Manifest 新发布协议升级为 v2，以 `downstream_csv_copy_count` 记录独立模型命令仍需要的 CSV 同步数量；Schema 继续接受历史 v1 Manifest。此处完成代码与契约迁移，当前磁盘发布随后在第 6 节完成 v2 实际切换。
- 发布器不再复制全球或预测 canonical 的 JS、索引和分块；保留的同步白名单只包含独立模型命令仍读取的 CSV。
- `full` Run 停止生成 14 个区域宏观、14 个航空需求、14 个运力供给、47 个城市市场，以及北京经营、财务、估值共 92 个旧整包 JS。新全球 Release 必须有全球主数据、协调主数据和轻量区域索引，不再构造逐脚本回退 bundle。
- 全球页退出归档 Run 直读，不再加载浏览器版 `macro_run_index.js` 或显示 Run/情景选择器；后端继续保留 `macro_run_index.json`，供工作区状态和内部工具使用。
- 全球 bootstrap 同时移除了内联 `onerror`，清除当前已知的 CSP 小障碍。

删除前冻结 `output/` 为 863 个文件、756,269,804 字节。服务停止后，精确删除：

| 目标 | 文件 | 字节 | 说明 |
|---|---:|---:|---|
| 浏览器 canonical | 43 | 155,709,584 | 全球主脚本/索引/14 区块、协调主脚本、预测索引与玩家/审计块 |
| Run 旧整包 JS | 92 | 39,275,992 | 新发布器不再消费的逐区域、逐城市及经营/财务/估值整包 |
| 旧备份 Release | 90 | 162,257,008 | `forecast_component_v12_20260717...`；阶段验收后从两个 Release 收敛到一个 |
| Run 索引浏览器 JS | 1 | 1,190 | 全球页退出归档 Run 直读后不再生成 |
| 合计 | 226 | 357,243,774 | 约 340.69 MiB |

该轮清理完成时，`output/` 为 637 个文件、399,026,030 字节（380.54 MiB）。当时唯一保留的 Release 是 `forecast_v12_closeout_20260718_baseline_20260718_014210_762075800`，90 个文件、160,752,735 字节；Manifest SHA-256 为 `73eba23dc2f1888a759a03d851ddd5d845fa5f1fd0b70b5cf9fb3eea1c190b66`。唯一正式 Run 的 96 个 CSV、138 个 JSON、Seed 缓存的 207 个文件以及 `saves/` 的 3 个文件大小均与删除前一致。Run 只剩发布所需的 6 个 JS：全球主数据、全球索引、协调主数据、预测玩家/审计索引和经营轻量索引。第 6 节记录此 v1 Release 被真实 v2 发布替换后的现状。

验收包括 Python 3.13 完整 299 项测试、浏览器 JavaScript 语法、Schema 和文档链接检查。真实浏览器在删除前后都重新加载当前 Release：全球页显示 61 行并成功按需切换中国大陆；最终页面不再出现归档 Run/情景选择器，加载脚本只来自当前 Manifest 与当前 Release；城市页显示 47 城并成功加载北京；预测玩家视图和开发审计分块均正常；控制台无 warning/error。删除后的两个 canonical URL、浏览器 Run 索引和旧 Release URL 返回 HTTP 404，当前 Release bundle 返回 HTTP 200。

恢复边界：当前 Release 和源 Run 可以直接继续使用；被删除的 canonical 与 92 个旧 JS 都是可从源 Run 或历史代码派生的副本。旧备份 Release 本地没有直接副本，只能在需要时从其历史版本、相同 Seed 与配置重新运行并发布；这次删除不是回收站操作。

## 6. Viewer Manifest v2 真实发布演练

2026-07-19 使用现存 `forecast_v12_closeout_20260718/baseline`、Seed 424242 直接调用 Viewer 发布器，没有重新执行任何模型。发布前完整 299 项测试通过；v1 页面基线为全球 61 行、城市 47 城、预测玩家与开发审计各 315 行。

新 Release 为 `forecast_v12_closeout_20260718_baseline_20260719_134006_934279300`。Manifest 已实际切换为 `airport-viewer-release-manifest-v2`，删除 `canonical_copy_count`，并记录 `downstream_csv_copy_count = 93`。新旧 Release 的 90 个原始文件集合一致；除三个 bundle 中必然变化的 Release ID 与 Manifest 版本外，所有文件逐字节一致，规范化后的三个 bundle 也完全一致。93 个下游 CSV 与源 Run 的 SHA-256 全部相同，因此这次发布只改变包装、版本指针和压缩表示，不改变模型内容。

v2 Release 为全部 90 个 JSON/JavaScript 原文件生成确定性 gzip：160,752,735 个原始字节压缩为 10,091,345 字节。真实 HTTP 请求确认全球、城市、预测 bundle 和预测审计 JSON 都返回 `Content-Encoding: gzip`、`Vary: Accept-Encoding` 与 immutable 缓存；全球 bundle 的传输长度从约 4.24 MB 降至 352,389 字节。

真实浏览器重新验收后，全球仍为 61 行并成功加载中国大陆区域块；城市仍为 47 城并完整加载北京；预测玩家视图仍为 12 份报告/315 行，开发审计仍为 13 份报告/315 行。所有页面只加载新 v2 Release。

验收通过后，在停止服务并确认目标不是当前 Release、位于 `output/viewer_releases/` 直接子目录且不含重解析点之后，删除旧 v1 Release 的 90 个文件、160,752,735 字节。最终 `output/` 为 727 个文件、409,177,762 字节（390.22 MiB）；唯一 Release 有 90 个原文件和 90 个 gzip 文件，共 170,844,080 字节。当前 Manifest SHA-256 为 `e966485aa7e6219f3363e7434942347c28ba760d6e85a29ab388acf13d2948cd`。

保护项保持一致：正式 Run 仍为 240 个文件、187,007,320 字节；Seed 缓存仍为 207 个文件、41,496,465 字节；`saves/` 仍为 3 个文件、5,734 字节。旧 v1 Release 的删除不是回收站操作；如需恢复，可从保留的源 Run 和相应历史代码重新发布。当前 v2 Release 可直接由现存源 Run 与当前发布器重建。
