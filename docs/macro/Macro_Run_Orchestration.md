# Macro Run Orchestration

## 当前主流程

`macro_run_orchestrator_sim.py` 是当前推荐入口，用来把全球宏观、14 区区域宏观、区域对账、区域航空需求/供给、城市机场客流、北京季度经营和历史分岔发生路径串成一次完整 run。

```text
seed
  -> global macro feedback chain
  -> branch risk watchlist
  -> optional manual / probabilistic branch path
  -> 14 regional macro paths with structural regional seed potential
  -> regional reconciliation and GDP levels
  -> 14 regional aviation demand layers
  -> 14 regional air capacity / supply fulfillment layers
  -> configured city airport market demand layers
  -> configured city airport potential passenger forecast layers
  -> configured city airport quarterly operations layers
  -> configured city airport financial state layers
  -> configured city airport valuation / forecast layers
  -> optional publish to viewer output
```

## 推荐命令

随机生成一个大 seed，只跑 baseline 并归档：

```powershell
py -3 .\macro_layers\macro_run_orchestrator_sim.py --random-seed
```

固定 seed，生成 baseline 和自动选择的发生分岔路径：

```powershell
py -3 .\macro_layers\macro_run_orchestrator_sim.py --seed 20260630 --scenario-state occurred --scenario-branch-id auto
```

固定 seed，生成发生路径并发布到现有 viewer 数据目录：

```powershell
py -3 .\macro_layers\macro_run_orchestrator_sim.py --seed 20260630 --scenario-state occurred --scenario-branch-id auto --publish-viewer scenario
```

固定 seed，按 seed 自动抽取历史岔路时间线并发布：

```powershell
py -3 .\macro_layers\macro_run_orchestrator_sim.py --seed 20260630 --scenario-state probabilistic --publish-viewer scenario
```

如果 `python` 在 Windows 上指向 WindowsApps 占位符，就使用 `py -3`。

## 输出位置

每次 run 会归档到：

```text
output/macro_runs/<run_id>/
```

调度器不会直接在正式 `<run_id>` 中逐层写文件。实际过程是：

```text
output/macro_runs/.staging_<内部短标识>/
  -> 生成全部变体
  -> 校验核心 CSV 行数、表头、列宽、Seed、年份、year_index 和 14 区覆盖
  -> 写入 complete Manifest
  -> 原子改名为 output/macro_runs/<run_id>/
```

计算或校验失败时，本次 staging 会被清理，Macro Run Index 不会列出 staging。显式指定已经存在的 `run_id` 会停止并报错，不会把新旧文件合并。Viewer 发布只在正式 Run 完成后进行。

Windows 下建议使用默认输出目录，或选择层级较浅的自定义 `--output-root`。部分区域文件名本身较长，过深的临时目录可能触及传统 Windows 路径长度限制。

典型结构：

```text
baseline/
  global_macro/
  regional_macro/
  regional_macro_reconciled/
  regional_aviation_demand/
  regional_air_capacity_supply/
  city_airport_market_demand/
  city_airport_potential_passenger_forecast/
occurred_<branch_id>_<trigger_year>/
  global_macro/
  regional_macro/
  regional_macro_reconciled/
  regional_aviation_demand/
  regional_air_capacity_supply/
  city_airport_market_demand/
  city_airport_quarterly_operations/
  city_airport_financial_state/
probabilistic_branch_timeline_<n>events/
  ...
manifest.json
```

`manifest.json` 记录 seed、年份、变体、被选中的分岔风险、影响年份、当前可用分岔 profile 数量和是否发布到 viewer。它还记录模型版本、输出/Manifest Schema、Python 版本、`run_state = complete`，以及各变体通过校验的行数、文件数、表头摘要和区域覆盖。

有效客流预测和季度经营虽然在写出顺序中前后出现，但二者都读取城市机场真实数据：预测是玩家信息分支，季度经营不读取预测值作为实际经营输入。

## Baseline 和 Scenario

baseline 是当前路径，也就是“分岔未发生”。

`occurred` 或 `counterfactual` 会生成另一条路径。它不是在原 CSV 旁边简单贴标签，而是把分岔冲击加入全球反馈循环，再重新生成全球、区域、航空和城市机场下游。

手动模式一次 run 只激活一个分岔风险。`--scenario-branch-id auto` 会从 baseline 的 watchlist 中选出得分最高的风险，也可以用具体 id 指定。

`--scenario-state probabilistic` 会按 seed 从每年 baseline watchlist 中抽取一条历史岔路时间线。同一个 seed、起始年份和时长会得到同一组岔路；换 seed 后，岔路时间线可能变化。当前默认：

- 年度抽取倍率：`--probabilistic-scenario-frequency 0.12`
- 最早触发年份 index：`--probabilistic-scenario-min-year-index 2`
- 最少事件数：`--probabilistic-scenario-min-events 1`
- 最大事件数：`--probabilistic-scenario-max-events 0`，表示按时长自动估算，默认约每 15 年最多 1 个，封顶 12 个
- 事件冷却期：`--probabilistic-scenario-cooldown-years 6`，会叠加在该事件的 impact + tail 后面，避免同一段时间过度堆叠

当前运行时可用历史岔路 profile 收束为 12 种核心类型。旧 id 会通过 alias 折叠到最接近的核心类型，避免旧命令和旧输出引用直接断链。新增类型不应轻易扩张玩家可见岔路数量；优先作为这 12 类下面的叙事子事件或强度变体。

## Impact 和 Tail

`horizon_years` 表示风险观察窗口，不等于主动冲击期。

发生路径使用：

```text
impact_years + tail_years
```

在这些年份里，全球路径会得到额外的增长、产出缺口、金融压力、通胀和政策冲击；区域层会按各区域暴露度生成额外传导。

tail 结束后，不会强制回到 baseline。路径会继续从新的宏观状态往后演化，所以会有轻微或明显的路径依赖。

为了避免重复触发，手动路径只根据选定 trigger year 生成一段 `event_year_indices`。概率路径会在多事件之间加入冷却期；如果未来拉长到 100 年、200 年，可以通过最大事件数和冷却期控制事件密度。

## 发布到 Viewer

默认情况下，run 只写入 `output/macro_runs/`，不会覆盖当前页面数据。

使用：

```powershell
--publish-viewer baseline
--publish-viewer scenario
```

会先为对应路径生成一个不可变发布版本：

```text
output/viewer_releases/<release_id>/
  global_gdp_viewer.bundle.js
  beijing_airport_operations_viewer.bundle.js
  beijing_potential_passenger_forecast_viewer.bundle.js
```

三个数据包全部写完并计算 SHA-256 后，版本目录才会从 staging 状态转为正式版本。为了兼容现有页面和外部脚本，调度器随后仍会把对应路径复制到：

```text
output/global_macro/
output/regional_macro/
output/regional_macro_reconciled/
output/regional_aviation_demand/
output/regional_air_capacity_supply/
output/city_airport_market_demand/
output/city_airport_potential_passenger_forecast/
output/city_airport_quarterly_operations/
output/city_airport_financial_state/
output/city_airport_valuation/
```

兼容复制成功后，调度器最后才原子替换：

```text
output/current_viewer_manifest.json
output/current_viewer_manifest.js
```

三个静态 Viewer 优先按照 Manifest 读取同一 release 的数据包；没有有效 Manifest 时回退读取旧 canonical 文件。发布中途失败不会切换当前指针，因此页面只会看到完整旧版本或完整新版本。归档 run 始终保留在 `macro_runs` 下，历史 release 当前也不会自动删除。

有效客流预测 release 使用轻量目录和按报告 JSON 数据块。release bundle 只包含目录脚本，报告数据块与 bundle 放在同一 release 目录；页面只在切换到某份报告时加载对应数据块。旧完整预测 JS 仍复制到 canonical 目录用于兼容，但不再嵌入新版 release bundle。

## 当前进度

已完成：

- 全球宏观主链条：GDP、通胀、政策、收益率曲线、美元流动性、信用、资产、石油商品、反馈校准。
- 全球分岔 watchlist：虚假黎明、政策失误、信用事故、银行惜贷、美元挤兑、能源冲击、债券市场失控、软着陆、流动性牛市、再融资墙、需求破坏式降通胀、滞胀、风险资产牛市脆弱化。
- 14 区区域宏观：GDP、通胀、收入、利率、货币、信用、资产、能源、压力和信心。
- 区域 structural seed 势能：不同 seed 下会生成区域长期增长、航空倾向、投资周期和开放度偏移；中国大陆、北美、西北欧、南亚、东南亚、非洲等区域的相对命运不再完全固定。
- 区域 GDP 对账：区域 GDP 体量、全球占比、排名、增长贡献和诊断误差。
- 全球分岔到区域的显式传导：发生路径会按区域暴露度影响区域宏观。
- 14 区区域航空需求层：航空需求指数、旅客结构、票价敏感度、票价弹性和消费倾向。
- 14 区区域航空供给/满足率层：实际可服务客流、未满足需求、分项旅客满足率和供给票价压力。
- 中国大陆城市机场客流层：已按城市配置承接区域航空需求/供给。
- 北京季度机场经营层、财务状态层、税务和净资产主估值层：已作为样例接入一键 run。
- 北京估值观察层：当前主口径为净资产定价，DCF、市场 EV、PE/PB 和宏观折溢价保留为观察指标。
- 城市机场市场需求层：根据城市 JSON 配置，将区域航空需求/供给自动下钻到城市潜在客流、航司供给和机场槽位容量瓶颈。目前已有北京、上海、广州、深圳、成都、重庆、杭州、南京、西安、武汉、昆明、郑州、厦门、长沙、青岛、天津、济南、福州、沈阳、大连、石家庄、哈尔滨、长春、太原、合肥、南昌、宁波、温州、贵阳、南宁、海口、三亚、乌鲁木齐、兰州、呼和浩特、银川、西宁、拉萨、珠海、泉州/晋江、烟台、无锡/苏州、潮汕、丽江、西双版纳、桂林、喀什样板。
- 北京城市有效客流预测层：先分别预测潜在客流和航司供给，再取小值作为市场有效客流；已按初级、中级、高级、专业级和神级未来透视生成 as-of 预测报告。普通预测只在 0-70 分内降质输出，连续年度窗口分别为 6/8/10/12 年，神级预测固定 100 分并标记 `future_peek_mode = true`。预测输出后会生成 0-100 的 `realized_report_quality_score` 审计分，并输出商务、休闲、探亲访友、长途和中转五类分项预测。
- 一键 run orchestration：baseline、occurred/counterfactual、归档输出和可选 viewer 发布。

当前边界：

- 暂时一次只激活一个分岔风险。
- viewer 已有 run browser；`--publish-viewer` 会生成版本化数据包并原子切换 Manifest，同时继续刷新 canonical 兼容数据。
- 当前已有北京、上海、广州、深圳、成都、重庆、杭州、南京、西安、武汉、昆明、郑州、厦门、长沙、青岛、天津、济南、福州、沈阳、大连、石家庄、哈尔滨、长春、太原、合肥、南昌、宁波、温州、贵阳、南宁、海口、三亚、乌鲁木齐、兰州、呼和浩特、银川、西宁、拉萨、珠海、泉州/晋江、烟台、无锡/苏州、潮汕、丽江、西双版纳、桂林、喀什写成可运行城市 JSON；中国大陆机场经营名单已基本闭合。
- 商业收入已经在北京季度经营样板中接入；商业销售预测、合同签约和玩家可见预测之间的动态闭环仍未完成。

## 最近验证

验证 run：

```powershell
py -3 .\macro_layers\macro_run_orchestrator_sim.py --seed 20260630 --years 60 --scenario-state occurred --scenario-branch-id auto --publish-viewer scenario --run-id macro_flow_demo_seed_20260630
```

结果：

```text
scenario: occurred_false_dawn_2043
global rows: 61
regional rows: 854
regions: 14
active global scenario rows: 7
active regional branch rows: 98
max reconciled growth gap: 0.0574 pp
max level gap after reconciliation: 0
```
