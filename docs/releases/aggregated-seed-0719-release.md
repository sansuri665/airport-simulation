# 聚合 Seed 0719 正式版交接说明

本文记录 `v0719-preview3` 之后完成的统一 Seed 工作区正式阶段边界。发布分支为 `agent/aggregated-seed-0719-release`，标签为 `聚合seed-0719正式版`。该版本不合并不存在的旧 `main`；模型公式、参数、随机数消费和正式 Viewer Release 结果没有改变。

## 1. Git 与数据边界

- `agent/aggregated-seed-0719-release` 作为当前正式分支，替代已被其完整包含的 `agent/forecast-system-0719-preview2`；`agent/forecast-system-0719-preview3` 保留为上一阶段版本。
- `output/` 与 `saves/` 继续由 Git 忽略。GitHub 只保存源代码、Schema、测试和文档，不上传本机 Release、正式 Run、Seed 缓存或玩家存档。
- 当前 Manifest 仍指向 `forecast_v12_closeout_20260718_baseline_20260719_134006_934279300`，其 SHA-256 未因本阶段改变。
- GitHub 操作继续遵循 [GitHub 发布与故障恢复](../development/GitHub_Publishing_and_Recovery.md)。

## 2. 统一 Seed 工作区

- 首页统一管理 `Seed + 年数` 槽位，支持输入或随机生成、激活、后台生成世界、缓存保留、独立清理以及完整删除非 Release Seed。
- “删除 Seed”在一次确认后，必要时先切换到当前 Release 或其它备用槽位，再对缓存和玩家存档分别执行已有的安全预览/确认操作，最后移除空槽位；当前 Release 和 pinned 缓存保持受保护。
- 经营、全球、城市和预测四页都使用 URL 中固定的 `seed + years`，不再各自选择 Seed，也不会被其它标签页的活动槽位变化静默改写。
- 当前发布槽位继续读取版本化 Release；其它有效槽位直接按需读取同一份 Seed 缓存，不生成每 Seed Viewer Release，也不落盘第二套浏览器分块。
- Release、Seed 缓存、玩家存档和正式 Run 保持独立生命周期；首页统计在每次写操作后重新读取真实状态。

## 3. 预测与场景收尾

- 预测玩家索引/报告与开发审计索引/报告由独立请求投影，响应携带可校验的槽位、来源、模式、revision 和 Release/缓存身份。
- 候选报告目录和生成请求必须显式绑定 Viewer Release 或 Seed 缓存，不再隐式借用当前发布；候选仍不写入正式发布或玩家存档。
- 当前 Release 的 12 份玩家报告（5,478 行）和 13 份审计报告（7,018 行）与共享序列化链逐份标准化哈希一致。
- 普通 Seed 缓存的预测读取改为依据 Run Manifest 校验 Seed、起始年份和总年数；60 年 Run 可正确容纳预测报告保留的前置历史区间，同时仍拒绝错误年数和越界报告年份。
- 全球页删除无消费者的动态世界残余；页面内分岔推演收敛到 `scenario-model.js` 的五个明确入口，仍只影响浏览器临时场景，不写盘、不替代 Python 权威结果。

## 4. 本机存档审计

提交前本机只保留两个有效 60 年槽位：当前活动的 `20260222` 和当前 Viewer Release 对应的 `424242`。两份玩家存档均为 `seed-explorer-simulation-save-v0.3`，路径身份、Seed、年数和 Run ID 一致；两份 Seed 缓存均通过当前指纹校验。旧测试存档和空草稿已通过正式工作区操作清理。

这些本机事实用于证明生命周期操作可用，不属于 Git 快照。删除普通 Seed 后，缓存可用同一 Seed 重新生成，但没有备份的玩家行动不会自动恢复。

## 5. 验收与剩余边界

- Python 3.13 完整 337 项测试通过。
- 59 份配置、31 个浏览器 JavaScript 文件和 33 份 Markdown 的本地链接检查通过。
- 真实浏览器验证首页固定深链、四页共享上下文、预测玩家/审计双标签、候选生成、全球分岔场景，以及 Seed 新增、激活、切换、独立清理和整体删除确认流程。
- 临时实施文档已删除；当前事实进入正式架构、API、用户指南和本交接说明，Roadmap 只保留未来事项。
- 正式玩家信息可见性边界仍未完成；在合并经营、预测、合同、项目和融资界面前，必须先处理 `allQuarters`、未来合同结果和隐藏预测真值。

上一阶段的 Release-only、Manifest v2 和 gzip 实际发布结果见 [v0719 Preview3 交接说明](v0719-preview3.md)。
