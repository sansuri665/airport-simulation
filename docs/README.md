# Airport 项目文档

这里保存项目当前有效的说明。文档按读者要解决的问题组织，不再按开发时间或版本演进堆叠。

如果文档与代码、配置、JSON Schema 或测试冲突，应先核实真实实现并修正文档。旧设计和被取代内容由 Git 保存，不在这里建立第二套历史归档。

## 我应该从哪里开始

### 想先理解这是什么项目

1. [游戏总体介绍](product/Game_Overview.md)
2. [游戏流程](product/Game_Flow.md)
3. [模型主链](models/Model_Pipeline.md)
4. [术语表](reference/Glossary.md)

### 想启动并使用界面

1. [快速开始](getting_started/Quick_Start.md)
2. [界面使用指南](getting_started/User_Guide.md)
3. [常见问题](development/Troubleshooting.md)

### 想理解模型

1. [模型主链](models/Model_Pipeline.md)
2. [全球宏观](models/Global_Macro.md)
3. [区域宏观](models/Regional_Macro.md)
4. [航空与城市机场市场](models/Aviation_and_City_Market.md)
5. [机场季度经营](models/Airport_Operations.md)
6. [财务、合同与项目](models/Finance_Contracts_and_Projects.md)

### 想修改或维护代码

1. [系统架构](architecture/System_Overview.md)
2. [本地服务与 Web](architecture/Runtime_and_Web.md)
3. [Run、缓存、存档与 Viewer 发布](architecture/Data_Cache_Save_and_Viewer.md)
4. [API 与数据契约](reference/API_and_Data_Contracts.md)
5. [测试与安全修改](development/Testing_and_Safe_Changes.md)
6. [文档维护规则](development/Documentation_Standard.md)

### 想把北京样板扩展到其它城市

1. [北京样板与新增完整经营城市指南](reference/Beijing_Template_and_New_City_Guide.md)
2. [航空与城市机场市场](models/Aviation_and_City_Market.md)
3. [机场经营参数参考](reference/Airport_Operations_Parameters.md)
4. [财务与估值参数参考](reference/Finance_and_Valuation_Parameters.md)
5. [测试与安全修改](development/Testing_and_Safe_Changes.md)

## 文档地图

### `getting_started/`

| 文档 | 说明 |
| --- | --- |
| [Quick_Start.md](getting_started/Quick_Start.md) | Python 3.13、启动、停止、Run 和缓存命令 |
| [User_Guide.md](getting_started/User_Guide.md) | 五个页面分别怎样使用，哪些页面只读，哪些可以操作 |

### `product/`

| 文档 | 说明 |
| --- | --- |
| [Game_Overview.md](product/Game_Overview.md) | 玩家身份、世界生成、季度循环、报表、目标与当前边界 |
| [Game_Flow.md](product/Game_Flow.md) | 玩家看到的信息、季度推进和决策关系 |

### `architecture/`

| 文档 | 说明 |
| --- | --- |
| [System_Overview.md](architecture/System_Overview.md) | 代码目录、模块职责和调用关系 |
| [Runtime_and_Web.md](architecture/Runtime_and_Web.md) | 8776 服务、页面路由、前后端和兼容入口 |
| [Data_Cache_Save_and_Viewer.md](architecture/Data_Cache_Save_and_Viewer.md) | 输出生命周期、原子写入、缓存、存档和 Viewer 发布 |

### `models/`

| 文档 | 说明 |
| --- | --- |
| [Model_Pipeline.md](models/Model_Pipeline.md) | 从全球宏观到机场财务的完整主链 |
| [Global_Macro.md](models/Global_Macro.md) | 全球增长、通胀、利率、信用、资产、商品和分岔 |
| [Regional_Macro.md](models/Regional_Macro.md) | 14 区路径、全球传导和区域对账 |
| [Aviation_and_City_Market.md](models/Aviation_and_City_Market.md) | 航空需求、航司供给、47 城市场和有效客流预测 |
| [Airport_Operations.md](models/Airport_Operations.md) | 北京机场季度容量、服务、收入和成本样板 |
| [Finance_Contracts_and_Projects.md](models/Finance_Contracts_and_Projects.md) | 财务、税务、贷款、商业合同和设施项目 |

### `reference/`

| 文档 | 说明 |
| --- | --- |
| [Glossary.md](reference/Glossary.md) | Seed、Run、客流、报表、缓存和存档等统一术语 |
| [Beijing_Template_and_New_City_Guide.md](reference/Beijing_Template_and_New_City_Guide.md) | 北京五层配置的迁移分类、新城市接入顺序和验收清单 |
| [API_and_Data_Contracts.md](reference/API_and_Data_Contracts.md) | HTTP API、JSON Schema、版本和兼容规则 |
| [Macro_Regional_Aviation_Parameters.md](reference/Macro_Regional_Aviation_Parameters.md) | 全球、区域和航空参数来源、单位与约束 |
| [Airport_Operations_Parameters.md](reference/Airport_Operations_Parameters.md) | 城市市场、季度需求、容量、服务和商业经营参数 |
| [Finance_and_Valuation_Parameters.md](reference/Finance_and_Valuation_Parameters.md) | 财务、贷款、税务和估值参数 |

### `development/`

| 文档 | 说明 |
| --- | --- |
| [Testing_and_Safe_Changes.md](development/Testing_and_Safe_Changes.md) | 固定 Seed、API、Schema、UI 和结构重构保护 |
| [Troubleshooting.md](development/Troubleshooting.md) | 端口、Python、缓存、页面和数据问题排查 |
| [Documentation_Standard.md](development/Documentation_Standard.md) | 文档归属、写法、更新和淘汰规则 |

### `plans/`

| 文档 | 说明 |
| --- | --- |
| [Roadmap.md](plans/Roadmap.md) | 唯一的未来工作清单；正式说明不混入待办事项 |

## 当前事实由什么决定

| 事实类型 | 首要来源 |
| --- | --- |
| 命令和运行入口 | `airport_sim/`、`airport_ui/`、根目录 BAT |
| 模型计算 | `macro_layers/` |
| 参数与版本 | `config/` |
| JSON 字段和兼容约束 | `schemas/` 与 API 实现 |
| 页面结构和交互 | `web/pages/`、`web/static/` |
| 回归保护 | `tests/` |
| 未来方向 | `plans/Roadmap.md` |

文档负责解释这些事实，但不替代它们。

## 当前项目边界

当前完整模型链覆盖全球宏观、14 区区域宏观、区域航空需求和供给、中国大陆 47 城市市场；机场季度经营、财务、合同、项目、融资和预测以北京为主要样板。其它城市的完整经营配置、正式游戏信息隔离、交易并购和更完整的商业谈判仍未实现。

具体限制写在各专题文档末尾；所有未来工作统一维护在 [Roadmap.md](plans/Roadmap.md)。
