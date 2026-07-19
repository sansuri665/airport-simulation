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

首页右上角应显示“本地服务正常”，并展示当前 Viewer 数据、缓存 Run 数量和独立玩家存档数量。页面中部的“统一 Seed 中心”还应显示当前活动的 `Seed + 年数` 槽位；四个功能入口都由这个槽位生成固定地址。

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

首页先管理 Seed 世界，再提供四个入口：

| 入口 | 用途 | 是否会计算 |
|---|---|---|
| Seed 动态测试 | 运行指定世界线、查看城市并模拟北京机场经营 | 会，按需要调用 Python |
| 全球宏观 Viewer | 查看当前槽位的全球、区域和航空数据 | 不会 |
| 城市航空市场 | 筛选当前槽位的 47 城市场结果 | 不会 |
| 有效客流预测 | 查看当前槽位的预测报告 | 不会 |

第一次想生成自己的世界线时：

1. 在首页保留默认 60 年，输入一个非负整数 Seed，或点击“随机生成”。
2. 点击“创建并激活”。这一步只建立或复用工作区槽位，不会运行模型。
3. 点击“生成当前世界”，等待首页显示缓存可用。
4. 从首页进入“Seed 动态测试”；地址会携带固定的 `seed + years`。
5. 在“城市市场”查看城市，在“北京运营”选择“加载历史”或“模拟运营”。

“随机生成”只填写新 Seed，不会创建槽位或开始计算。模拟运营要求 60 年槽位；高级设置中的 5–90 年主要用于短期测试或长期分析。

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

1. **生成工作区 Seed 不会自动更新当前 Viewer Release。** 三个 Viewer 可以只读适配当前活动 Seed 的有效缓存，但只有正式 Run 使用 `--publish-viewer` 才会切换版本化 Release。
2. **缓存不是存档。** 临时计算缓存位于 `output/`，玩家存档位于 `saves/`；单独清理缓存不会删除玩家存档。“删除 Seed”则会在确认后删除该非 Release 槽位的缓存和存档。
3. **全球页面的场景推演不是正式 Run。** 它只在浏览器中改变观察情景；正式世界线始终来自 Python 模型链。

更完整的页面操作见 [用户指南](User_Guide.md)。启动失败时见 [故障排查](../development/Troubleshooting.md)。
