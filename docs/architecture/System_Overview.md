# 系统总览

## 1. 项目是什么

Airport 是一个以 Python 为权威计算源的机场经营模拟工作区。它把同一条 Seed 世界线依次传过全球宏观、区域宏观、区域航空、城市机场市场和北京机场经营/财务模型，再由本地网页展示和操作。

对非计算机专业读者，可以把系统理解为四层：

```text
网页：选择、操作、画图
  ↓
本地服务：接收请求、管理任务、缓存和存档
  ↓
模型链：真正计算宏观、客流、经营和财务
  ↓
本地数据：Run、Viewer 发布、缓存和玩家存档
```

浏览器不是正式账本。合同、项目、融资、现金、税务和资产负债表结果以 Python 服务返回值为准。

## 2. 主模型关系

当前完整链条是：

```text
Seed 与运行参数
  -> 全球宏观反馈链
  -> 14 区区域宏观
  -> 区域 GDP 对账
  -> 14 区航空需求
  -> 14 区航空供给趋势、信心与约束信号
  -> 中国大陆 47 城市机场市场
       ├-> 有效客流预测报告（玩家能看到的信息）
       └-> 北京季度经营（使用同一世界线的真实城市输入）
             -> 北京财务状态
             -> 北京实验估值
```

预测和经营是城市市场之后的两个分支。预测模拟“玩家当时知道什么”，经营使用隐藏的真实城市需求和航司供给；预测本身不会反过来决定真实经营结果。

北京是目前唯一完成季度经营、财务、合同、项目、融资和玩家存档闭环的城市。其他城市已经有市场需求结果，但没有同等完整的动态经营系统。

## 3. 根目录各自负责什么

| 目录或文件 | 当前职责 | 是否为权威来源 |
|---|---|---|
| `airport_sim/` | 正式命令入口、路径定义、缓存生命周期和 8776 服务 | 是 |
| `airport_sim/server/` | HTTP、任务、存储、存档与玩家模拟服务 | 是 |
| `macro_layers/` | 全球到机场经营的 Python 模型与总调度器 | 是 |
| `config/` | 模型参数、城市配置、设施规格和统一版本记录 | 是 |
| `schemas/` | API、Run、Viewer 与按需加载数据协议 | 是 |
| `web/pages/` | 五个 HTML 页面结构 | 前端结构来源 |
| `web/static/` | 页面 CSS、JavaScript、图表和 API client | 前端行为来源 |
| `tests/` | 固定 Seed、协议、路径、缓存、发布和页面契约 | 验收来源 |
| `output/` | 可重算的缓存、正式 Run 与 Viewer 发布 | 生成物，不是源码 |
| `saves/` | 玩家存档与缓存保留策略 | 持久用户数据 |
| `docs/` | 面向用户和开发者的解释 | 应与上述事实来源保持一致 |
| `airport_ui/` | `airport_sim serve` 的兼容包装 | 否 |
| `dynamic_tests/` | 旧 Seed Explorer 启动与导入兼容包装 | 否 |
| `start_airport_ui.bat` | Windows 一键启动 | 正式用户入口 |
| `stop_airport_ui.bat` | 安全停止已确认身份的 8776 服务 | 正式用户入口 |

`output/` 可以重新计算，`saves/` 不能作为缓存一起删除；这是项目最重要的数据边界之一。

## 4. 正式入口

所有日常命令通过同一个包入口：

```powershell
py -3.13 -m airport_sim serve
py -3.13 -m airport_sim run --seed 20261324
py -3.13 -m airport_sim validate-config
py -3.13 -m airport_sim cache plan
```

`airport_ui` 和 `dynamic_tests/seed_explorer/seed_explorer_server.py` 只为旧命令与旧导入保留。新增功能不应继续写进兼容包装。

## 5. 一次页面操作如何到达模型

以 Seed Explorer 的“运行全链路”为例：

```text
用户点击运行
  -> /api/run 接收 seed、years、force
  -> 服务校验输入并为该 Run 加锁
  -> 有效缓存存在：读取缓存
  -> 否则：调用 macro_run_orchestrator_sim
  -> 汇总城市与北京结果
  -> 原子写入缓存
  -> 返回带版本元数据的 JSON
  -> 浏览器更新列表、图表和状态
```

玩家确认合同、项目或融资时，浏览器把完整行动日志提交给 `/api/player-simulation`。服务端重算后返回新的季度路径；页面不能只在本地修改几项数字来冒充正式结果。

## 6. 正式 Run 与 Viewer 不是同一件事

命令行完整 Run 写入：

```text
output/macro_runs/<run_id>/
```

它是一份可追溯的正式世界线归档。只有运行时明确使用：

```powershell
py -3.13 -m airport_sim run --seed 20261324 --publish-viewer baseline
```

才会生成 Viewer release 并切换三个只读 Viewer 的当前数据。单纯生成 Run 后页面没有变化，通常不是故障。

## 7. 当前技术边界

- 正式服务已经迁入 `airport_sim/server/`，但 `app.py` 仍包含部分路由、运行编排和合同/项目/融资规则，尚未完成彻底分层。
- 全球 Viewer 的浏览器预览只用于快速观察；正式世界线来自 Python。
- Seed Explorer 为本地调试和经营原型返回完整 `allQuarters`，因此浏览器当前拥有未来季度数据；成为正式游戏界面前需要收紧可见范围。
- 估值仍是实验观察输出，不是成熟定价系统。
- Viewer 仍保留 canonical 当前索引以兼容无 Manifest 的本地入口；有效客流预测已经取消重复的完整 JS，只保留玩家/审计索引与报告分块。
- 区域并行和玩家行动增量重算尚未实施；当前优先保证固定 Seed 与长期账本一致。

运行与前后端细节见 [运行与 Web 架构](Runtime_and_Web.md)，数据生命周期见 [Run、缓存、存档与 Viewer](Data_Cache_Save_and_Viewer.md)。
