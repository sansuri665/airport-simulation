# 故障排查

按下面顺序检查。不要一遇到问题就删除整个 `output/` 或 `saves/`。

## 1. 启动脚本一闪而过或提示找不到 Python

在 `airport` 根目录打开 PowerShell：

```powershell
py -3.13 --version
py -3.13 -m airport_sim serve --help
```

若第一条失败，安装或修复 Python 3.13。若第二条失败，确认当前目录确实包含 `pyproject.toml` 和 `airport_sim/`。

## 2. 8776 被占用

先检查是不是已经启动的 Airport：

```powershell
Invoke-RestMethod http://127.0.0.1:8776/api/health
```

如果 `serviceId` 是 `airport-local-ui-v1`，无需再次启动，直接打开首页即可。

如果健康接口失败但端口仍被占用：

```powershell
Get-NetTCPConnection -LocalPort 8776 -State Listen
```

启动/停止 BAT 不会结束身份不明的进程。请先确认占用者，再由使用者决定关闭它；不要按 PID 猜测并强制结束。

## 3. 浏览器打不开或首页显示服务异常

1. 保持启动终端处于打开状态。
2. 查看终端是否打印 `Airport local UI listening` 或 Python 异常。
3. 直接访问 `/api/health`。
4. 确认地址是 `http://127.0.0.1:8776/`，不是 `file://`，也不是旧端口。
5. 服务代码刚更新过时，先停止再重启；正在运行的 Python 进程不会自动载入新代码。

## 4. 页面打开但样式、按钮或图表丢失

先按 `Ctrl+F5` 强制刷新，再打开浏览器开发者工具检查 Console 和 Network。

常见判断：

- `/static/...` 为 404：前端文件或 HTML 引用路径不一致；检查 `web/static/`。
- `/output/...` 为 404：当前发布或 canonical 数据不完整。
- JSON 块加载错误：记录缺失的报告、区域或 `d_valuation.json` 路径，不要改成空数组掩盖问题。
- 页面标题正常但图表为空：先查看页头状态文字和 Viewer Manifest，而不是先怀疑模型数值。

查看当前发布：

```powershell
Invoke-RestMethod http://127.0.0.1:8776/api/workspace-status | ConvertTo-Json -Depth 8
```

若 `viewerRelease.mode` 是 `versioned_release`，核对 Manifest 中的 release 是否存在；若是 `legacy_canonical`，页面依赖 canonical 输出。不要手工编辑 Manifest 指针，应该从完整 Run 重新发布。

## 5. 生成了新 Run，但三个 Viewer 仍是旧数据

这是最常见的概念混淆。生成正式 Run 只创建归档，不会切换 Viewer。

需要明确发布：

```powershell
py -3.13 -m airport_sim run --seed 20261324 --publish-viewer baseline
```

发布完成后刷新首页，核对 Run、变体、Seed 和发布时间。Seed Explorer 的临时 Run 也不会自动成为静态 Viewer 发布。

## 6. Seed Explorer 一直计算、失败或重复重算

- 看页面状态和启动终端日志；
- 使用同一 Seed 和年数查看任务进度：

```text
http://127.0.0.1:8776/api/task-status?seed=20261324&years=60
```

- 代码、配置或 Python 环境变化后，旧缓存按设计失效；
- “忽略已有结果，重新生成”会有意跳过有效缓存；
- 不同年数属于不同 Run；
- 同一 Run 正在写入时会由锁串行处理，不应同时删除其目录。

如果长同步请求不适合调用方，可使用 `/api/run-job` 和 `/api/jobs/<jobId>`，但它不会缩短单个模型 Run 的计算链。

## 7. 模拟运营只能看到开头几个季度

确认操作顺序：

1. 左侧选择“模拟运营”，不是“加载历史”。
2. 点击“运营”。
3. 年数应自动扩展到至少 60。
4. 等服务端返回后再点击“下一季度”。

若页面仍保持短年数或只返回四个季度，通常是旧服务进程仍在运行。停止 8776、重新启动当前代码，并用 `Ctrl+F5` 刷新页面。

## 8. 合同、项目或融资按钮无法点击

先区分业务条件和 UI 故障：

- 必须处于“模拟运营”；
- 当前季度必须已进入玩家决策期；
- 合同只有在到期前的谈判窗口开放；
- 项目受槽位占用、在建状态、现金和翻新/重建冷却期限制；
- 融资受每季次数、期限选择和提款后负债率限制。

如果页面说明当前可操作但按钮仍不可用，请记录 Seed、年数、当前季度、模式、事务类型和按钮旁的提示，并检查 Console；这些信息比截图单独出现更容易定位。

## 9. 存档显示为空或读取失败

存档绑定 **Seed 和年数**。先确认输入值与保存时完全一致，再进入模拟运营。

存档实际位于 `saves/seed_explorer/`，缓存位于 `output/seed_explorer_runs/`。缓存被清理后首次读取可能需要重算，但不应导致存档消失。

不要用复制另一个 Seed 的 JSON 来“修复”存档。需要人工检查时先备份原文件，并核对服务日志中的具体错误。

## 10. 缓存清理被拒绝

`cache clean --confirm` 在 8776 正在运行时会拒绝执行，这是数据安全设计。先停止服务，再运行：

```powershell
py -3.13 -m airport_sim cache plan
py -3.13 -m airport_sim cache clean --confirm
```

当前 Viewer release、来源 Run、staging、固定 Run 和玩家存档仍会受保护。

## 11. 测试失败

先确认解释器：

```powershell
py -3.13 --version
py -3.13 -m compileall -q airport_sim macro_layers tests
py -3.13 -B -m unittest discover -s tests -v
```

固定 Seed 摘要失败时，不要立刻更新期望值。先检查随机数调用、迭代/排序、浮点顺序、默认参数、配置和 Python 版本是否无意变化。

Schema 或 API 快照失败时，确认服务响应、Schema、版本记录和前端读取是否同步修改。

## 12. 报告问题时提供什么

尽量同时提供：

- 当前 Git 提交；
- Python 3.13 完整版本；
- 启动命令；
- URL、Seed、年数、模式和季度；
- 页面状态文字；
- Console 第一条 error；
- 服务终端对应错误；
- `/api/health` 与 `/api/workspace-status` 的关键字段。

玩家存档和完整输出可能很大，也可能包含正在测试的策略，不要在未确认范围时整目录上传。
