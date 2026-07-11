# 项目瘦身执行审计（2026-07-11）

## 执行前

- 正式 `output/`：681,842,045 字节，5,835 个文件。
- 旧嵌套 `airport/airport/output/`：98,916,210 字节，583 个文件。
- 玩家存档：2 个，共 1,862 字节。
- 当前 Viewer release：`operations_lazy_loading_validation_baseline_20260711_142132_589721500`。
- 当前 Viewer 来源 Run：`operations_lazy_loading_validation`。
- 8776 和 8876 均未监听；没有 `.staging_*`。

## 保护基线

- `seed_20260716_years_60` 存档 SHA-256：`F0E4FF9F937DD71DB107C5B31BBC175EA90A2EBA16E6642846A5BD5B4B3039C8`。
- `seed_20261939_years_60` 存档 SHA-256：`0D1CCAFF0BB005D00016D2CF61B542A450FC6A7237FB4B7B700CBC074C56803A`。
- `current_viewer_manifest.js` SHA-256：`6F32370C723B5764AF409153F50374E027712D8D21BF40F90AC4D8BDAB120987`。
- `current_viewer_manifest.json` SHA-256：`42B67E25CB91C0F5321721B38E85ABFAFCF2C2928C697217CB58FC7C7C17F0DF`。

## 自动清理

`python -m airport_sim cache clean --confirm` 删除 33 个经过计划分类的目标，释放 624,906,748 字节，失败数为 0。删除内容包括：

- 4 个指纹失效的旧 Seed Explorer 完整缓存。
- 26 个早期 test/smoke/probe/draft/eval 输出目录。
- 1 个未引用的旧 Macro Run。
- 1 个未引用的旧 Viewer release。
- 1 个已经迁空的旧保存目录。

当前 Manifest 指向的 release 和来源 Run没有进入候选列表，玩家存档位于 `saves/`，也没有进入删除边界。

## 旧嵌套输出

旧嵌套输出包含两个过期 smoke Run，当前源码和测试均无引用。删除前已压缩到工作区外：

```text
C:\d_e\oiltanker\_airport_slimming_backups\legacy_nested_output_20260711.zip
```

- 压缩包大小：10,113,415 字节。
- SHA-256：`E06A0AA974C17BF6BAFCD8776DF8EF5AC7234FD777B2C1510281575F4305B414`。

压缩包验证成功后，`airport/airport/output/` 及其空父目录已删除。

## Artifact profile 对照

使用相同 Seed `20261324`、相同 2 年参数分别运行 `full` 和 `seed-cache`：

- CSV：94 对 94。
- 缺失 CSV：0。
- 额外 CSV：0。
- 哈希不同 CSV：0。
- `full` JS 文件：95。
- `seed-cache` JS 文件：0。
- `full` 总字节：3,031,016。
- `seed-cache` 总字节：910,321。
- 样本减小：70%。

该对照说明精简的是静态展示副本，模型/API CSV 结果没有变化。

## 最终状态

- 正式 `output/`：58,360,695 字节（55.66 MiB），935 个文件。
- 旧嵌套 `airport/airport/output/`：已移除，工作区外保留上述可校验压缩备份。
- 当前 Seed Explorer 缓存：1 个，为 `seed_20261324_years_5`；大小 1,432,896 字节，JS 文件 0，缓存指纹有效。
- 再次执行只读清理计划：候选数 0，可释放字节数 0。
- 当前 Viewer 三个 bundle 的文件哈希均与 Manifest 相符。
- 两个玩家存档及两个当前 Viewer Manifest 的 SHA-256 与保护基线完全一致。
- 8776 浏览器验收结束后已主动关闭；8876 也未监听。

相较执行前两个输出根目录合计，机场工作区内约减少 689 MiB；工作区外另保留约 9.65 MiB 的旧输出压缩备份，以便必要时追溯。
