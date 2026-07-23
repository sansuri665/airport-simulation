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

各客群从 100 点起步。区域需求 v0.3 先用潜在增长、增长 surprise、收入、信心、信用和共同票价/事件冲击计算总量增长，再计算五类客群的相对调整；相对调整按区域基期权重中心化，因此纯结构变化在当期不改变加权总量。票价弹性已经真实进入对应客群，地缘政治按相对中性点影响长途和中转，不再用绝对水平机械压低中转。最终目标增长只用 `demand_adjustment_speed` 平滑一次并累积为需求指数，总需求指数仍是五类指数的区域权重加总。

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

模型根据需求增长、供需缺口、航司信心、盈利压力、信用融资、油价、机队交付、机组人员、维修和机场时刻约束，形成目标运力增长。实际运力带有惯性，并受本区年度扩张/收缩上限约束。这里形成的是供城市模型使用的区域景气、趋势和压力信号，不负责给某个城市分配客流硬上限。

重要公式口径是：

```text
区域潜在旅客量
  = 区域基准旅客量 × 区域需求指数 / 100

区域计划座位
  = 区域基准旅客量 ÷ 初始载客率 × 区域运力指数 / 100

区域可运营座位
  = 区域计划座位 × 运营可用率

区域参考有效承接能力
  = 区域可运营座位 × 可实现载客率

区域参考承接旅客量
  = min(区域潜在旅客量, 区域参考有效承接能力)
```

“可实现载客率”吸收了区域总座位与具体航线、时段不能完全匹配的影响。供给紧张时，五类客群不会同比例被挤出；商务通常更抗压，休闲通常更容易受票价和容量影响，具体差异来自区域参数。

### 输出

- 运力指数、运力增长、可用座位和载客率；
- 区域潜在、参考承接和参考未满足旅客量，单位为百万人次；
- 总体及五类客群的满足率；
- 航司信心、盈利压力、机队/航线扩张意愿；
- 机队交付、人员、维修和时刻约束指数；
- `supply_regime` 和上游解释字段。

这里的机场时刻约束只是区域航司供给压力之一，**不是**某个城市机场的航站楼硬容量。区域 `reference_*_passengers_million` 也只是诊断和解释值，不会限制城市潜在客流、城市航司供给或机场承接量。旧字段 `served_passengers_million` 和 `unmet_passengers_million` 暂时作为兼容别名保留。

### 当前数量语义：reference-only

当前实现没有旅程网络，也没有在唯一旅客、OD 旅次、航段旅客量和机场处理人次之间做数量转换。因此，区域百万人次参考量与城市百万人次体量虽然单位后缀相同，**仍不是可跨层加总或守恒的同一种事实量**：

| 术语 | 当前含义 |
| --- | --- |
| 唯一旅客 | 统计期内去重的人；当前模型不生成此实体 |
| OD 旅次 | 从最终起点到最终目的地的一次旅程；当前模型不生成此实体 |
| 航段旅客量 | 每乘坐一个航段计一次；当前模型不生成航段网络 |
| 机场处理人次 | 机场对旅客的一次处理计数；中转计一次还是两次尚未冻结 |
| 城市潜在客流 | 城市本地配置锚生成的模型体量，不从区域参考量分配 |
| 航司投放能力 | `city_airline_offered_capacity_million`，是旅客等价运力，不是实际旅客 |
| 航司可承接量 | 分项需求封顶后的可服务量，尚未经过机场硬容量约束 |
| 城市最终承接量 | 再经过机场容量约束的结果，是当前最接近机场实际吞吐的模型量 |

当前契约只要求层内关系成立：五类城市潜在量之和等于城市潜在客流，五类可承接量与最终承接量分别守恒，并满足“最终承接量 ≤ 可承接量 ≤ 城市潜在客流”“可承接量 ≤ 航司投放能力”和“最终承接量 ≤ 机场最大容量”。它**不要求** 47 城市潜在客流合计等于中国区域参考量；两者不相等在当前版本不是模型错误。

长期若取得区域 OD 旅次、国内旅次占比、区域内中转规则、47 城同口径覆盖率和未建模机场剩余量，可另行引入版本化的“旅次—吞吐量桥接”。候选关系可从 `区域机场处理量 = 2 × 国内 OD 旅次 + 国际 OD 旅次 + 中转修正` 开始，但这些校准数据目前缺失，公式尚未实现，也不能用 `domestic_market_depth` 或单个 Seed 的历史比例代替。

## 第三层：城市机场市场

### 配置输入

[`city_airport_market_demand_layer_sim.py`](../../macro_layers/city_airport_market_demand_layer_sim.py) 读取区域航空需求、区域航司供给和区域宏观，同时加载每个城市 JSON。城市配置定义：

- 城市和机场系统身份、市场等级与类型；
- 起始潜在客流和长期增长偏置；
- 五类客群基础份额与城市偏置；
- 城市航司供给基准、区域运力捕获率，以及显式选择的航司供给动态模板；
- 城市 seed 势能模板；
- 高端旅客与商业倾向偏置；
- 机场、航站楼槽位、设施规格和启用年份。

当前 47 个城市的五类基础份额都合计为 100%，也都启用了城市 seed 势能。seed 势能会在若干年后逐步释放；区域环境对齐分数继续输出供解释，但不再重复进入 Seed 数值乘数。Seed 势能改变长期潜在客流，不直接增加航司或航站楼容量。

### 城市潜在客流

城市需求 v0.4 把总量路径和五类结构路径分开。潜在总量以城市 JSON 的 `baseline_city_potential_passengers_million` 为体量锚：

```text
城市潜在总量
  = 基准潜在客流
  × 区域航空总需求因子
  × 城市长期偏置因子
  × 城市 Seed 势能乘数
```

区域航空总需求只在这条公式中进入一次：指数 100～150 保持线性，超过 150 后采用收益递减但带小幅线性尾部的平滑映射，因此成熟市场不会无限按原始指数同比放大，不同强势世界线也不会收敛到同一个固定平台。既有长期城市偏置保留方向和排序，以显式 `0.40` 弹性进入；Seed 乘数保持配置给出的有界幅度，并只由稳定的城市/Seed 路径决定。

五类结构不再各自携带同一份区域总量增长。模型先计算“区域分项指数 ÷ 区域总需求指数”的相对信号，再按城市客群响应弹性形成相对得分，与城市基础份额相乘并归一化到 100%；最后用归一化份额拆分城市潜在总量。因此纯总量冲击不会改变五类份额，纯结构冲击也不会改变城市总量。区域事件和宏观冲击已经在上游区域路径中消费，城市需求层不再根据事件标签重复施加。

五类旧指数边界仍作为极端输入的最终安全线，但现在每类都会同时输出 raw index、final index、边界方向、floor/cap flag 和连续命中年数。它们是结构诊断，不再参与城市总量计算。审计旧 Run 时只能观察最终边界；新 Run 可以区分“接近边界”和“确实被截断”。

`baseline_region_demand_share_pct` 尽管保留了历史字段名，实际是“城市基准潜在量 ÷ 区域参考量”的诊断比率；它用于比较当年计算比率并输出 `city_share_adjustment_pp`，不是把区域旅客量按固定比例直接分配给城市的公式参数。47 城该字段合计不要求为 100%。

城市输出会记录 `source_region_reference_*` 方便解释上游背景，但这些区域参考数量不进入城市客流硬上限。城市只继承区域运力指数、航司信心、扩张意愿和约束压力等方向性信号。

### 城市航司供给

城市航司供给有独立的基准客流和年度状态。当前实现把长期均衡、缺口追赶和区域短期规划拆成显式通道：

```text
长期均衡 = 城市潜在客流锚 + 宏观调整 - 运营约束拖累
本年捕获目标 = 上年供给 + clip(demand_pull_capture × (长期均衡 - 上年供给))
区域短期规划信号 = 区域运力趋势本年变化量（有界）
```

`demand_pull_capture` 现在只决定本年吸收多少均衡缺口，因此会改变收敛速度，但不会再把长期终点固定在“区域趋势与城市需求之间”。区域运力趋势仍影响阶段判断和短期投放，但其绝对水平不再形成第二个长期固定点。第一年保留原有区域趋势参考，以免重写配置起点；随后再让航司经历有持续性的经营阶段：

```text
平衡 → 扩张 → 过度扩张 → 收缩 → 低谷 → 恢复 → 新一轮平衡或扩张
```

扩张和收缩不是预先画好的正弦波。阶段转换由供需缺口、信心、约束、Seed 冲击和岔路事件共同触发；每个阶段会持续若干年，因此供给不会一年上涨、下一年又机械回落。扩张期允许航司把近期乐观外推成过度投放；进入过度扩张后，模型会以“潜在客流 × 配置的目标过剩率”作为最低过热目标，而不只是高于正常基本面。收缩和低谷期允许悲观情绪把供给压到正常水平以下。实际供给仍有惯性，扩张通常慢于削减，低谷后的恢复也不会立即完成。

共享配置位于 [`china_city_airline_supply_behavior_profiles_v2.json`](../../config/airline_supply_dynamics_profiles/china_city_airline_supply_behavior_profiles_v2.json)。每个城市必须选择一个基础门户行为，并显式列出可叠加特征：

- 基础行为：全球枢纽、国家门户、区域门户、次级门户；
- 叠加特征：旅游暴露、战略支撑、高原约束；
- 例如昆明、厦门、海口保留原有门户等级，同时叠加旅游暴露；乌鲁木齐和喀什叠加战略支撑；拉萨和西宁叠加高原约束。

基础行为和特征只规定响应速度、过度投放、悲观收缩、供给底线和阶段持续倾向。`overcapacity_target_pct` 显式规定过热期相对潜在客流的目标过剩率，`upward_change_limit_pct` 和 `downward_change_limit_pct` 显式规定单年指数调整上限；三者都来自共享配置，不再藏在代码默认公式中。具体阶段时点、强弱、冲击数量和持续时间继续由 `market_id + Seed` 派生，因此同类城市不会共享固定答案。单城只有在有明确校准依据时，才可用 `dynamics_overrides` 覆盖最终有效参数。

因此，城市需求上升后，航司可以滞后扩张；压力年份也可以先收缩再恢复。这里要区分三种数：

- **投放运力** `offered_capacity`：航司本年准备投放的总能力；
- **可承接供给** `serviceable_supply`：投放运力按五类客群分配、并扣除某类需求已经饱和后真正能服务的量；
- **机场最终承接** `served_passengers`：可承接供给再受机场极限容量约束后的量。

当投放运力高于潜在客流时，超出部分只进入 `city_airline_unused_capacity_million`。它可以表示低客座率、低效航班和未来削减压力，但不会变成真实旅客，也不会突破任一客群的潜在需求上限。当前供给状态按年度生成；季度经营只按季节权重拆分年度结果，没有另造一套季度增班或撤班随机过程。

五类分配由统一函数完成。函数先把区域航司信心、航线/机队意愿、票价、汇率、宏观和时刻压力转为动态权重，再乘城市类型模板和城市微调；随后使用有上限的加权分配，把某一客群多余的投放重新分给仍有需求的客群。因此同时满足：

```text
五类可承接供给合计 = min(城市潜在客流, 城市航司投放运力)
单类可承接供给 <= 该类潜在客流
单类最终承接量 <= 单类可承接供给
```

通用模板位于 [`china_city_component_allocation_profiles_v1.json`](../../config/airline_supply_component_allocation_profiles/china_city_component_allocation_profiles_v1.json)。未单独配置的中国城市使用均衡模板；北京使用双枢纽模板，并在自己的城市 JSON 中做小幅微调。模板表示一类城市的通用供给偏好，城市微调只表达北京自身差异，不把北京参数写进通用算法。

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

总量公式没有改变，但五类结果不再用同一个总满足率乘潜在客流。机场容量不足时，当前政策 `proportional_compression` 会在已经分配好的五类可承接供给上同比例压缩，保留年度航司分配形成的客群差异。

模型同时输出 `demand_limited`、`airline_bottleneck`、`airport_bottleneck` 或双重瓶颈，以及潜在、航司供给、设计容量、极限容量、承接和未满足客流。这些字段是后续季度经营和玩家扩建决策的输入。

季度经营读取同一年度五类可承接供给并按季节权重拆分；客流预测的审计真值也读取同一结果。两条下游不再各自重建一套分客群供给。

## 客流预测报告

客流预测是城市市场之后的信息层，不反向修改城市真实路径、航司真实供给或季度经营。普通报告在某个 `as-of` 年份只能使用：

- 截至该年的公开历史、近期趋势和城市结构；
- 当前航司供给状态；
- 从隐藏未来压缩得到的方向、强弱、周期和模糊拐点窗口；
- 报告等级、研究风格、修饰标签和上一期观点。

普通报告不读取目标年份的真实数值。隐藏未来先被分类为 `strong_decline`、`decline`、`stable`、`moderate_growth` 或 `strong_growth` 等信号，再按报告等级发生遗漏、错分和时间窗口扰动。两条精确未来若得到相同信号包，普通报告会生成相同的预测路径；神级开发审计报告除外。

每期报告一次联合生成完整潜在需求路径与航司供给路径，并继续保持：

```text
预测有效客流
  = min(预测潜在客流, 预测航司供给)
```

整条路径使用同一组持续偏向、研究叙事和拐点判断，相邻年度增速变化受等级模板约束，不再为每个目标年独立混入隐藏真实值。五类预测分别生成潜在需求占比路径和航司优先权重路径，再复用城市市场的封顶分配函数；由此得到每类初始计划投放、再分配后的有效供给、满足率和未满足需求。五类初始计划投放合计等于总计划投放；某类需求提前封顶后，余下运力会按权重重新分给其他客群，因此单类有效供给可以高于该类初始计划投放，但不会超过该类潜在需求，五类有效供给合计仍等于总预测有效客流。

分项预测只观察由隐藏未来压缩得到的结构方向，不能读取未来精确客群值。`客群敏感` 会提高需求结构和航司分配两类信号的辨识能力，`供给敏感` 主要改善航司分配判断。分项区间同时吸收总量误差和客群份额误差，因此属于单客群边际区间，五类上限不具备可加性。

同一报告 ID 的下一期报告会继承上一期尚未到期的预测路径。实际结果、需求信号、供给信号或拐点窗口变化时，报告按自己的修订速度调整，并记录修订原因；缺少新证据时，例行更新幅度受到限制。

事后评价采用 `narrative-passenger-realized-score-v1.2`：

- **总量结果**：中值 30%、趋势 12%、形状 8%、瓶颈 5%、总量区间 15%；
- **分项结果**：潜在需求结构 4%、航司有效供给结构 5%、供给满足率差异 3%、分项区间 3%；
- **预测结果分**：总量结果 70% 与分项结果 15% 合并后归一化到 0～100；
- **实际评分**：结果分占 85%，另加入拐点判断 8% 和修订纪律 7%，修订纪律内部按总量 80%、分项 20% 合成。

报告等级不直接加分。初级报告如果路径准确、区间诚实且修订合理，同样可以取得高分。

玩家报告分块不含隐藏真值、未到期评分和神级报告。开发审计使用独立索引与分块，额外携带真实路径、信号原始分类和完整评分。

普通报告共享 8 种基础分析方法；同一方法可以通过能力等级、立场、方法侧重、修订行为和不确定性标签形成不同机构。报告输出同时携带中文风格说明、分析方法、典型盲点、标签名称、分类、作用和代价，供玩家界面解释。共享等级、风格和标签参数见[客流预测报告参数](../reference/Forecast_Parameters.md)。

## 输出位置

完整 Run 中的目录为：

```text
output/macro_runs/<run_id>/<variant>/regional_aviation_demand/<region_id>/
output/macro_runs/<run_id>/<variant>/regional_air_capacity_supply/<region_id>/
output/macro_runs/<run_id>/<variant>/city_airport_market_demand/<region_id>/
output/macro_runs/<run_id>/<variant>/city_airport_potential_passenger_forecast/<region_id>/
```

每层都有逐年 CSV 和摘要 JSON；`full` 产物模式还会生成 Viewer 数据。主要数量与单位：

| 后缀或名称 | 含义 |
| --- | --- |
| `_index` | 无量纲内部指数，必须结合该字段自己的基准解释 |
| `_pct` | 百分比或年增长率；`_pp` 才表示百分点差 |
| `_million` | 百万人次体量；相同后缀不代表不同层级可以直接加总 |
| `target_load_factor_pct` | 区域航线与时段匹配后可实现的目标载客率 |
| `load_factor_pct` | 区域参考承接旅客量相对可运营座位的实际载客率 |
| `fulfillment_pct` | 区域参考需求中被有效承接能力满足的比例 |
| `reference_*_passengers_million` | 区域诊断和解释量，不是城市客流硬上限 |
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
- 城市航司供给行为模板：[`china_city_airline_supply_behavior_profiles_v2.json`](../../config/airline_supply_dynamics_profiles/china_city_airline_supply_behavior_profiles_v2.json)
- 五类客群供给分配模板：[`china_city_component_allocation_profiles_v1.json`](../../config/airline_supply_component_allocation_profiles/china_city_component_allocation_profiles_v1.json)
- 客流预测等级模板：[`forecast_report_tier_profiles_v1.json`](../../config/forecast_report_tier_profiles/forecast_report_tier_profiles_v1.json)
- 客流预测叙事模板：[`forecast_narrative_profiles_v2.json`](../../config/forecast_narrative_profiles/forecast_narrative_profiles_v2.json)
- 北京预测报告配置：[`beijing_airport_system_potential_passenger_forecast_v1.json`](../../config/city_airport_potential_passenger_forecast/beijing_airport_system_potential_passenger_forecast_v1.json)
- 客流预测实现：[`city_airport_potential_passenger_forecast_layer_sim.py`](../../macro_layers/city_airport_potential_passenger_forecast_layer_sim.py)
- 航站楼规格：[`standard_terminal_sizes_v1.json`](../../config/facility_size_catalogs/standard_terminal_sizes_v1.json)
- 一键串联和输出：[`macro_run_orchestrator_sim.py`](../../macro_layers/macro_run_orchestrator_sim.py)
- 14 区、47 城和 60 年数量契约：[`test_long_horizon_contract.py`](../../tests/test_long_horizon_contract.py)
- 固定 seed 数值基线：[`test_safety_baseline.py`](../../tests/test_safety_baseline.py)
- 预测叙事与信息边界：[`test_forecast_narrative_model.py`](../../tests/test_forecast_narrative_model.py)

## 当前限制

- 区域航空需求和供给参数仍内嵌在 Python；只有城市市场和设施规格使用 JSON 配置。
- 需求与供给是大区汇总，没有机场对机场航线网络、票价舱位、航空公司主体或机队机型。
- 区域参考满足率不再设人为下限；五类客群满足率仍各有下限，这是稳定性保护，会压低极端短缺的尾部幅度。
- 城市层不是把区域总客流做守恒分摊；各城市以自己的基准潜在客流计算，因此 47 城市潜在客流之和不保证等于中国大陆区域总量。
- 区域参考承接旅客量会作为解释字段进入城市层；城市供给环境来自区域运力、信心和约束信号，区域参考百万人次数量不会成为城市实际客流上限。
- 机场容量当前只按年度启用的设施规格求和，没有跑道、小时峰值、天气、空域、安检或地面保障的独立硬约束。
- 47 城配置已有独立 JSON Schema、`schema_version` 过滤和运行时字段/槽位验证；Schema 固定结构与基础范围，不替代固定 Seed 数值回归或跨层语义校准。
