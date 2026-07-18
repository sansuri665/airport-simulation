# v0719 Preview2 交接说明

本文记录 `v0719-preview2` 阶段快照的发布边界。该版本建立在 `v0719-preview` 之上，保存兼容边界退役和 API v2 收敛结果；它仍是快速迭代的 Preview，不代表预测系统已经完成独立正式产品验收。

## 1. Git 边界

- 发布分支：`agent/forecast-system-0719-preview2`。
- 发布标签：`v0719-preview2`。
- 上一个阶段版本继续由 `agent/forecast-system-0719-preview` 与 `v0719-preview` 保存。
- 远端默认分支从旧 `main` 切换为本发布分支后删除 `main` 分支指针；`main` 的祖先提交仍存在于两个 Preview 分支历史中，不做历史改写。
- 本次不创建合并请求，也不把 Preview2 解释为已批准合并或正式发布。

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
