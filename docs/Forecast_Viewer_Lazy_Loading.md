# 有效客流预测 Viewer 按需加载

## 目的

北京有效客流预测 Viewer 原先在进入页面时一次加载全部报告数据。当前 canonical 数据约 7,018 行、13 份报告，单个 Viewer JS 约 37.9 MB。

现在页面先加载约 14 KB 的报告目录，再只读取当前选中报告的数据块。默认 `public_consensus` 数据块约 1.71 MB，首屏数据传输量下降约 95.5%。

这项修改只改变数据加载方式，不修改预测公式、字段值、报告排序、默认报告或页面显示结果。

## 输出结构

每次生成预测 Viewer 数据时会同时生成：

```text
<market_id>_forecast_index.js
<market_id>_forecast_chunks/
  r_<report_id>.json
<market_id>_potential_passenger_forecast_viewer_data.js
```

目录文件记录：

- Schema 版本。
- 总行数和 Seed。
- 默认报告。
- 报告顺序。
- 每个数据块的行数、字节数和 SHA-256。

每个数据块只包含一份 `forecast_report_id` 的全部 Seed 和发布年份数据。页面切换报告时才读取该块，并释放上一份报告的解析结果，避免内存持续增长。

## 兼容与发布

- 新版 Viewer 优先读取版本化 release 或 canonical 的轻量目录。
- 如果目录或新版 release 不存在，会自动回退旧完整 Viewer JS。
- Viewer release 会复制报告数据块，并在 bundle 中只放轻量目录，不再把约 37.9 MB 的完整预测数据嵌入 release bundle。
- canonical 兼容发布先复制数据块，最后复制目录指针，避免目录先指向尚未复制的数据。

旧完整 Viewer JS 暂时继续生成，用于兼容旧页面和外部工具。确认兼容窗口结束后，可以再评估停止生成该文件，以减少归档磁盘占用。

## Schema

对应协议：

```text
schemas/forecast-viewer-lazy-index.schema.json
schemas/forecast-viewer-report-chunk.schema.json
```

自动化测试会校验分块前后数据完全相同、行数和 SHA-256 正确、release/canonical 均包含数据块，以及旧单文件回退仍保留。
