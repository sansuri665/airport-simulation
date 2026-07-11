# 全球宏观 Viewer 按区域加载

## 目的

全球宏观 Viewer 原先在进入页面时一次加载 14 个区域的三组数据：区域宏观、航空需求和运力供给。即使用户只查看全球总览，浏览器也会下载并解析全部区域数据。

现在首屏只加载全球宏观主链、区域协调结果和约 4 KB 的区域目录。用户切换到某个区域，或进入区域航空视图时，页面才读取该区域的一个 JSON 数据块。模型公式、字段、行值、区域顺序和页面默认的全球总览均未改变。

12 年、固定 Seed `424242` 的真实发布验证结果：

| 项目 | 大小 |
|---|---:|
| 原完整全球发布包估算 | 2,639,324 bytes |
| 新首屏全球发布包 | 907,031 bytes |
| 轻量区域目录 | 4,136 bytes |
| 中国大陆区域块 | 123,946 bytes |
| 14 个区域块合计 | 1,737,272 bytes |

首屏发布包下降约 65.6%。进入一个区域后只增加该区域的数据，不会把其余 13 个区域一起载入。

## 输出结构

每个 Macro Run 的 `global_macro` 目录新增：

```text
global_viewer_index.js
global_viewer_chunks/
  r_north_america.json
  r_china_mainland.json
  ...共 14 个区域
```

轻量目录记录每个区域的名称、三组行数、文件名、字节数和 SHA-256。每个区域块包含：

- `regionalMacroRows`：区域宏观行。
- `aviationDemandRows`：区域航空需求行。
- `airCapacitySupplyRows`：区域运力供给行。

将同一区域的三组数据放在一个块内，可以保证航空需求与运力供给在同一次切换中就绪，也减少多次网络请求。

## 页面行为

- 默认“全球 / 宏观”视图不加载任何区域块。
- 切换到区域宏观时，加载该区域块并建立区域宏观数据集。
- 切换到航空视图时，加载目标区域块，并将航空需求与供给按 Seed 和年份合并。
- 已加载区域保留在当前页面会话中，再次切换不重复请求。
- 切换到新版归档 Run 时继续按区域加载；旧归档没有轻量目录时回退原来的逐脚本加载。

## 兼容与原子发布

- 新 release 的全球 bundle 只包含全球主链、协调结果、轻量目录和 release 信息。
- 14 个区域块随 release 一起复制。
- canonical 兼容目录先复制数据块，最后复制 `global_viewer_index.js` 指针，避免目录指向尚未就绪的块。
- 原有区域 JS 继续生成和复制，供旧页面、旧归档和外部脚本使用。
- 页面找不到新版目录时会自动执行原有完整脚本模板。

## Schema 与验证

对应协议：

```text
schemas/global-viewer-lazy-index.schema.json
schemas/global-viewer-region-chunk.schema.json
```

`tests/test_global_viewer_lazy_loading.py` 验证三组行数据在拆分前后完全相同、行数与 SHA-256 正确、release 和 canonical 都包含 14 个块，并确认旧版回退入口仍保留。

真实运行使用 `global_lazy_loading_validation`，固定 Seed `424242`、2025 年起 12 年；完整测试共 35 项通过。
