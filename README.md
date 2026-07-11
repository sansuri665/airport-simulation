# Airport Simulation Workspace

这是一个使用 Python 3.13 运行的机场经营模拟项目。它把全球经济、区域经济、航空需求、航司运力、中国大陆城市机场市场，以及北京机场的季度经营和财务样板连接成一条可重复计算的模型链。

项目目前同时提供：

- 完整模型 Run；
- 全球宏观、北京经营和有效客流预测 Viewer；
- 可按 Seed 运行并按季度查看北京机场经营的动态测试；
- 独立玩家存档、临时 Run 缓存和版本化 Viewer 发布。

## 最快启动方式

Windows 用户双击：

```text
start_airport_ui.bat
```

浏览器会打开仅限本机访问的统一工作台：

```text
http://127.0.0.1:8776/
```

停止服务可以关闭启动窗口、按 `Ctrl+C`，或运行：

```text
stop_airport_ui.bat
```

命令行启动方式：

```powershell
py -3.13 -m airport_sim serve
```

项目只支持 Python 3.13；其它 Python 版本不属于当前测试范围。

## 主要页面

| 地址 | 用途 |
| --- | --- |
| `http://127.0.0.1:8776/` | 统一首页和运行状态 |
| `http://127.0.0.1:8776/seed-explorer` | 城市市场与北京机场动态测试 |
| `http://127.0.0.1:8776/global-gdp` | 全球和区域宏观 Viewer |
| `http://127.0.0.1:8776/beijing-operations` | 北京机场经营 Viewer |
| `http://127.0.0.1:8776/beijing-forecast` | 北京有效客流预测 Viewer |

旧的 `*.html` 地址和 Seed Explorer 启动脚本仍保留兼容，但正式入口以上表为准。

## 模型主链

```text
全球宏观
  -> 历史分岔与情景
  -> 14 个区域宏观路径
  -> 区域航空需求
  -> 航司运力与供给满足率
  -> 中国大陆 47 城市机场市场
  -> 北京机场季度经营
  -> 财务、税务、贷款、合同、项目与估值观察
```

有效客流预测是玩家的信息层：它根据真实城市市场结果生成带误差和审计分的预测报告，但不会反过来改变真实客流。

完整关系见 [模型主链](docs/models/Model_Pipeline.md)。

## 常用命令

生成随机 Seed 的完整 Run：

```powershell
py -3.13 -m airport_sim run --random-seed
```

生成固定 Seed 和指定情景：

```powershell
py -3.13 -m airport_sim run --seed 20260630 --scenario-state occurred --scenario-branch-id auto
```

同时发布 Viewer 数据：

```powershell
py -3.13 -m airport_sim run --seed 20260630 --publish-viewer baseline
```

查看缓存而不删除内容：

```powershell
py -3.13 -m airport_sim cache list
py -3.13 -m airport_sim cache plan
```

运行全部自动化测试：

```powershell
py -3.13 -m unittest discover -s tests -q
```

更多命令和故障处理见 [快速开始](docs/getting_started/Quick_Start.md) 与 [常见问题](docs/development/Troubleshooting.md)。

## 目录说明

| 目录 | 内容 |
| --- | --- |
| `airport_sim/` | 正式命令行、缓存管理、Viewer 发布和 8776 服务 |
| `macro_layers/` | 全球、区域、航空、城市和机场模型实现 |
| `config/` | 模型参数、区域配置、机场经营和版本配置 |
| `schemas/` | 正式 JSON Schema |
| `web/pages/` | 五个 HTML 页面 |
| `web/static/` | 页面 CSS 和 JavaScript |
| `tests/` | 固定 Seed、API、Schema、UI 和安全回归测试 |
| `output/` | 可重新生成的 Run、缓存和 Viewer 数据 |
| `saves/` | 玩家主动保存的动态经营进度 |
| `docs/` | 当前项目说明 |
| `dynamic_tests/` | 动态测试兼容入口；正式服务不在这里 |
| `airport_ui/` | 统一 UI 兼容入口 |

`output/` 可以按规则清理和重建；`saves/` 是独立玩家存档，不应当作普通缓存删除。

## 文档入口

从 [文档总览](docs/README.md) 开始。推荐顺序：

1. [游戏总体介绍](docs/product/Game_Overview.md)
2. [游戏流程](docs/product/Game_Flow.md)
3. [快速开始](docs/getting_started/Quick_Start.md)
4. [模型主链](docs/models/Model_Pipeline.md)
5. [系统架构](docs/architecture/System_Overview.md)
6. [术语表](docs/reference/Glossary.md)

如果准备把北京样板扩展到其它城市，先阅读 [北京样板与新增完整经营城市指南](docs/reference/Beijing_Template_and_New_City_Guide.md)。

## 当前边界

- 全球、区域、航空和中国大陆城市市场已经形成完整模拟链。
- 机场季度经营、财务、合同、项目和融资以北京为主要可操作样板。
- Viewer 主要用于查看已经发布的结果；Seed Explorer 用于动态测试。
- 其它城市的完整经营配置、正式游戏信息隔离、商业谈判、交易和并购仍属于未来工作。

尚未实现的内容只在 [路线图](docs/plans/Roadmap.md) 中维护，正式说明不再混入历史进度流水账。
