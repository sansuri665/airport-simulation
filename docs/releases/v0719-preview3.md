# v0719 Preview3 交接说明

本文记录 `v0719-preview3` 阶段快照的发布边界。该版本承接 `v0719-preview2` 标签后的维护工作，把 Viewer 消费、发布协议和实际磁盘 Release 一并收敛到 Release-only / Manifest v2；它仍是 Preview，不代表预测系统已经完成独立正式产品验收，也不合并 `main`。

## 1. Git 发布边界

- 发布分支：`agent/forecast-system-0719-preview3`。
- 发布标签：`v0719-preview3`，使用 annotated tag。
- 上一个保留分支：`agent/forecast-system-0719-preview2`。
- 新分支和标签验证后，默认分支切换到 Preview3；最早的 `agent/forecast-system-0719-preview` 分支退出，历史标签继续保留。
- `output/` 与 `saves/` 仍由 Git 忽略；GitHub 保存源代码、测试和文档，不保存本机 Run、Release、Seed 缓存或玩家存档。
- GitHub 发布与传输故障处理遵循 [GitHub 发布与故障恢复](../development/GitHub_Publishing_and_Recovery.md)。

## 2. 本期完成内容

- 全球、城市和预测 Viewer 只读取当前 Manifest 指向的版本化 Release；缺少有效发布时明确报告 `unavailable`，不再访问浏览器 canonical。
- 全球页退出归档 Run 直读和浏览器 Run 索引，不再显示 Run/情景选择器；后端继续保留 JSON Run 索引供工作区和维护工具使用。
- Viewer 发布器只同步 93 个独立模型命令需要的下游 CSV，不再复制浏览器 canonical、旧整包 JS 或分块。
- `full` Run 停止生成 92 个已无消费者的逐区域、逐城市和经营/财务/估值整包 JS。
- Viewer Manifest 新发布只写 `airport-viewer-release-manifest-v2` 和 `downstream_csv_copy_count`；Schema 继续接受历史 v1 Manifest。
- 全球 bootstrap 移除内联 `onerror`，页面启动与 Release-only 契约由特征测试保护。

## 3. 真实 v2 发布结果

使用现存正式 Run `forecast_v12_closeout_20260718/baseline`、Seed 424242 直接发布，没有重新执行模型。当前 Release 为：

```text
forecast_v12_closeout_20260718_baseline_20260719_134006_934279300
```

新旧 Release 的 90 个原始文件集合一致；非 bundle 文件逐字节一致，三个 bundle 去除必然变化的 Release ID 与 Manifest 版本后也完全一致。93 个下游 CSV 与源 Run 的 SHA-256 全部相同。

v2 Release 为 90 个 JSON/JavaScript 原文件生成确定性 gzip：160,752,735 个原始字节压缩为 10,091,345 字节。真实 HTTP 请求确认全球、城市、预测 bundle 和预测审计 JSON 均返回 `Content-Encoding: gzip`；全球 bundle 的传输长度降至 352,389 字节。

旧 v1 Release 在真实浏览器验收后安全删除。最终 `output/` 为 727 个文件、409,177,762 字节（390.22 MiB），只保留当前 v2 Release；正式 Run、Seed 缓存和玩家存档保持演练前基线。

## 4. 验收

- Python 3.13 完整 299 项测试通过。
- 59 份配置、30 个浏览器 JavaScript 文件和 32 份 Markdown 的 244 个本地链接检查通过。
- 两套正式命令入口和 `git diff --check` 通过。
- 真实浏览器验证全球 61 行及中国大陆区域块、城市 47 城及北京明细、预测玩家 12 份报告/315 行、开发审计 13 份报告/315 行。
- 当前 Manifest 为 v2，旧 v1 Release URL 返回 404，新 Release 返回 200；服务健康接口报告 `seed-explorer-api-v2`。

## 5. 仍未完成

- Preview 分支仍未完成独立正式产品验收，因此本期不合并 `main`。
- 正式经营界面的未来信息可见性边界仍按 [Roadmap](../plans/Roadmap.md) 暂缓；Seed Explorer 继续是本地开发与经营原型。
- 季度经营核心、浏览器宏观近似模型和内部兼容门面不因本期发布继续机械拆分。

恢复边界、空间清理明细和 v1→v2 逐步过程见 [v0719 Preview2 交接说明](v0719-preview2.md)。
