# 地图与交通网络预研

`map_research/` 是随仓库保存的独立静态预研，不属于 Airport 正式模型、配置、API、缓存或 Viewer 发布链。它可以与主版本一起提交，但版本号变化不会自动使这里的数据成为项目事实。

## 入口

- [`index.html`](index.html)：机场坐标、城市筛选和静态地图交互；
- [`railway.html`](railway.html)：铁路线路、站点和城市关系预研；
- [`City_Airport_Market_List_v0.1.md`](City_Airport_Market_List_v0.1.md)：从 Git 历史恢复的机场市场候选名单，仅作研究参考。

在仓库根目录启动独立静态服务：

```powershell
py -m http.server 8780 --directory map_research
```

随后访问 `http://127.0.0.1:8780/`。该服务与 Airport 正式的 `8776` 服务无关。

## 文件边界

| 文件 | 用途 |
| --- | --- |
| `airports.js` | 机场坐标与研究标签 |
| `transport_cities.js` | 机场/铁路预研共享的城市身份 |
| `app.js` | 机场地图交互 |
| `railways.js` | 铁路线路与站点研究数据 |
| `railway.js` | 铁路地图交互 |
| `style.css` | 两个预研页面共享样式 |

机场记录保留逐条来源标签；其中标为 OurAirports 的坐标来自其[开放数据下载](https://ourairports.com/data/)，该数据以 Public Domain 发布但不保证准确性或适用性。铁路坐标主要是用户提供的研究参考。当前恢复文件没有保存统一的抓取日期，因此未来用于正式配置前必须重新核对时点。提交前的语法检查会覆盖本目录 JavaScript，但这不等于坐标、线路状态或未来机场规划已经完成事实核验。

## 与正式项目的关系

- 正式机场市场仍以 [`config/city_airport_markets/`](../config/city_airport_markets/) 为准；
- 本目录不会被 `airport_sim/`、`macro_layers/`、Schema 或正式测试隐式读取；
- 未来若迁移某条数据，必须明确选择记录、核实来源和时点、建立 ID 映射，并在正式配置与测试中独立验收；
- 不允许用本目录的候选机场、铁路线路或坐标直接改变现有 Seed 的模型结果。
