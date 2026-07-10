# Regional Aviation Docs

区域航空层把区域宏观路径转成航空需求，再通过航司供给/运力满足率得到实际可服务客流。

## 入口

1. `Regional_Aviation_Demand_Layer_Overview.md`
2. `Regional_Air_Capacity_Supply_Layer_Design.md`

## 边界

区域航空需求层回答：

```text
这个区域想飞的人有多少，旅客结构如何，对价格多敏感。
```

区域航空供给层回答：

```text
这些潜在需求中有多少能被航司航班、座位和航线供给满足。
```

机场容量瓶颈属于下一层 `airport_operations/`。

## 代码位置

```text
airport/macro_layers/regional_aviation_demand_layer_sim.py
airport/macro_layers/regional_air_capacity_supply_layer_sim.py
```
