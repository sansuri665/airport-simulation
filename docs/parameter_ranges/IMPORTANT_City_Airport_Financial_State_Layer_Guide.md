# IMPORTANT: City Airport Financial State Layer Guide

这份文档记录城市机场财务状态层 v0.4 的会计边界。它服务于资产负债表、后续估值模型、拆除重建和融资系统。

真实 source of truth：

- `airport/macro_layers/city_airport_financial_state_layer_sim.py`
- `airport/config/city_airport_finance/beijing_airport_group_financial_state_v1.json`
- `airport/output/city_airport_financial_state/china_mainland/`
- `airport/web/pages/beijing_airport_operations_viewer.html`

贷款系统规划另见：

- `airport/docs/parameter_ranges/IMPORTANT_City_Airport_Loan_System_Guide.md`

## 当前设计

财务状态层是季度经营层的下游层：

```text
城市机场季度经营层
  -> 经营利润
  -> 会计折旧
  -> capex / 在建工程 / 转固
  -> 现金
  -> 固定资产账面值
  -> 负债
  -> 权益 / 留存收益
  -> 资产负债表
```

v0.4 已经接入一般贷款账本和资产负债率定价。北京样板启用三笔测试贷款，用来验证短期到期一次还本、长期等额本金、长期宽限后等额本金三种还款方式。

贷款系统仍然保持轻量：只处理一般贷款、提款时利率锁定、资产负债率利差和禁贷线，不处理项目贷款、评级、再融资和违约。

## 北京样板

北京机场集团配置在：

```text
airport/config/city_airport_finance/beijing_airport_group_financial_state_v1.json
```

当前初始现金：

```text
opening_cash_million_cny = 18000
```

这是游戏口径，不是现实财报。它的作用是：

- 能覆盖 2025-2029 自动经营历史。
- 能覆盖样本翻新。
- 不让后期新建航站楼 capex 完全无感。

北京初始固定资产来自三个既有主力槽位：

- 北京首都 `PEK_SLOT_1`（主槽位）：首都T3航站楼，`extra_large`，2008 投用。
- 北京首都 `PEK_SLOT_2`（次槽位）：首都T2航站楼，`large`，2000 投用。
- 北京大兴 `PKX_SLOT_1`（主槽位）：大兴T1航站楼，`giant`，2019 投用。

这些资产现在属于财务状态配置，不应长期只写在 viewer 里。

## 会计口径

季度经营层的：

```text
quarter_operating_profit_million_cny
```

在本层视为折旧前经营利润。

财务状态层再计算：

```text
period_pretax_accounting_profit
  = period_operating_profit
  - period_accounting_depreciation
  - rebuild_demolition_expense
  - rebuild_old_asset_writeoff
  - interest_expense

period_income_tax_prepayment
  = max(period_pretax_accounting_profit, 0)
  * corporate_income_tax_rate_pct
  * quarterly_prepayment_ratio

Q4 年度汇算：

annual_taxable_income_after_loss
  = max(annual_pretax_accounting_profit - tax_loss_used, 0)

annual_income_tax_payable
  = annual_taxable_income_after_loss
  * corporate_income_tax_rate_pct

period_income_tax_settlement
  = annual_income_tax_payable
  - annual_income_tax_prepayment

period_income_tax_expense
  = period_income_tax_prepayment
  + period_income_tax_settlement

period_accounting_profit
  = period_pretax_accounting_profit
  - period_income_tax_expense
```

亏损结转：

```text
如果 annual_pretax_accounting_profit < 0：
  tax_loss_generated = -annual_pretax_accounting_profit

如果未来年度 annual_pretax_accounting_profit > 0：
  按 FIFO 使用未过期 tax_loss_carryforward

tax_loss_carryforward_years = 5
```

亏损结转只影响年度汇算，不在季度预缴时提前抵扣。当前不确认递延所得税资产。

其中折旧包括：

- 初始固定资产折旧。
- 翻新资产折旧。
- 新建资产折旧。
- 重建资产折旧。

拆除重建费用和核销：

- `period_rebuild_demolition_expense_million_cny` 是期间费用，影响会计利润和现金流，不形成资产。
- `period_rebuild_old_initial_asset_writeoff_million_cny` 是被拆槽位旧初始资产账面净值核销，影响会计利润，不影响现金。
- `period_rebuild_old_renovation_asset_writeoff_million_cny` 是被拆槽位旧翻新资产账面净值核销，影响会计利润，不影响现金。
- `period_rebuild_old_asset_writeoff_million_cny` 是上述两类核销合计。

留存收益：

```text
retained_earnings_end
  = retained_earnings_begin
  + period_accounting_profit
```

现金：

```text
period_free_cash_flow_before_financing
  = period_operating_profit
  - period_total_capex_outlay
  - rebuild_demolition_expense
  - period_cash_tax_paid

period_end_cash
  = period_begin_cash
  + period_free_cash_flow_before_financing
  + period_financing_cash_flow
  - interest_payment
```

融资现金流：

```text
period_financing_cash_flow
  = period_loan_drawdown
  - period_principal_repayment
```

利息作为现金流支出单独扣除，同时进入会计利润。还本不影响利润。
当前简化税务按企业所得税 25% 计算；季度预缴、Q4 汇算，亏损 5 年结转，暂不确认递延所得税资产或负债。

## 资产负债表

当前资产：

- 现金。
- 固定资产账面净值。
- 在建工程。

当前负债：

- 短期债务，来自 `loan_type = short_term` 的一般贷款余额。
- 长期债务，来自 `loan_type = long_term` 的一般贷款余额，以及以后可选的自动兜底融资。

当前权益：

- 期初投入资本。
- 留存收益。

平衡关系：

```text
total_assets
  = total_liabilities
  + total_equity
```

输出字段 `balance_check_million_cny` 应接近 `0`。

## 与其它机制的关系

翻新：

- 施工期产生 capex 和在建工程。
- 完工后转入翻新资产。
- 折旧进入会计利润。

新建航站楼：

- 施工期产生 capex 和在建工程。
- 完工后转入新建资产。
- 折旧进入会计利润。

拆除重建：

- 已实现 v0.1 会计处理。
- 重建 capex 由季度经营层输出，施工期进入在建工程，完工后进入重建资产并折旧。
- 拆除费用当期费用化，减少现金和留存收益。
- 被拆槽位旧初始资产由本层按 `rebuild_started_slot_ids` 找到并核销。
- 被拆槽位旧翻新资产由季度经营层计算核销额，本层读取后进入会计利润。
- 当前没有 salvage / 处置收入。若以后加入，应作为现金流和处置损益单独建字段。

一般贷款：

- 已实现 v0.1 账本。
- 财务配置中的 `general_loans` 按季度展开为提款、付息、还本和期末债务余额。
- v0.2 增加资产负债率利差和硬禁贷线。
- 如果贷款不填写显式利率，会读取季度经营层传来的 `input_10y_yield_pct` 和 `input_hy_spread_bps`，按城市配置里的 `loan_rate_model` 在提款季度锁定利率。
- 当前资产负债率定价改为分段线性曲线：`45%: +0 bps`，`60%: +60 bps`，`70%: +150 bps`，`80%: +300 bps`，区间内线性插值。
- 如果提款前或提款后资产负债率达到 `80%`，本次新增贷款会被拒绝提款。
- `auto_borrow_on_negative_cash` 当前在北京配置中关闭。若现金为负，应先作为警告暴露，而不是自动融资掩盖问题。

估值模型：

- 尚未实现。
- 后续可以从本层读取现金、固定资产净值、留存收益、自由现金流、会计利润和债务状态。

## 后续扩展

建议顺序：

1. 保持北京有债务样例账本稳定。
2. 加入估值模型 v0.1。
3. 再加入债务上限、利息覆盖、再融资和信用约束。
4. 扩展到上海、广州、深圳、重庆等城市。
