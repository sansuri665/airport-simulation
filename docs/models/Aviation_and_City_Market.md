# 区域航空与城市机场市场

## 它解决什么问题

宏观增长不等于机场实际客流。本模型把区域经济逐步转换为：

1. 区域居民和企业想产生的航空旅行；
2. 区域航司体系能够提供的运力；
3. 某个城市能够吸引的潜在旅客；
4. 该城市的航司供给和机场设施最终能服务的旅客。

这几层刻意分开，因为“有人想坐飞机”“航司有座位”和“机场有航站楼容量”是三件不同的事。

```text
对账后的区域宏观
  → 区域航空潜在需求
  → 区域航司运力与满足率
  → 城市潜在客流
  → 城市航司供给
  → 机场设计/极限容量
  → 城市实际承接客流
```

## 共同输入与时间口径

三层都按年度运行，沿用同一个 `seed`、`year_index`、年份和岔路状态。默认 60 年 Run 会为每个区域和每个城市市场生成 61 行年度数据。

区域航空覆盖与区域宏观完全相同的 14 个区域。城市机场市场目前有 47 个，全部位于 `china_mainland`；城市配置由 [`config/city_airport_markets/china_mainland/`](../../config/city_airport_markets/china_mainland/) 下的 JSON 提供。

## 第一层：区域航空潜在需求

### 输入

[`regional_aviation_demand_layer_sim.py`](../../macro_layers/regional_aviation_demand_layer_sim.py) 合并区域原始宏观和对账结果，重点读取：

- 对账后 GDP 增长和区域 GDP 体量；
- 实际收入增长、收入指数和消费者信心；
- 通胀、能源成本、汇率压力、宏观压力和高收益信用利差；
- 股票回报、估值、财富效应和风险偏好；
- 区域 seed 的增长、航空倾向、投资、开放度和需求乘数；
- 全球岔路传到该区域后的冲击字段。

### 处理

航空需求固定分为五类，14 个区域的五项基础权重都合计为 1：

| 客群 | 含义 | 主要敏感因素 |
| --- | --- | --- |
| `business` | 商务 | GDP、信心、信用、资产和企业环境 |
| `leisure` | 休闲旅游 | 收入、信心、票价、油价和汇率 |
| `vfr` | 探亲访友 | 收入、票价和汇率，波动通常较小 |
| `long_haul` | 长航程 | 收入、国际开放、油价、汇率和商务环境 |
| `transfer` | 中转 | 枢纽权重、开放度、航线环境和槽位压力 |

各客群从 100 点起步。模型先计算本年度客群增长，再用惯性平滑并累积为需求指数；总需求指数是五类指数的区域权重加总。它同时计算票价压力、不同客群的票价弹性、高端旅客倾向，以及免税、奢侈品、电子产品、餐饮和普通零售倾向。

消费倾向指数只表示客群结构对商业的有利程度，不是销售额，也不包含机场合同或租金条款。

### 输出

关键结果包括：

- `regional_air_demand_index` 和年度增长率；
- 五类客群的需求指数、增长和份额；
- `airfare_price_sensitivity_index`、`airfare_pressure_index` 和票价弹性；
- 高端旅客份额及五类商业倾向；
- `aviation_demand_regime`、机场事件提示和上游解释字段。

## 第二层：区域航司运力

### 输入与处理

[`regional_air_capacity_supply_layer_sim.py`](../../macro_layers/regional_air_capacity_supply_layer_sim.py) 读取上一层的潜在需求、客群份额、票价压力以及宏观压力。每区还有一个“基准区域旅客量”和供给参数，用于把指数转换为百万人次。

模型根据需求增长、供需缺口、航司信心、盈利压力、信用融资、油价、机队交付、机组人员、维修和机场时刻约束，形成目标运力增长。实际运力带有惯性，并受本区年度扩张/收缩上限约束。

重要公式口径是：

```text
区域潜在旅客量
  = 区域基准旅客量 × 区域需求指数 / 100

区域承接旅客量
  = 区域潜在旅客量 × 航司供给满足率
```

供给紧张时，五类客群不会同比例被挤出。商务通常更抗压，休闲通常更容易受票价和容量影响；具体差异来自区域参数。

### 输出

- 运力指数、运力增长、可用座位和载客率；
- 区域潜在、承接和未满足旅客量，单位为百万人次；
- 总体及五类客群的满足率；
- 航司信心、盈利压力、机队/航线扩张意愿；
- 机队交付、人员、维修和时刻约束指数；
- `supply_regime` 和上游解释字段。

这里的机场时刻约束只是区域航司供给压力之一，**不是**某个城市机场的航站楼硬容量。

## 第三层：城市机场市场

### 配置输入

[`city_airport_market_demand_layer_sim.py`](../../macro_layers/city_airport_market_demand_layer_sim.py) 读取区域航空需求、区域航司供给和区域宏观，同时加载每个城市 JSON。城市配置定义：

- 城市和机场系统身份、市场等级与类型；
- 起始潜在客流和长期增长偏置；
- 五类客群基础份额与城市偏置；
- 城市航司供给基准、区域运力捕获率、调整速度和波动；
- 城市 seed 势能模板；
- 高端旅客与商业倾向偏置；
- 机场、航站楼槽位、设施规格和启用年份。

当前 47 个城市的五类基础份额都合计为 100%，也都启用了城市 seed 势能。seed 势能会在若干年后逐步释放，并接受区域环境对齐修正；它改变长期潜在客流，不直接增加航司或航站楼容量。

### 城市潜在客流

城市潜在客流以城市 JSON 的 `baseline_city_potential_passengers_million` 为体量锚，再叠加：

```text
固定长期增长偏置
× 城市 seed 势能乘数
× 五类客群的区域航空和宏观指数
```

`baseline_region_demand_share_pct` 目前用于比较“当年计算出的城市份额”与配置参考值，并输出 `city_share_adjustment_pp`；它不是把区域旅客量按固定比例直接分配给城市的公式参数。

### 城市航司供给

城市航司供给有独立的基准客流和年度状态。目标供给由城市潜在客流锚、区域运力增长、航司信心/扩张意愿、运营约束、确定性周期、seed 冲击和岔路事件共同决定；实际供给再按上一年状态逐步追向目标。

因此，城市需求上升后，航司可以滞后扩张；压力年份也可以先收缩再恢复。五类客群会共享同一个供给总量，再按客群需求和航司偏好重新分配，分项不会额外创造总供给。

### 机场设施容量

机场容量来自 [`standard_terminal_sizes_v1.json`](../../config/facility_size_catalogs/standard_terminal_sizes_v1.json)。只有 `open_year` 已到、且规格不为 `empty` 的槽位会计入当年容量。

| 规格 | 设计容量 | 极限容量 |
| --- | ---: | ---: |
| `small` | 8 | 12 |
| `medium` | 16 | 24 |
| `large` | 32 | 45 |
| `extra_large` | 50 | 65 |
| `giant` | 72 | 90 |

单位均为百万人次/年。设计容量用于判断舒适度和拥挤；极限容量是当前客流硬上限。主槽位、次槽位和辅助槽位可选的最大规格不同，城市配置加载时会验证这些规则。

### 最终承接客流

当前城市年度承接口径可以简化为：

```text
城市实际承接客流
  = min(城市潜在客流, 城市航司供给, 当年机场极限容量)
```

模型同时输出 `demand_limited`、`airline_bottleneck`、`airport_bottleneck` 或双重瓶颈，以及潜在、航司供给、设计容量、极限容量、承接和未满足客流。这些字段是后续季度经营和玩家扩建决策的输入。

## 输出位置

完整 Run 中的目录为：

```text
output/macro_runs/<run_id>/<variant>/regional_aviation_demand/<region_id>/
output/macro_runs/<run_id>/<variant>/regional_air_capacity_supply/<region_id>/
output/macro_runs/<run_id>/<variant>/city_airport_market_demand/<region_id>/
```

每层都有逐年 CSV 和摘要 JSON；`full` 产物模式还会生成 Viewer 数据。主要数量与单位：

| 后缀或名称 | 含义 |
| --- | --- |
| `_index` | 无量纲内部指数，必须结合该字段自己的基准解释 |
| `_pct` | 百分比或年增长率；`_pp` 才表示百分点差 |
| `_million` | 百万人次 |
| `load_factor_pct` | 旅客量相对座位的载客率 |
| `fulfillment_pct` | 需求中被供给或容量满足的比例 |
| `design_capacity_million` | 正常经营容量 |
| `max_capacity_million` | 当前设施的硬上限 |

## 与下游模块的关系

- 城市潜在客流可被玩家可见的预测报告读取，但隐藏真实未来不等于玩家一定能看到的预测。
- 城市承接客流、客群、拥挤和容量进入季度经营。
- 季度经营再进入财务状态和估值；本模型本身不计算收入、利润、债务或企业价值。
- 目前 47 个城市都能生成年度城市市场，但潜在客流预测、季度经营、财务和估值配置只覆盖北京样板；其余 46 个城市会在 Run 的 `city_airport_downstream_skips.json` 中记录缺少下游配置。

把现有城市扩展为完整模型城市时，应按[北京样板与新增完整经营城市指南](../reference/Beijing_Template_and_New_City_Guide.md)补齐五层配置并分别验收模型链和可玩界面。

## 真实代码、配置和验证位置

- 区域航空需求与 14 区参数：[`regional_aviation_demand_layer_sim.py`](../../macro_layers/regional_aviation_demand_layer_sim.py)
- 区域航司供给与 14 区参数：[`regional_air_capacity_supply_layer_sim.py`](../../macro_layers/regional_air_capacity_supply_layer_sim.py)
- 城市市场公式和配置加载：[`city_airport_market_demand_layer_sim.py`](../../macro_layers/city_airport_market_demand_layer_sim.py)
- 47 个城市 JSON：[`config/city_airport_markets/china_mainland/`](../../config/city_airport_markets/china_mainland/)
- 航站楼规格：[`standard_terminal_sizes_v1.json`](../../config/facility_size_catalogs/standard_terminal_sizes_v1.json)
- 一键串联和输出：[`macro_run_orchestrator_sim.py`](../../macro_layers/macro_run_orchestrator_sim.py)
- 14 区、47 城和 60 年数量契约：[`test_long_horizon_contract.py`](../../tests/test_long_horizon_contract.py)
- 固定 seed 数值基线：[`test_safety_baseline.py`](../../tests/test_safety_baseline.py)

## 当前限制

- 区域航空需求和供给参数仍内嵌在 Python；只有城市市场和设施规格使用 JSON 配置。
- 需求与供给是大区汇总，没有机场对机场航线网络、票价舱位、航空公司主体或机队机型。
- 区域供给满足率代码当前设有 68% 的下限，五类客群满足率也各有下限；这是稳定性保护，会压低极端短缺的尾部幅度。
- 城市层不是把区域总客流做守恒分摊；各城市以自己的基准潜在客流计算，因此 47 城市潜在客流之和不保证等于中国大陆区域总量。
- 区域承接旅客量会作为解释字段和供给环境进入城市层，但不会直接按固定份额成为城市实际客流上限。
- 机场容量当前只按年度启用的设施规格求和，没有跑道、小时峰值、天气、空域、安检或地面保障的独立硬约束。
- 47 城配置只有 `schema_version` 过滤和运行时字段/槽位验证，尚无独立 JSON Schema 文件。
