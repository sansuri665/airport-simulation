# 测试与安全修改

## 1. 支持环境

项目唯一支持并用于 CI 的版本是 Python 3.13。运行依赖只有标准库；本地命令以下均假设当前目录是 `airport`。

```powershell
py -3.13 --version
```

`pyproject.toml` 要求 `>=3.13,<3.14`。使用其他 Python 得到的“测试通过”不能替代 3.13 验收。

## 2. 完整验收命令

```powershell
py -3.13 -m compileall -q airport_sim airport_ui macro_layers dynamic_tests tests
py -3.13 -m airport_sim validate-config
py -3.13 -B -m unittest discover -s tests -v
git diff --check
```

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
| 正式 Run | `test_atomic_run.py` | staging、校验、失败清理、版本记录和原子正式化 |
| API | `test_api_snapshot.py`、`test_local_ui.py` | 固定 Seed JSON、路由、请求边界和服务状态 |
| Schema | `test_json_schemas.py` | 2020-12 Schema、真实响应、Manifest 与预测配置/等级/风格目录 |
| 缓存与存档 | `test_cache_service.py`、`test_safety_baseline.py` | 指纹、保留、固定、清理保护和旧存档迁移 |
| 后台任务 | `test_background_jobs.py` | 去重、状态、活动上限和错误裁剪 |
| Viewer 发布 | `test_viewer_release.py` | 数据包哈希、兼容复制、失败时不切换指针 |
| 按需加载 | 三个 `test_*_lazy_loading.py` | 报告/区域/估值分块、哈希、玩家/审计隔离与必需索引 |
| 前端结构 | `test_viewer_smoke.py`、`test_viewer_dom_contract.py` | 资源存在、脚本顺序、关键 DOM `id` 唯一 |
| 包与命令 | `test_airport_sim_cli.py`、`test_package_imports.py` | 统一入口、兼容包装和任意工作目录导入 |

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
py -3.13 -B -m unittest tests.test_local_ui tests.test_api_snapshot tests.test_json_schemas tests.test_background_jobs -v
```

若字段发生变化，还必须更新 Schema、固定 Seed 快照和前端读取逻辑；不能只改其中一处。

### 缓存、存档、路径或发布

```powershell
py -3.13 -B -m unittest tests.test_cache_service tests.test_atomic_run tests.test_viewer_release tests.test_safety_baseline -v
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
10. 旧入口先变为薄包装并通过兼容测试，再考虑移除。

## 6. 配置修改

修改 `config/` 后先运行：

```powershell
py -3.13 -m airport_sim validate-config
```

该命令检查全部配置 JSON 的语法和重复对象键。它不会验证所有模型参数的业务范围，因此还要运行使用该配置的模型测试与固定 Seed 契约。

参数的权威来源是配置文件和读取它的 Python 代码。文档中的示例范围用于解释，不能覆盖实际代码。

## 7. 浏览器验收清单

启动：

```powershell
py -3.13 -m airport_sim serve --host 127.0.0.1 --port 8776
```

至少检查：

1. `/` 显示服务正常与 Viewer 发布元数据。
2. `/seed-explorer` 能生成随机 Seed、运行或读取缓存、显示城市图表。
3. 北京运营的“加载历史”和“模拟运营”含义没有互换。
4. 经营报告受影响的图表、表格和季度切换正常。
5. `/global-gdp` 能切换全球/区域/航空视图，区域块按需加载。
6. `/city-markets` 能筛选城市、切换年份，并按需加载需求/航司供给三口径趋势、客群与供给状态；页面不显示机场容量和最终经营承接；`/beijing-operations` 正确重定向到该页。
7. `/beijing-forecast` 默认只加载玩家报告，能切换 12 份报告、发布年份和六种客流口径；切换开发审计后再加载独立审计索引、真实曲线和神级报告。
8. 浏览器控制台没有新的 error，服务终端没有未处理异常。
9. 旧 `*.html` 地址仍可访问，除非本次变更明确结束兼容并有迁移方案。

## 8. 交付前检查

- `git status` 只包含本次范围内的源码和文档；
- 不提交 `output/`、`saves/`、`__pycache__/` 等生成物；
- 所有新增真实文件路径都有对应文档或入口更新；
- 完整 Python 3.13 测试通过；
- 涉及 UI 时完成浏览器验收；
- 涉及数值时明确说明结果是保持不变还是有意升级。
