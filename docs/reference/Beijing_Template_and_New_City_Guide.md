# 北京样板与新增完整经营城市指南

本文回答一个具体问题：把上海、广州等现有“城市市场”扩展成与北京同等级的预测、季度经营、财务和估值城市时，哪些内容必须重做，哪些可以复用，以及为什么仅复制 JSON 还不能得到可玩的城市界面。

当前中国大陆已有 47 个城市市场配置，但它们最初主要是为了让全国城市覆盖、Viewer、Seed 差异和容量链能够提前运行的**占位市场**，不能据此宣称 47 城已经完成逐城研究和数值校准。只有北京具备完整的五层配置；上海和广州已经分别存在 `shanghai_airport_system.json` 和 `guangzhou_airport_system.json`，扩展时应审查原占位值并补齐下游配置，不要再创建第二份同 ID 的城市市场文件。

## 1. 两种“完成”不要混淆

| 完成层级 | 判定标准 | 是否需要改代码 |
| --- | --- | --- |
| 模型链完整 | 正式 Run 能为该城市生成城市市场、有效客流预测、季度经营、财务和估值输出 | 通常只需配置；测试预期需要更新 |
| 游戏界面可玩 | 8776 动态经营能选择该城市，项目、合同、融资、存档、API 和 Viewer 都按该城市工作 | 需要先把北京硬编码参数化 |

本指南先保证模型链配置正确，同时明确第二层的代码前置条件。不要把“Run 已生成上海经营 CSV”写成“上海已可在动态经营界面游玩”。

## 2. 五类配置与事实来源

| 层级 | 北京当前文件 | 主要代码 |
| --- | --- | --- |
| 城市市场 | [`beijing_airport_system.json`](../../config/city_airport_markets/china_mainland/beijing_airport_system.json) | [`city_airport_market_demand_layer_sim.py`](../../macro_layers/city_airport_market_demand_layer_sim.py) |
| 有效客流预测 | [`beijing_airport_system_potential_passenger_forecast_v1.json`](../../config/city_airport_potential_passenger_forecast/beijing_airport_system_potential_passenger_forecast_v1.json) | [`city_airport_potential_passenger_forecast_layer_sim.py`](../../macro_layers/city_airport_potential_passenger_forecast_layer_sim.py) |
| 季度经营 | [`beijing_airport_system_quarterly_operations_v1.json`](../../config/city_airport_operations/beijing_airport_system_quarterly_operations_v1.json) | [`city_airport_quarterly_operations_layer_sim.py`](../../macro_layers/city_airport_quarterly_operations_layer_sim.py) |
| 财务状态 | [`beijing_airport_group_financial_state_v1.json`](../../config/city_airport_finance/beijing_airport_group_financial_state_v1.json) | [`city_airport_financial_state_layer_sim.py`](../../macro_layers/city_airport_financial_state_layer_sim.py) |
| 估值观察 | [`beijing_airport_group_valuation_forecast_v1.json`](../../config/city_airport_valuation/beijing_airport_group_valuation_forecast_v1.json) | [`city_airport_valuation_forecast_layer_sim.py`](../../macro_layers/city_airport_valuation_forecast_layer_sim.py) |

五层由 [`macro_run_orchestrator_sim.py`](../../macro_layers/macro_run_orchestrator_sim.py) 以 `city_airport_market_id` 连接。具体公式和默认回退以代码为准；JSON 是城市实际参数；本文和其它参考文档负责解释，不替代两者。

## 3. 四种迁移分类

后文使用以下分类：

- **必须按城市调整**：直接代表当地客流、机场、经营或资产，复制北京值会得到错误城市。
- **可从大陆参考起步**：可以把中国大陆共同口径作为首轮假设，但必须手工复制并留下校准依据，不存在运行时继承。
- **全局共享，慎改**：修改会影响北京和其它引用者；城市有特殊口径时优先新增独立配置。
- **当前硬编码，先参数化**：JSON 即使齐全，8776 或 Viewer 仍不会自动切换到新城市。

快速判断如下：

| 内容 | 分类 |
| --- | --- |
| 城市客流、机场清单、槽位、商业结构、开局资产和现金 | 必须按城市调整 |
| 大陆税率起点、季度通用形状、成本曲线和估值框架 | 可从大陆参考起步 |
| 标准设施等级和容量、区域宏观与航空层 | 全局共享，慎改 |
| 动态项目目录、北京 CSV 路径、合同 ID、融资产品、北京 Viewer | 当前硬编码，先参数化 |

## 4. 文件命名、注册与 Run 发现

推荐使用以下命名；真正的连接键始终是文件内部的 ID：

```text
config/city_airport_markets/china_mainland/<market_id>.json
config/city_airport_potential_passenger_forecast/<market_id>_potential_passenger_forecast_v1.json
config/city_airport_operations/<market_id>_quarterly_operations_v1.json
config/city_airport_finance/<operator_id>_financial_state_v1.json
config/city_airport_valuation/<operator_id>_valuation_forecast_v1.json
```

注册规则：

1. 城市市场目录会递归查找 JSON，并读取 `market.city_airport_market_id`。
2. 其余四个目录只查找各自目录顶层的 `*.json`，并读取顶层 `city_airport_market_id`；不要擅自放入城市子目录。
3. 不需要另改中央注册表。文件被加载且五层 `city_airport_market_id` 完全一致，就是正式 Run 的注册。
4. 同一目录若出现重复 `city_airport_market_id`，后加载文件可能覆盖前者；项目没有把这种情况作为可靠的配置机制，必须保持唯一。
5. 预测配置独立挂在城市市场之后；经营缺失时 Run 会记录 `missing_operations_config`。财务依赖经营，估值再依赖经营与财务。
6. 文件名主要服务于人和输出约定。`schema_version` 必须使用对应加载器支持的精确值；`config_version` 应在有意义的调参后递增。

ID 建议保持稳定：

- `market_id` 使用小写 snake case，例如 `shanghai_airport_system`；
- `operator_id` 表示经营主体，不必与 market ID 相同；
- `airport_id` 优先使用稳定机场代码；
- `slot_id` 使用 `<AIRPORT_ID>_SLOT_<序号>`，一经进入资产、项目或存档后不要随意改名；
- 机场、槽位、资产、贷款、项目和事件 ID 在各配置中都应唯一。

## 5. 第一层：城市市场

### 当前 47 城的成熟度边界

现有 47 城配置首先是一套机制覆盖和未来扩展骨架：它能让同一模型在不同城市、机场结构和 Seed 上运行，但不等于每个城市的客流规模、客群结构、航司投放和长期路径都已达到正式产品校准水准。当前客流项目只需要保证模型公式、配置加载、守恒、确定性和跨 Seed 分化健康；逐城历史回测、当地航线网络、分客群供给研究和经营参数精调留到该城市真正进入可玩范围时进行。

未来任何城市从“占位市场”升级为“已校准城市市场”，至少必须明确声明并复核以下四块。四块可以复用共享模板，但不能依赖未记录的代码默认值：

| 声明块 | 当前配置入口 | 未来升级要求 |
| --- | --- | --- |
| 总客流需求 | `demand_model` | 明确基准年、城市本地潜在量、长期增长偏差和 Seed 势能边界，并记录统计口径或校准依据 |
| 分项客流需求 | `component_mix`、`component_biases` | 明确商务、休闲、探亲访友、长途和中转的基期结构及城市相对偏置；结构合计守恒，不能把模板标签当成数据证据 |
| 总航司供给 | `airline_supply_model` | 明确基准投放量、共享行为模板、修饰特征和必要的单城覆盖；说明它为何属于相应门户/约束类型 |
| 分项航司供给 | `airline_supply_component_allocation` | 显式选择共享分配模板并声明城市微调；即使选择均衡模板，也应明确写出，而不是因字段缺失静默回退 |

这四块是城市年度市场的最低业务契约，不要求现在立刻把 47 城全部精调。现有占位配置可以继续用于当前客流层的机制验收；只有当某城市要进入经营预测、季度经营或正式玩家选择时，才把四块逐项升级为有依据的配置，并升级对应 `config_version`。没有可靠证据时，明确保留“占位/待校准”状态优于编造看似精确的城市参数。

机场槽位、设施规格、开放年份和容量属于第五类设施声明，由 `facility_model` 与 `airports[].slots[]` 管理；它与上述需求/供给四块相互约束，但不是航线或 OD 网格。当前模型没有机场到机场航线网络、航空公司主体、舱位或机队配置，不能从这些城市 JSON 推断出真实航线网络。

### 必须按城市调整

- `market`：城市、区域、市场等级、单机场/多机场结构和机场系统名称；
- `demand_model`：基准年、区域需求份额、城市潜在客流、长期增长偏差和 Seed 势能范围；
- `component_mix` 与 `component_biases`：商务、休闲、探亲访友、长途、中转五类结构；基础占比合计应为 100%；
- `airline_supply_model`：当地基础航司供给、区域运力增长捕获、本地供给增长，并用 `dynamics_profile_id` 选择基础门户行为、用 `dynamics_modifier_ids` 叠加旅游/战略/高原等特征；
- `airline_supply_component_allocation`：选择共享城市类型模板，并只填写该城市相对模板的微调；北京使用 `china_dual_hub_v1`，其它城市不能因为方便而照抄北京微调；
- `commercial_biases`：高端、免税、精品、电子、餐饮和普通零售倾向；
- `airports[].slots[]`：真实机场、槽位角色、设施等级、允许等级和启用年；
- `capacity_reference_profiles` 和文字说明也应改成当地事实，避免配置自相矛盾，即使其中部分字段目前只用于说明或输出元数据。

### 可复用与共享边界

- 中国大陆城市通常可以继续使用 `region_id = china_mainland`、上游 Seed/branch 继承方式和五类客流字段名。
- [`china_city_airline_supply_behavior_profiles_v2.json`](../../config/airline_supply_dynamics_profiles/china_city_airline_supply_behavior_profiles_v2.json) 是共享总供给行为目录。新城市先在全球/国家/区域/次级门户中选一种基础行为，再按需要叠加旅游暴露、战略支撑或高原约束；特征是总供给行为，不是客群分项。过热目标、单年上调上限和单年下调上限都已显式写在目录中。若确有单城校准依据，可在 `dynamics_overrides` 覆盖最终参数。不要复制整套参数到每个城市，也不要为了单城修改共享模板。
- [`china_city_component_allocation_profiles_v1.json`](../../config/airline_supply_component_allocation_profiles/china_city_component_allocation_profiles_v1.json) 是共享客群供给模板目录。普通城市默认使用 `china_balanced_city_v1`；只有多个城市确实共享稳定特征时才新增通用模板，北京等单城差异留在城市 JSON。
- [`standard_terminal_sizes_v1.json`](../../config/facility_size_catalogs/standard_terminal_sizes_v1.json) 是全局设施目录。修改其容量会影响所有引用城市；若当地需要不同等级，新增唯一 `catalog_id` 的目录文件更安全。
- `facility_model` 中的容量紧缺政策可以复用，但当地槽位数量和角色不能照搬北京的“首都 + 大兴、双机场各五槽位”。

特别注意：市场槽位的 `open_year` 表示它何时进入模拟容量；它不等于建筑真实投运年或财务折旧起点。

## 6. 第二层：有效客流预测

### 必须按城市调整

- 顶层 market、city、region 标识；
- `timeline`，并与其它四层保持一致；
- 该城市能获得哪些等级与研究风格、报告来源、最大预测期、质量、校准、偏差上限和误差带；
- 如果当地数据质量或行业透明度不同，不能默认沿用北京 13 份报告的能力梯度。

`forecast_report_source` 是预测行为的来源标签，不是一个会自动读取外部机构数据的文件路径。普通报告不会读取目标年的精确真值：隐藏未来先压缩成供需方向、强弱、客群结构方向和模糊拐点窗口，再由等级能力、研究风格、0～2 个修饰标签及连续修订生成 as-of 路径。普通报告的 `future_peek_mode` 应为 `false`；`真实路径` 是明确的开发审计，不属于正常平衡。

新增配置必须通过 [`forecast-config.schema.json`](../../schemas/forecast-config.schema.json)，并引用共享的等级与风格目录；`forecast_lag_years`、`derive_lag_from_quality` 等旧滞后参数已退出正式配置，不能复制回新城市。预测规则和全部参数含义以[客流预测报告参数](Forecast_Parameters.md)为唯一权威说明。

### 可以复用

如果所有城市共享同一套“玩家可购买研究产品”，等级模板、研究风格、评分和通用算法可以复用；城市配置只选择报告组合并做必要覆盖。质量、偏差和区间仍需用该城市多 Seed 误差分布重新校准。预测报告不会反向改变真实客流。

## 7. 第三层：季度经营

北京经营配置引用的 [`parameter schema`](../../config/city_airport_operations/templates/city_airport_quarterly_operations_parameter_schema_v1.json) 和 [`中国大陆参考值`](../../config/city_airport_operations/reference_defaults/china_mainland_quarterly_operations_reference_defaults_v1.json) 都是说明和手工起点，运行时不会自动合并。

### 必须按城市调整

- 五类客流季度权重；当前新建季度经营配置时必须显式校准，每类 Q1–Q4 合计应为 1；
- 设施固定成本、城市复杂度、各槽位真实维护年龄起点和季节成本；
- 单客航空收入、客流结构权重、服务成本、拥挤阈值和当地定价环境；
- 餐饮零售的客单价、自营效率、销售成本和当地商业复杂度；
- 免税与精品的有效客流权重、国际暴露、捕获率、客单、宏观敏感度和质量敏感度；
- 合同期限、分成、保底、开局继承合同和预测签约假设；
- 翻新、新建、重建的当地成本乘数、工期、拆除、残值和折旧寿命；
- `facility_*_events` 中所有北京示例事件。新城市没有已确定事件时应使用空数组，不能保留首都/大兴项目。

### 季节性配置原则

城市年度市场不需要季节性参数，也不应为了年度 Viewer 给现有 47 城补写暂时无效的季度权重。只有城市真正接入季度经营、季节性会影响客流、拥挤、收入或成本时，才需要配置这一层。

不同城市的季节结构可能显著不同，例如商务枢纽相对平滑，暑期旅游城市、冬季避寒城市和春节探亲型城市各有不同高峰。新城市不能无依据照搬北京的 Q1/Q3 结构。当前尚未建立共享季节模板目录；在只有少数可玩城市时，可以先在该城市经营配置中显式校准。

如果以后扩展多个季度经营城市，优先建立“商务枢纽、均衡城市、暑期旅游、冬季旅游、探亲型”等共享季节模板，让城市显式选择模板并只做必要覆盖，不要给每个城市复制一套近似参数。届时还可以评估是否将需求季节权重与航司供给季节权重分开，避免航司在每个季度都完全同步跟随需求。

季节性不要求在城市年度市场页面单独展示。只有它会影响玩家季度判断时，才需要在动态经营界面提供季度曲线或解释；配置存在并不意味着必须增加一个独立 Viewer 面板。

### 设施、项目和合同的一致性

- 经营配置中的 `slot_open_years` 是维护年龄锚；市场配置的 `open_year` 是模拟容量启用年；财务配置的 `in_service_year` 是折旧锚。三者含义不同，但必须能讲通同一资产历史。
- 静态新建事件的完工季度应与市场槽位开始提供容量的年份一致。项目期间容量、完工资产和后续折旧必须连续。
- 设施目录 ID 应在市场、翻新、新建、重建和感知质量模型中一致。季度经营按 `<catalog_id>.json` 文件名读取目录，因此自定义目录的文件名必须与 `catalog_id` 相同。
- 免税/精品先计算运营商销售额，再由分成或保底转成机场收入；不能把销售额直接记作机场收入。

完整参数含义见 [机场经营参数参考](Airport_Operations_Parameters.md)。

## 8. 第四层：财务状态

### 必须按城市或经营主体调整

- `operator_id`、经营主体名称、market 和 region 标识；
- 开局现金、留存收益、短期/长期债务；
- 当地税务适用口径，包括税率、预缴、汇算和亏损结转；
- 债务政策、城市信用利差和利率边界；
- `initial_assets` 的机场/槽位 ID、真实投运年、原值、寿命和残值；
- `general_loans`。北京三笔贷款是长期路径测试样例，不是大陆默认债务，复制到新城市会真实进入基准 Run。

初始资产只应包括模拟开始时已经存在的资产。模拟期内翻新、新建和重建产生的资产由经营事件进入财务层，不要再放入 `initial_assets` 重复入账。

中国大陆 25% 税率和北京贷款定价可以作为首轮参考，但必须确认主体资格和城市信用条件。开局投入资本由现金、资产和债务平衡得出，不应为了“看起来像北京”倒填。

## 9. 第五层：估值观察

必须替换 operator、market、region 和时间线，并重新判断：历史窗口、增长回退、利润率收敛、维护资本开支、城市风险溢价、资产质量、合同质量和不确定性范围。

当前正式主口径是净资产价值，Operating EV 和 Market EV 是实验观察字段；配置齐全不代表该城市已经具有可交易市场价格。可以复用北京的估值框架，但不能把北京的资产质量、合同质量和风险假设当成全国常数。估值不会反向改变经营、贷款或合同。

完整口径见 [财务与估值参数参考](Finance_and_Valuation_Parameters.md)。

## 10. 跨层时间线与单位

新增城市提交前至少核对：

| 约束 | 正确关系 |
| --- | --- |
| 起始年 | 市场 `baseline_year`、预测/经营/财务/估值 `simulation_start_year` 对齐 |
| 玩家接管 | `simulation_start_year + startup_operating_history_years = player_decision_start_year` |
| 设施历史 | 初始槽位、维护年龄锚和初始资产应引用同一 slot ID，并分别使用正确年份含义 |
| 建设启用 | 静态项目完工后才增加容量；新资产从正确季度进入在建工程、折旧和账面值 |
| 金额 | `*_million_cny` 为百万元人民币；界面可能换算为亿元 |
| 客流 | `*_million` 为百万人次；“百万人次 × 元/人次”数值上等于百万元 |
| 比例 | `*_pct` 中 `25.0` 表示 25%；`*_multiplier` 中 `1.05` 表示 1.05 倍 |
| 利差与时间 | `*_bps` 中 100 bp = 1 个百分点；4 quarters = 1 年 |

所有 market/city/region/operator、airport、slot、asset 和 event 引用都应逐项交叉检查，不能只确认文件能被 JSON 解析。

## 11. 8776 与 Viewer 的北京硬编码边界

[`airport_sim/server/app.py`](../../airport_sim/server/app.py) 当前明确是北京动态经营服务，至少包含以下需参数化内容：

| 硬编码 | 新城市可玩前要做什么 |
| --- | --- |
| 北京经营、财务和城市需求 CSV 相对路径 | 改为由 market ID 解析 Run 输出 |
| 北京经营/财务配置常量和生成文件名 | 建立按城市选择的配置注册对象 |
| PEK/PKX 初始槽位、154/200 容量和航站楼编号 | 从城市市场和财务配置派生 |
| `PROJECT_TEMPLATES`、槽位名称、工程目录 | 改为城市/机场驱动的项目目录 |
| `DUTY_FREE_MAIN`、`LUXURY_RETAIL_MAIN` 合同动作 | 建立可配置合同定义和稳定动作 ID |
| `FINANCING_PRODUCTS` 和每季动作限制 | 区分全局产品规则、城市信用政策与界面校验 |
| 玩家配置写入、子进程 `--market beijing_airport_system` | 传入当前城市并隔离缓存/存档键 |
| `aggregate_beijing_operations`、北京 API Schema 与页面文案 | 升级为通用城市契约或明确的版本化城市契约 |

[`macro_run_orchestrator_sim.py`](../../macro_layers/macro_run_orchestrator_sim.py) 虽能为新城市生成标准输出，但经营与预测 Viewer 发布包仍有北京文件名和北京页面入口。Web 页面、懒加载索引、发布 Manifest 键和浏览器路由也要一起通用化，不能只改一条页面标题。

这些改动应在新城市模型链稳定之后单独进行，避免把“参数校准误差”和“多城市 UI 重构错误”混在同一次变更中。

## 12. 推荐实施顺序

1. 先确定 `market_id`、经营主体、机场和槽位 ID，建立数据来源表，记录基准年、单位、来源、估算方法和不确定性。
2. 上海/广州优先审查并修订已有占位市场；真正的新城市才新增市场文件。先为总需求、分项需求、总供给和分项供给四块建立数据来源与校准结论。
3. 单独跑城市市场，确认潜在客流、航司供给、五类结构和容量路径合理；不能只因旧占位配置能够运行就宣布校准完成。
4. 新增预测配置，用多个 Seed 检查各等级报告的误差、覆盖和偏差，而不是只看一条漂亮曲线。
5. 从大陆参考手工建立经营配置，先不放未来静态项目，再逐项校准成本、收入、商业和合同。
6. 建立财务开局与初始资产，检查现金、折旧、债务、税务和资产负债表平衡。
7. 最后接入估值；经营和财务不稳定时不要用 DCF 倒推参数。
8. 正式 Run 确认五层被发现且 `city_airport_downstream_skips` 不再记录该城市缺失层。
9. 模型链验收后，再启动 8776/Viewer 多城市参数化工作。

## 13. 验收清单

### 配置与模型

- [ ] 五类配置的 schema 版本正确，JSON 无重复键；
- [ ] 五层 `city_airport_market_id` 完全相同且唯一；
- [ ] 城市/区域/经营主体、机场和槽位引用一致；
- [ ] 总需求、分项需求、总供给和分项供给四块均已显式声明，不依赖未记录的默认回退；
- [ ] 四块参数各有来源、估算方法或明确的待校准标记，没有把旧占位值伪装成正式事实；
- [ ] 五类基础客流占比为 100%，每类季度权重为 1；
- [ ] 每个设施等级都存在于所引用目录，设计容量不高于极限容量；
- [ ] 北京的 PEK、PKX、资产、贷款、项目、合同和说明文字已全部移除；
- [ ] 静态项目的开工、完工、容量启用、资产形成和折旧连续；
- [ ] 财务恒等式成立，现金、债务、税务和资产没有重复入账；
- [ ] 估值的主口径和实验字段没有混称；
- [ ] 多个 Seed 与短期/60 年路径都没有 NaN、无穷值或异常数量级。

先执行：

```powershell
py -3.13 -m airport_sim validate-config
py -3.13 -m airport_sim run --seed 20261324 --years 12
py -3.13 -m airport_sim run --seed 20261334 --years 60
```

`validate-config` 只检查 JSON 语法和重复键，不验证所有业务范围；两个 Run 和测试不能省略。输出应出现在对应 Run 的 `baseline/city_airport_*` 目录，并以新 `market_id` 命名。

### 回归测试

- [ ] [`test_long_horizon_contract.py`](../../tests/test_long_horizon_contract.py) 中“只有北京有下游配置”和 skip 数量的预期已按有意扩展更新；
- [ ] [`test_safety_baseline.py`](../../tests/test_safety_baseline.py) 的北京固定 Seed 摘要仍不变，除非本次明确修改了共享模型；
- [ ] 为新城市增加行数、字段、财务平衡、项目和预测质量断言，而不是只放宽旧测试；
- [ ] API/Viewer 若通用化，同步更新 Schema、快照、懒加载、发布和 DOM 测试；
- [ ] Python 3.13 完整测试与 `git diff --check` 通过。

完整命令见 [测试与安全修改](../development/Testing_and_Safe_Changes.md)。

## 14. 完成定义

一个新城市只有在五份配置通过 ID 自动拼接、正式 Run 生成完整下游、长期财务和估值稳定、测试明确覆盖其存在时，才可称为“完整模型城市”。只有在北京硬编码被参数化、动态操作与存档按城市隔离、Viewer/API/Schema 和浏览器验收通过后，才可称为“完整可玩城市”。

这两个里程碑应分开提交和验收。
