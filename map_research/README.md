# 地图与交通网络预研

`map_research/` 是随仓库保存的独立静态预研，不属于 Airport 正式模型、配置、API、缓存或 Viewer 发布链。它可以与主版本一起提交，但版本号变化不会自动使这里的数据成为项目事实。

## 入口

- [`railway.html`](railway.html)：中国大陆 / 港澳台铁路线路与站点查看
- [`index.html`](index.html)：跳转到铁路页

在仓库根目录启动独立静态服务：

```powershell
py -m http.server 8780 --directory map_research
```

随后访问 `http://127.0.0.1:8780/`。该服务与 Airport 正式的 `8776` 服务无关。

## 文件边界

| 文件 | 用途 |
| --- | --- |
| `railways.js` | 中国大陆 / 港澳台铁路线路与站点 |
| `railway.js` | 铁路地图查看交互 |
| `railway.html` | 铁路预研页面 |
| `style.css` | 页面样式 |

## 范围

只保留 `china_mainland`、`hk_macao_taiwan`，以及二者之间的跨区域线路。界面提供线路/站点列表、区域筛选、地图缩放平移与选中查看。机场预研、路径规划与旅行记录已移除。

铁路坐标主要是用户提供的研究参考。提交前的语法检查会覆盖本目录 JavaScript，但这不等于坐标或线路状态已经完成事实核验。

## 与正式项目的关系

- 正式机场市场仍以 [`config/city_airport_markets/`](../config/city_airport_markets/) 为准；
- 本目录不会被 `airport_sim/`、`macro_layers/`、Schema 或正式测试隐式读取；
- 未来若迁移某条数据，必须明确选择记录、核实来源和时点、建立 ID 映射，并在正式配置与测试中独立验收；
- 不允许用本目录的候选线路或坐标直接改变现有 Seed 的模型结果。
