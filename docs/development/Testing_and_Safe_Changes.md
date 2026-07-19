# 测试与安全修改

## 1. 支持环境

项目唯一支持并用于 CI 的版本是 Python 3.13。运行依赖只有标准库；本地命令以下均假设当前目录是 `airport`。

```powershell
py -3.13 --version
```

`pyproject.toml` 要求 `>=3.13,<3.14`。使用其他 Python 得到的“测试通过”不能替代 3.13 验收。

## 2. 完整验收命令

```powershell
py -3.13 -m compileall -q airport_sim macro_layers tests
py -3.13 tools/check_markdown_links.py
py -3.13 tools/check_javascript_syntax.py
py -3.13 -m airport_sim validate-config
py -3.13 -B -m unittest discover -s tests -v
git diff --check
```

JavaScript 语法检查需要 Node.js；它只用于前端静态验证，不是运行机场模型或本地服务的依赖。CI 显式安装 Node.js 22，本地未加入 PATH 时可向脚本传入 `--node` 指定可执行文件。

CI 会在 Windows 和 Linux 上安装当前项目的 editable package，再执行相同的语法、入口、配置和完整测试检查。

## 3. 自动化保护了什么

| 测试领域 | 代表文件 | 主要保护 |
|---|---|---|
| 固定 Seed 数值 | `test_safety_baseline.py` | 九组数值摘要、Python 3.13 浮点口径、IO 细节 |
| 长期模型 | `test_long_horizon_contract.py` | 60 年情景、14 区、47 城、CSV 表头和玩家融资回放 |
| 区域与城市权责 | `test_regional_air_supply_boundaries.py` | 区域承接量只作参考，不成为城市客流硬上限 |
| 客群航司供给 | `test_component_airline_allocation.py` | 总量守恒、单客群上限、商务/休闲差异及年度—季度—预测一致性 |
| 预测报告叙事 | `test_forecast_narrative_model.py` | 8 种共享风格、四类标签、中文元数据、非数值伴飞、报告继承、神级精确与玩家/审计隔离 |
| 城市航司周期 | `test_airline_supply_dynamics_profiles.py` | 47 城模板、经营阶段、过剩/波谷分布、年度调节上限和空置运力边界 |
| 正式 Run、生命周期、变体产物与 staged 校验 | `test_atomic_run.py`、`test_orchestrator_run_lifecycle_service.py`、`test_orchestrator_variant_outputs_service.py`、`test_orchestrator_run_validation_service.py` | 参数拒绝、index-only、Run/staging 命名、重复拒绝、失败清理边界、发布/索引/Manifest 顺序、11 类 CSV 字段/路径和 full/seed-cache 写入顺序、摘要/skip、CSV 校验与原子正式化 |
| 编排器发布、资产与索引 | `test_orchestrator_release_index_services.py`、`test_orchestrator_viewer_assets_service.py`、`test_viewer_release.py` | 高层正式化/下游 CSV/Manifest 指针顺序、Release-only 必需资产、浏览器 canonical 禁止、URL/SHA-256/确定性 gzip，以及 Run JSON 索引排序、过滤和标签 |
| API 与文件协议 | `test_api_snapshot.py`、`test_local_ui.py`、`test_server_routes.py`、`test_http_file_response.py`、`test_cache_save_api_schemas.py`、`test_seed_workspace_service.py`、`test_seed_workspace_actions.py`、三个 `test_*_context_service.py` | 固定 Seed JSON、34 个公开路由、统一 Seed 读取与安全写操作、三个 Viewer 的缓存只读上下文、缓存清单、存档四动作、已退役路由的 404、请求边界、流式响应、ETag/304、缓存分层和 gzip 协商 |
| 预测候选与工作区 | `test_forecast_workspace_services.py`、`test_forecast_viewer_context_service.py`、`test_forecast_candidate_generator.py` | 显式 Release/缓存来源、玩家/审计隔离、防隐式回退、候选请求规范化、缓存/存档计数和相对路径 |
| Schema 与配置 | `test_json_schemas.py`、`test_cache_save_api_schemas.py`、`test_config_validation.py` | 2020-12 Schema、真实响应/Manifest、缓存与存档对象/响应，以及 59 份配置的结构、范围、引用、守恒和曲线契约 |
| Run、缓存、北京经营、玩家服务与存档 | `test_run_cache_service.py`、`test_beijing_operations_service.py`、`test_player_simulation_service.py`、`test_player_action_domains.py`、`test_cache_service.py`、`test_safety_baseline.py` | 缓存命中/锁内复查/执行顺序、北京字段/舍入/空值/财务配对/警告、replay 重试、玩家存档序列化、行动顺序/覆盖/拒绝、项目冷却和冻结配置、两层命令、失败 Manifest、指纹协议和保留 |
| 后台任务 | `test_background_jobs.py` | 去重、状态、活动上限和错误裁剪 |
| Viewer 发布 | `test_viewer_release.py` | 数据包哈希、gzip 旁车、下游 CSV 同步、无 canonical 浏览器副本、失败时不切换指针 |
| 按需加载 | 三个 `test_*_lazy_loading.py` | 报告/区域/城市分块、哈希、玩家/审计隔离、Release/缓存双来源与必需索引 |
| 前端结构与 Seed 上下文 | `test_viewer_smoke.py`、`test_viewer_dom_contract.py`、`test_seed_context_contract.py` | 资源存在、脚本顺序、关键 DOM `id` 唯一、四页共用固定 URL 上下文、旧 Seed 控件退出、全球场景模块显式消费者 |
| 包与命令 | `test_airport_sim_cli.py`、`test_package_imports.py` | 唯一统一入口和任意工作目录导入 |

DOM 契约不检查颜色、尺寸、布局和图表视觉效果。涉及页面布局、图表或交互的修改仍要做真实浏览器验收。

## 4. 按修改类型选择最小检查

完整测试是交付前标准；开发中可以先运行相关模块缩短反馈时间。

### 仅文档

- 检查命令、路径、URL 和相对链接是否存在；
- 运行 `git diff --check`；
- 若文档声称了具体运行行为，用对应测试或代码再次核对。

### 前端页面或静态资源

```powershell
py -3.13 -B -m unittest tests.test_viewer_smoke tests.test_viewer_dom_contract -v
py -3.13 -B -m unittest tests.test_global_viewer_lazy_loading tests.test_city_market_viewer_lazy_loading tests.test_forecast_lazy_loading -v
```

之后启动 8776，在浏览器实际打开五个页面，切换受影响的按钮、报告、区域和图表，并检查控制台错误。

### 服务、路由或 API

```powershell
py -3.13 -B -m unittest tests.test_forecast_workspace_services tests.test_beijing_operations_service tests.test_player_action_domains tests.test_player_simulation_service tests.test_local_ui tests.test_api_snapshot tests.test_json_schemas tests.test_background_jobs -v
```

若字段发生变化，还必须更新 Schema、固定 Seed 快照和前端读取逻辑；不能只改其中一处。

### 缓存、存档、路径或发布

```powershell
py -3.13 -B -m unittest tests.test_cache_save_api_schemas tests.test_orchestrator_run_lifecycle_service tests.test_orchestrator_variant_outputs_service tests.test_orchestrator_run_validation_service tests.test_orchestrator_viewer_assets_service tests.test_orchestrator_release_index_services tests.test_run_cache_service tests.test_cache_service tests.test_atomic_run tests.test_viewer_release tests.test_safety_baseline -v
```

测试应使用临时目录，不要把 smoke/test 产物写进正式 `output/` 或 `saves/`。

### 模型、参数或随机逻辑

至少运行固定 Seed 数值、60 年契约和完整套件。若变化是有意的模型升级，应先写清版本与迁移计划；不能通过直接更新摘要来掩盖无意漂移。

航空与城市供给相关修改可先运行：

```powershell
py -3.13 -B -m unittest tests.test_regional_air_supply_boundaries tests.test_component_airline_allocation tests.test_airline_supply_dynamics_profiles -v
```

城市年度市场是五类客群可承接供给的权威来源。季度经营与预测只能读取或拆分这套结果；过剩投放只能形成 `unused_capacity`，不能增加潜在客流、单客群上限或机场实际承接量。

客流预测模型修改还应运行：

```powershell
py -3.13 -B -m unittest tests.test_forecast_narrative_model tests.test_forecast_lazy_loading tests.test_safety_baseline -v
```

普通报告不得重新读取目标年份真实数值；玩家分块不得包含 `debug_*`、`realized_*` 或神级报告。审计分块必须继续保留城市客群权威真值和完整评分。

## 5. 不改变结果的安全重构规则

1. 先记录现有固定 Seed 测试结果，再移动代码。
2. 机械搬移和业务逻辑修改分成不同步骤。
3. 不改变随机数对象、调用次数、循环与排序顺序。
4. 不改变浮点运算、舍入、缺失值和 CSV 字段顺序。
5. 不统一看似相同但语义不同的 helper。
6. 新服务模块必须加入缓存指纹依赖，避免旧缓存被误用。
7. 写 Run、缓存、存档和 Viewer 指针时保留 staging/临时文件加原子替换。
8. 缓存清理与玩家存档删除永远分开授权。
9. API 保持向后兼容时只增加可选字段；不兼容变更必须升级版本。
10. 已声明退役的入口必须从代码、包配置、Schema、测试和文档同时删除。

## 6. 配置修改

修改 `config/` 后先运行：

```powershell
py -3.13 -m airport_sim validate-config
```

该命令严格归类工作区的 59 份配置，并检查 JSON 语法、重复对象键、Schema、字段范围、ID/跨文件引用、适用的权重守恒、曲线顺序和派生设施容量。错误同时给出文件、错误代码和 JSON 路径；`--json` 可输出机器可读报告。完整清单和扩展规则见[配置清单与校验契约](../reference/Configuration_Validation.md)。

该命令不重新计算模型结果，也不能代替消费该配置的模型测试与固定 Seed 契约。

参数的权威来源是配置文件和读取它的 Python 代码。文档中的示例范围用于解释，不能覆盖实际代码。

## 7. 浏览器验收清单

启动：

```powershell
py -3.13 -m airport_sim serve --host 127.0.0.1 --port 8776
```

至少检查：

1. `/` 显示服务正常与 Viewer 发布元数据。
2. 首页经营入口携带 `seed + years`；`/seed-explorer` 无页内 Seed 控件，能按固定上下文后台生成或读取缓存并显示城市图表。
3. 北京运营的“加载历史”和“模拟运营”含义没有互换。
4. 经营报告受影响的图表、表格和季度切换正常。
5. 首页全球入口携带 `seed + years`；`/global-gdp` 对发布槽位读取 Release、对有效缓存槽位读取上下文 API，能切换全球/区域/航空视图，区域块按槽位隔离并按需加载；页面不再有 Seed 下拉框或随机 Seed 按钮。
6. 首页城市入口携带 `seed + years`；`/city-markets` 对发布槽位读取 Release、对有效缓存槽位读取上下文 API，能筛选城市、切换年份并按需加载需求/航司供给与客群状态；页面不显示机场容量和最终经营承接。
7. 首页预测入口携带 `seed + years`；`/beijing-forecast` 对发布槽位读取 Release、对有效缓存槽位读取上下文 API，默认只加载玩家报告；切换开发审计后才加载独立审计索引、真实曲线、神级报告和绑定同一来源的候选实验室。页面无 Seed 下拉框，报告内存缓存按槽位、来源、revision 和信息层级隔离。
8. 浏览器控制台没有新的 error，服务终端没有未处理异常。
9. 旧 `*.html`、`/beijing-operations` 和旧存档 API 地址返回 404，不重新引入第二套路由。
10. 双标签切换首页活动 Seed 时，已打开经营页只提示 revision 变化，不静默切换 URL 或数据。
11. 已打开城市页同样固定 URL 和内存分块缓存；另一个标签页切换 Seed 后只显示提示，不混入新 Seed 城市块。
12. 已打开全球页同样固定 URL 和区域内存缓存；另一个标签页切换 Seed 后只显示提示，不回退或混入当前 Release。
13. 已打开预测页同样固定 URL；另一个标签页切换 Seed 后只显示提示，玩家报告响应不包含审计真值，候选目录与生成响应的来源身份一致。

## 8. 交付前检查

- `git status` 只包含本次范围内的源码和文档；
- 不提交 `output/`、`saves/`、`__pycache__/` 等生成物；
- 所有新增真实文件路径都有对应文档或入口更新；
- 完整 Python 3.13 测试通过；
- 涉及 UI 时完成浏览器验收；
- 涉及数值时明确说明结果是保持不变还是有意升级。
