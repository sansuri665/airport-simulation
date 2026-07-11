# Airport Workspace

这个目录当前承载机场游戏的全球/区域宏观基座、区域航空需求/供给层、中国大陆城市机场市场，以及北京机场经营、财务、税务、估值和有效客流预测样板。主流程已经从“逐层手动运行”整理为一键 macro run。

## 当前主入口

非计算机专业用户建议直接双击：

```text
start_airport_ui.bat
```

它会启动仅限本机访问的统一工作台：

```text
http://127.0.0.1:8776/
```

首页集中提供 Seed 动态测试、全球宏观、北京机场经营和有效客流预测四个入口，并显示当前 Viewer 发布模式、缓存 Run 和独立存档数量。关闭启动窗口或按 `Ctrl+C` 可停止服务；也可以运行 `stop_airport_ui.bat`。如果 8776 端口被其他程序占用，启动脚本只会提示，不会结束来源不明的进程。

终端中的统一入口是：

```powershell
py -3.13 -m airport_sim serve
```

项目统一使用 Python 3.13。`pyproject.toml`、Windows 启动脚本和自动化测试均以 3.13 为唯一支持版本；电脑中安装的其他 Python 版本不属于本项目运行环境。

命令行完整 Run 入口如下。

生成随机 seed 的完整 baseline run：

```powershell
py -3.13 -m airport_sim run --random-seed
```

生成固定 seed，并额外生成一条历史分岔发生路径：

```powershell
py -3.13 -m airport_sim run --seed 20260630 --scenario-state occurred --scenario-branch-id auto
```

生成发生路径，并发布到现有 HTML viewer 读取的输出目录：

```powershell
py -3.13 -m airport_sim run --seed 20260630 --scenario-state occurred --scenario-branch-id auto --publish-viewer scenario
```

单独重算已开放区域的航空需求层：

```powershell
py -3.13 .\macro_layers\regional_aviation_demand_layer_sim.py --region north_america
py -3.13 .\macro_layers\regional_aviation_demand_layer_sim.py --region china_mainland
py -3.13 .\macro_layers\regional_aviation_demand_layer_sim.py --region west_north_europe
py -3.13 .\macro_layers\regional_aviation_demand_layer_sim.py --region japan_korea
py -3.13 .\macro_layers\regional_aviation_demand_layer_sim.py --region southeast_asia
py -3.13 .\macro_layers\regional_aviation_demand_layer_sim.py --region south_asia_india
py -3.13 .\macro_layers\regional_aviation_demand_layer_sim.py --region hk_macao_taiwan
py -3.13 .\macro_layers\regional_aviation_demand_layer_sim.py --region middle_east_gulf
py -3.13 .\macro_layers\regional_aviation_demand_layer_sim.py --region oceania
py -3.13 .\macro_layers\regional_aviation_demand_layer_sim.py --region south_east_europe_mediterranean
py -3.13 .\macro_layers\regional_aviation_demand_layer_sim.py --region central_asia_turkey_eurasia
py -3.13 .\macro_layers\regional_aviation_demand_layer_sim.py --region north_africa
py -3.13 .\macro_layers\regional_aviation_demand_layer_sim.py --region latin_america_caribbean
py -3.13 .\macro_layers\regional_aviation_demand_layer_sim.py --region sub_saharan_africa
```

单独重算已开放区域的航空供给/满足率层：

```powershell
py -3.13 .\macro_layers\regional_air_capacity_supply_layer_sim.py --region north_america
py -3.13 .\macro_layers\regional_air_capacity_supply_layer_sim.py --region china_mainland
py -3.13 .\macro_layers\regional_air_capacity_supply_layer_sim.py --region west_north_europe
py -3.13 .\macro_layers\regional_air_capacity_supply_layer_sim.py --region japan_korea
py -3.13 .\macro_layers\regional_air_capacity_supply_layer_sim.py --region southeast_asia
py -3.13 .\macro_layers\regional_air_capacity_supply_layer_sim.py --region south_asia_india
py -3.13 .\macro_layers\regional_air_capacity_supply_layer_sim.py --region hk_macao_taiwan
py -3.13 .\macro_layers\regional_air_capacity_supply_layer_sim.py --region middle_east_gulf
py -3.13 .\macro_layers\regional_air_capacity_supply_layer_sim.py --region oceania
py -3.13 .\macro_layers\regional_air_capacity_supply_layer_sim.py --region south_east_europe_mediterranean
py -3.13 .\macro_layers\regional_air_capacity_supply_layer_sim.py --region central_asia_turkey_eurasia
py -3.13 .\macro_layers\regional_air_capacity_supply_layer_sim.py --region north_africa
py -3.13 .\macro_layers\regional_air_capacity_supply_layer_sim.py --region latin_america_caribbean
py -3.13 .\macro_layers\regional_air_capacity_supply_layer_sim.py --region sub_saharan_africa
```

单层模型命令继续作为开发调试兼容入口；普通使用者只需要 `airport_sim run` 和 `airport_sim serve`。

缓存盘点、预览和清理：

```powershell
python -m airport_sim cache list
python -m airport_sim cache plan
python -m airport_sim cache clean
python -m airport_sim cache clean --confirm
python -m airport_sim cache retention 2
```

`clean` 默认只预览或要求交互确认；显式 `--confirm` 才执行。8776 正在运行、当前 Viewer 发布、活动/staging Run、固定 Run 和 `saves/` 玩家存档均受保护。Seed Explorer 默认只保留最近 2 个有效缓存，可用 `cache pin RUN_ID` 固定例外。

orchestrator 的默认输出目录现在基于脚本所在的 `airport` 根目录解析，不再依赖当前工作目录：

```text
<airport>/output/macro_runs/
<airport>/output/
```

因此既可以在 `airport` 目录运行 `.\macro_layers\...`，也可以从父目录运行 `.\airport\macro_layers\...`。显式传入的 `--output-root` 和 `--viewer-output-root` 仍按用户给定的路径处理。

完整 Macro Run 现在先写入同一输出根目录下的隐藏 staging 目录。所有变体完成并通过核心 CSV 行数校验后，才原子改名为正式 `<run_id>`。中途计算或校验失败会清理本次 staging，不会留下看似完整的正式 Run；Run Index 也会忽略意外遗留的 staging 目录。显式指定已经存在的 `--run-id` 会报错，不再合并覆盖旧 Run。

统一版本记录位于：

```text
config/airport_versions.json
```

正式 Run Manifest 和 Seed Explorer API 会记录模型版本、输出/API Schema 版本及 Python 版本。API 新增字段均为向后兼容字段，不删除现有字段。

正式 JSON Schema 位于 `schemas/`。启动本地服务后，可通过以下接口查看 Schema 目录及 API 对应关系：

```text
http://127.0.0.1:8776/api/schema
```

详细说明见 `docs/architecture/API_and_JSON_Schema.md`。

## 查看界面

统一入口启动后可使用以下地址：

```text
http://127.0.0.1:8776/                       统一首页
http://127.0.0.1:8776/seed-explorer          Seed 动态测试
http://127.0.0.1:8776/global-gdp             全球宏观 Viewer
http://127.0.0.1:8776/beijing-operations     北京机场经营
http://127.0.0.1:8776/beijing-forecast       有效客流预测
```

五个页面源码统一位于 `web/pages/`，页面使用的 CSS 和 JavaScript 位于 `web/static/`。上述浏览器地址和旧的 `*.html` 兼容地址保持不变；正式 HTTP 服务实现位于 `airport_sim/server/app.py`。

旧的 Seed Explorer 启动脚本仍然保留，会调用统一入口并直接打开动态测试页：

```text
dynamic_tests/seed_explorer/start_seed_explorer.bat
```

Seed Explorer 的临时 Run 缓存在：

```text
output/seed_explorer_runs/
```

玩家动态测试存档独立保存在：

```text
saves/seed_explorer/
```

清理或强制重算缓存不会删除持久存档。服务启动时会把旧缓存目录中的 `dynamic_test_save.json` 复制迁移到新存档目录；旧文件暂时保留，直到对应缓存按正常策略清理。

完整 Run 缓存现在包含模型脚本、配置和 Python 环境指纹。依赖变化后，相同 Seed 的旧缓存会自动失效并重新计算。查看缓存列表本身不会再触发清理。

静态 Viewer 优先读取当前发布清单：

```text
output/current_viewer_manifest.js
output/viewer_releases/<release_id>/
```

一次发布会先在临时版本目录中生成三个 Viewer 数据包并计算 SHA-256，版本目录完成后再复制下面的 canonical 兼容输出，最后原子替换当前 Manifest 指针。这样页面只会看到完整的旧版本或完整的新版本，不会在发布中断时混用两次 Run 的数据。

为兼容旧页面和外部脚本，以下 canonical 输出仍会继续生成：

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

主 viewer 已在“航空需求”视图下读取 14 区航空供给/满足率输出，并显示分项旅客供给满足率。

北京机场经营面板当前读取北京季度经营、财务、估值和有效客流预测输出。建议通过 orchestrator 重算并发布 canonical viewer 数据：

```powershell
py -3.13 .\macro_layers\macro_run_orchestrator_sim.py --seed 20261324 --scenario-state none --publish-viewer baseline
```

orchestrator 默认只归档 run，不覆盖页面数据。需要更新页面数据时加：

```powershell
--publish-viewer baseline
--publish-viewer scenario
```

如果尚未做过新版发布，或者 Manifest 明确为空，三个静态 Viewer 会回退读取上述 canonical 文件。因此现有输出可以继续使用；下一次正常 `--publish-viewer` 后会自动切换到版本化数据包。

有效客流预测 Viewer 已率先改为按报告加载。当前 7,018 行、13 份报告的完整旧数据约 37.9 MB；新版首屏只加载约 14 KB 目录和约 1.71 MB 的默认报告数据，减少约 95.5%。切换报告时再加载对应 JSON 数据块，旧完整 JS 继续作为兼容回退。详见 `docs/architecture/Forecast_Viewer_Lazy_Loading.md`。

全球宏观 Viewer 现按区域加载宏观、航空需求和运力供给；北京经营 Viewer 将季度经营与财务状态保留为核心包，只在打开“估值曲线”时加载估值块。详见 `docs/architecture/Global_Viewer_Lazy_Loading.md` 和 `docs/architecture/Operations_Viewer_Lazy_Loading.md`。

## 输出结构

归档 run：

```text
output/macro_runs/<run_id>/
```

每个 run 通常包含：

```text
baseline/
occurred_<branch_id>_<trigger_year>/
manifest.json
```

每个变体内部都有全球宏观、14 区区域宏观、区域对账、区域航空需求和区域航空供给输出。

已配置的航空需求和航空供给区域会随 run 归档，目前包括：

```text
regional_aviation_demand/north_america/
regional_aviation_demand/china_mainland/
regional_aviation_demand/west_north_europe/
regional_aviation_demand/japan_korea/
regional_aviation_demand/southeast_asia/
regional_aviation_demand/south_asia_india/
regional_aviation_demand/hk_macao_taiwan/
regional_aviation_demand/middle_east_gulf/
regional_aviation_demand/oceania/
regional_aviation_demand/south_east_europe_mediterranean/
regional_aviation_demand/central_asia_turkey_eurasia/
regional_aviation_demand/north_africa/
regional_aviation_demand/latin_america_caribbean/
regional_aviation_demand/sub_saharan_africa/
regional_air_capacity_supply/north_america/
regional_air_capacity_supply/china_mainland/
regional_air_capacity_supply/west_north_europe/
regional_air_capacity_supply/japan_korea/
regional_air_capacity_supply/southeast_asia/
regional_air_capacity_supply/south_asia_india/
regional_air_capacity_supply/hk_macao_taiwan/
regional_air_capacity_supply/middle_east_gulf/
regional_air_capacity_supply/oceania/
regional_air_capacity_supply/south_east_europe_mediterranean/
regional_air_capacity_supply/central_asia_turkey_eurasia/
regional_air_capacity_supply/north_africa/
regional_air_capacity_supply/latin_america_caribbean/
regional_air_capacity_supply/sub_saharan_africa/
```

## 文档入口

文档已按层级收拢到 `docs/`：

1. `docs/architecture/Game_Overview.md`
2. `docs/README.md`
3. `docs/macro/README.md`
4. `docs/regional_macro/README.md`
5. `docs/regional_aviation/README.md`
6. `docs/airport_operations/README.md`

建议阅读顺序：

1. `docs/architecture/Game_Overview.md`
2. `docs/macro/Macro_Run_Orchestration.md`
3. `docs/macro/Global_Macro_Layer_Index.md`
4. `docs/regional_macro/Regional_Macro_Roadmap.md`
5. `docs/regional_macro/Regional_Branch_Transmission_Plan.md`
6. `docs/regional_macro/Regional_Macro_Reconciliation_Layer_Design.md`
7. `docs/regional_aviation/Regional_Aviation_Demand_Layer_Overview.md`
8. `docs/regional_aviation/Regional_Air_Capacity_Supply_Layer_Design.md`
9. `docs/airport_operations/City_Airport_Market_Layer_Plan.md`
10. `docs/airport_operations/City_Airport_Potential_Passenger_Forecast_System_Plan.md`

底层单层脚本仍保留在 `macro_layers/`，用于调试单独的全球层、区域层或对账层。

## 回归与 Smoke 测试

第一阶段安全重构使用 Python 标准库 `unittest`，不需要安装第三方测试框架：

```powershell
py -3.13 -B -m unittest discover -s tests -v
```

当前测试覆盖：

- 固定 Seed 的全球、区域、航空、北京城市客流、预测、经营、财务和估值数值特征。
- orchestrator 默认路径不依赖当前工作目录。
- 完整 Run 缓存指纹命中和失效。
- 旧动态存档迁移到独立持久目录。
- 查询缓存不触发删除，清理缓存不删除存档。
- 统一首页和四个主要页面的本地脚本资源完整性。
- 三个静态 Viewer 的版本化发布入口与旧数据回退。
- Viewer 发布包哈希、Manifest 切换及发布失败时指针不变。
- 单端口页面/API 路由、工作区状态接口和目录穿越防护。
- 启动脚本遇到未知端口占用时不会误杀其他进程。
- 固定 Seed 的城市市场与北京经营 API JSON 快照。
- 完整 Macro Run staging、核心行数校验、失败清理和原子正式化。
- 模型、Manifest、输出、API 和 Python 版本元数据一致性。
- JSON Schema 2020-12、Schema 安全路由和固定 Seed/真实 Manifest 协议验证。
- 有效客流预测目录、按报告 JSON 数据块、发布复制、数据等价和旧文件回退。

修整与重构的完整顺序见 `docs/refactoring/REFACTORING_GUIDE.md`。
