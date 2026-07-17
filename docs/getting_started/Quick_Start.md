# 快速开始

这份说明只解决一件事：在 Windows 上用当前正式入口启动 Airport，并确认它确实在工作。

## 1. 准备环境

项目唯一支持的 Python 版本是 **Python 3.13**，运行时只使用 Python 标准库，不需要另外安装第三方依赖。

在 PowerShell 中确认版本：

```powershell
py -3.13 --version
```

如果命令找不到 Python 3.13，先安装或修复 Python 3.13；不要改用 3.10、3.11 或 3.12 继续测试，否则数值基线不属于本项目支持范围。

## 2. 启动工作台

最简单的方式是在 `airport` 根目录双击：

```text
start_airport_ui.bat
```

脚本会启动正式服务并打开：

```text
http://127.0.0.1:8776/
```

也可以在 `airport` 根目录使用终端：

```powershell
py -3.13 -m airport_sim serve
```

看到以下信息就说明服务已经开始监听：

```text
Airport local UI listening on http://127.0.0.1:8776/
```

不要关闭这个终端窗口；浏览器页面需要它提供数据和计算服务。

## 3. 确认服务状态

首页右上角应显示“本地服务正常”，并展示当前 Viewer 数据、缓存 Run 数量和独立玩家存档数量。

也可以直接打开健康接口：

```text
http://127.0.0.1:8776/api/health
```

返回内容中应包含：

```json
{
  "ok": true,
  "serviceId": "airport-local-ui-v1"
}
```

## 4. 第一次使用

首页有四个入口：

| 入口 | 用途 | 是否会计算 |
|---|---|---|
| Seed 动态测试 | 运行指定世界线、查看城市并模拟北京机场经营 | 会，按需要调用 Python |
| 全球宏观 Viewer | 查看已经发布的全球、区域和航空数据 | 不会 |
| 城市航空市场 | 筛选 47 城并查看单城市潜在客流、航司供给与客群分配 | 不会 |
| 有效客流预测 | 查看已经发布的预测报告 | 不会 |

第一次想生成自己的世界线时：

1. 进入“Seed 动态测试”。
2. 保留默认 60 年，输入一个非负整数 Seed，或点击“Python 随机 Seed”。
3. 点击“运行全链路”。
4. 等状态显示“全链路完成”或“读取已有结果”。
5. 在“城市市场”查看城市，在“北京运营”选择“加载历史”或“模拟运营”。

“Python 随机 Seed”只填写新 Seed，不会自动开始计算。

## 5. 常用终端命令

不经过页面生成一个正式随机 Run：

```powershell
py -3.13 -m airport_sim run --random-seed
```

生成固定 Seed 并发布给三个只读 Viewer：

```powershell
py -3.13 -m airport_sim run --seed 20261324 --publish-viewer baseline
```

只读查看缓存清单和可清理计划：

```powershell
py -3.13 -m airport_sim cache list
py -3.13 -m airport_sim cache plan
```

Run、发布和缓存的区别见 [Run、缓存、存档与 Viewer 数据](../architecture/Data_Cache_Save_and_Viewer.md)。

## 6. 停止服务

可以在启动终端中按 `Ctrl+C`，或者双击：

```text
stop_airport_ui.bat
```

停止脚本会先确认 8776 上运行的是 Airport 服务。若端口属于其他程序，它只会提示，不会结束来源不明的进程。

## 7. 三个重要提醒

1. **运行 Seed Explorer 不会自动更新三个只读 Viewer。** Viewer 只有在正式 Run 使用 `--publish-viewer` 发布后才会切换数据。
2. **缓存不是存档。** 临时计算缓存位于 `output/`，玩家存档位于 `saves/`；安全清理缓存不会删除玩家存档。
3. **全球页面的“浏览器预览”不是正式 Run。** 正式结果始终来自 Python 模型链。

更完整的页面操作见 [用户指南](User_Guide.md)。启动失败时见 [故障排查](../development/Troubleshooting.md)。
