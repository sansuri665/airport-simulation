# 北京经营 Viewer 数据边界与估值按需加载

## 目的

北京经营 Viewer 使用三套 Python 输出：

- 季度经营：客流、容量、收入、成本和经营利润。
- 财务状态：现金、资产、折旧、贷款、税务和资产负债表。
- 估值预测：净资产口径和实验性 DCF 观察值。

默认“经营损益”总览同时使用季度经营与财务状态。如果把这两套数据继续拆开，首屏会短暂缺少余额、折旧或税务数字，因此它们被定义为经营核心包。估值只在“估值曲线”模式使用，现已改成点击后才加载。

这次修改只调整加载边界，不修改经营、财务或估值公式，也不改变页面已有数字。

## 输出结构

每个机场市场的季度经营目录新增：

```text
<market_id>_operations_index.js
<market_id>_operations_chunks/
  d_valuation.json
```

轻量目录记录：

- 季度经营和财务状态的核心行数。
- 估值块的行数、文件名、字节数和 SHA-256。
- 目录与数据块的 Schema 版本。

旧的完整估值 Viewer JS 继续生成和复制，用于旧页面、旧 release 和外部工具兼容。

## 页面行为

- 默认经营损益、客流容量、资产折旧和资产负债表不请求估值块。
- 第一次点击“估值曲线”时请求 `d_valuation.json`。
- 同一页面会话再次切换到估值曲线时复用内存数据，不重复请求。
- 加载或协议校验失败时保留当前视图，并在页头显示可理解的错误。
- 没有新版索引时自动回退原来的三个完整 JS。

## 原子发布

- 新 release 的经营 bundle 包含季度经营、财务状态、轻量目录和 release 信息。
- 估值 JSON 块与 release 一起发布，但不进入首屏 bundle。
- canonical 兼容目录先复制估值块，最后复制轻量目录指针。
- 旧 release 没有轻量目录时仍继续加载完整估值脚本。

## 真实验证

固定 Seed `424242`、2025 年起 12 年：

| 项目 | 大小 |
|---|---:|
| 原完整经营发布包估算 | 1,125,922 bytes |
| 新首屏经营发布包 | 925,279 bytes |
| 轻量目录 | 611 bytes |
| 按需估值块 | 192,688 bytes |

首屏下降约 17.8%。本次验证 Run 为 `operations_lazy_loading_validation`。

## Schema 与测试

```text
schemas/operations-viewer-lazy-index.schema.json
schemas/operations-viewer-chunk.schema.json
tests/test_operations_viewer_lazy_loading.py
```

测试会验证估值行在拆分前后完全相同、核心行数与 SHA-256 正确、release/canonical 发布顺序正确，以及旧版回退入口仍然存在。
