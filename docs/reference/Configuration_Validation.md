# 配置清单与校验契约

本文记录 `config/` 下正式 JSON 的配置族、Schema、加载器/消费者和语义校验边界。目的不是改变模型参数，而是在模型启动前发现拼写、缺字段、越界、失效引用和不守恒等输入错误。

权威入口是：

```powershell
py -3.13 -m airport_sim validate-config
py -3.13 -m airport_sim validate-config --json
```

工作区当前共有 59 个 JSON、13 个配置族，均必须被登记并通过校验。CI 使用默认 `config/`，因此新增但未登记的 JSON 会以 `family_unclassified` 失败。

## 1. 配置族清单

| 配置族 | 文件 | Schema | 加载器或主要消费者 | 族级语义校验 |
| --- | ---: | --- | --- | --- |
| 机场版本 | 1 | `airport-version-record.schema.json` | `airport_sim/server/app.py` | 版本记录结构和未知字段 |
| 航司客群分配档案 | 1 | `airline-supply-component-allocation-catalog.schema.json` | `city_airport_market_demand_layer_sim.py` | Profile ID 唯一、默认 Profile 存在、五客群偏置为正 |
| 航司供给动态档案 | 1 | `airline-supply-dynamics-catalog.schema.json` | `city_airport_market_demand_layer_sim.py` | Profile/Modifier ID 唯一、字段白名单、合并后参数范围 |
| 城市机场市场 | 47 | `city-airport-market-config.schema.json` | `city_airport_market_demand_layer_sim.py`；宏观编排器间接消费 | 文件名与市场 ID、档案/目录引用、五客群权重 100%、Seed 范围、机场/槽位 ID、槽位角色与设施容量 |
| 城市机场财务 | 1 | `city-airport-financial-state-config.schema.json` | `city_airport_financial_state_layer_sim.py`、`airport_sim/server/app.py`；宏观编排器间接消费 | 市场/机场/槽位引用、资产和贷款 ID、初始设施一致、利率上下界、曲线顺序 |
| 经营参考默认值 | 1 | `city-airport-operations-reference-defaults.schema.json` | 当前供文档与配置校验引用 | 市场 ID 和基础结构；不作为运行时参数覆盖 |
| 经营参数模板 | 1 | `city-airport-operations-parameter-template.schema.json` | 当前供文档与配置校验引用 | 模板结构；不作为运行时参数覆盖 |
| 城市机场季度经营 | 1 | `city-airport-operations-config.schema.json` | `city_airport_quarterly_operations_layer_sim.py`、`airport_sim/server/app.py`；宏观编排器间接消费 | 模板/默认值/市场/设施引用、事件 ID、季度权重 1.0、时间线和曲线顺序 |
| 潜在客流预测 | 1 | `forecast-config.schema.json` | `forecast_system/profile_config.py`；预测层与宏观编排器消费 | 目录文件、市场、等级/叙事/修饰 ID、报告 ID、质量范围和预测期步长 |
| 城市机场估值 | 1 | `city-airport-valuation-config.schema.json` | `city_airport_valuation_forecast_layer_sim.py`；宏观编排器间接消费 | 市场引用、增长/利率/折现/不确定性上下界和曲线顺序 |
| 设施尺寸目录 | 1 | `facility-size-catalog.schema.json` | 城市市场层、季度经营层和本地服务 | Catalog ID、`empty`、尺寸/角色/模板引用、设计容量不超过最大容量 |
| 预测叙事档案 | 1 | `forecast-narrative-catalog.schema.json` | `forecast_system/profile_config.py` | Profile/Modifier ID 唯一、候选 Modifier 引用 |
| 预测报告等级档案 | 1 | `forecast-tier-catalog.schema.json` | `forecast_system/profile_config.py` | Profile ID 唯一、质量与信号捕获范围顺序 |

登记表的机器可读权威来源是 [`CONFIG_FAMILY_SPECS`](../../airport_sim/config_validation.py)。结构规则位于 [`schemas/`](../../schemas)，运行时和测试共同使用 [`schema_validation.py`](../../airport_sim/schema_validation.py)。

## 2. 校验层次

`validate-config` 按以下顺序运行：

1. JSON 语法、UTF-8、重复对象键和非有限数；
2. 配置族归类；
3. 对应 JSON Schema 的必填字段、类型、枚举、范围、数组唯一性和未知字段策略；
4. 同族及跨文件的 ID 唯一性和引用；
5. 适用的权重守恒、区间顺序、曲线严格递增、设施角色和派生容量；
6. 经营、财务与估值配置的共同时间线一致性。

校验器不重新计算模型输出，也不改写配置。通过校验只表示基础配置契约成立，模型或参数改动仍须运行固定 Seed、60 年契约和对应领域测试。

## 3. 错误格式

`--json` 输出版本为 `airport-config-validation-v2`。每个错误都含：

```json
{
  "path": "city_airport_markets/china_mainland/example.json",
  "code": "reference_not_found",
  "location": "$.airline_supply_model.dynamics_profile_id",
  "message": "unknown airline supply dynamics profile 'missing_profile'",
  "error": "reference_not_found at $.airline_supply_model.dynamics_profile_id: ..."
}
```

- `path` 定位文件；
- `location` 是文件内的 JSON 路径；
- `code` 供 CI 或工具稳定分类；
- `message` 供人阅读；
- `error` 保留单行兼容描述。

常见 `code` 包括 `json_syntax`、`duplicate_object_keys`、`family_unclassified`、`schema_validation`、`duplicate_id`、`reference_not_found`、`reference_type_mismatch`、`weight_balance`、`range_order`、`curve_order` 和 `derived_capacity`。

## 4. 新增或修改配置

修改现有配置时：

1. 保持它属于现有配置族并同步更新对应 Schema；
2. 先运行 `validate-config`，再运行消费该配置的模型测试；
3. 参数或模型语义有意变化时，另行升级版本并更新固定 Seed 基线，不能把它伪装成校验器修改。

新增配置族时必须同时加入：

1. `CONFIG_FAMILY_SPECS` 的唯一 glob、Schema 和消费者；
2. `schemas/` 下带唯一 `$id` 的 Draft 2020-12 Schema；
3. `config_validation.py` 中需要的跨文件或守恒规则；
4. 至少一个有效例和一个失败反例测试；
5. 本文清单。

自定义 `--config-root` 默认允许未登记 JSON，以兼容局部语法检查；工作区默认目录和自动测试使用严格归类。若在 Python 中验证完整副本，应调用 `validate_config_tree(root, require_classified=True)`。
