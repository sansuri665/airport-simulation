# IMPORTANT: City Airport Loan System Guide

这份文档记录城市机场一般贷款系统 v0.2。它已经接入北京样板的财务状态层和资产负债表界面，用来先跑通提款、付息、还本、负债、现金流、资产负债率定价和禁贷线。

真实 source of truth：

- `airport/macro_layers/city_airport_financial_state_layer_sim.py`
- `airport/config/city_airport_finance/beijing_airport_group_financial_state_v1.json`
- `airport/output/city_airport_financial_state/china_mainland/`
- `airport/web/pages/beijing_airport_operations_viewer.html`

## 当前结论

第一版只做一般贷款，不做项目贷款。

贷款用途可以由玩家自己理解为补充现金、支持翻新、新建或拆除重建，但账本上不强制绑定具体工程项目。这样先把融资、利息、还本和负债跑通，后续再接工程评估、商业预测、估值和银行风控。

## 贷款类型

短期贷款：

- 用于短期周转。
- 推荐期限：`1 - 3` 年，即 `4 - 12` 个季度。
- 默认还款方式：到期一次还本，按季度付息。
- 适合临时现金缺口，不适合长期航站楼建设。

长期贷款：

- 用于长期资本开支或现金缓冲。
- 推荐期限：`5 - 20` 年，即 `20 - 80` 个季度。
- 默认还款方式：等额本金。
- 可选还款方式：宽限期后等额本金。
- 适合翻新、新建、拆除重建这些会带来长期资产和长期现金流影响的支出。

## 还款方式

### 1. 到期一次还本，按期付息

配置值：`bullet_principal`

主要用途：短期贷款。

```text
每季度利息 = 期初贷款本金 * 年利率 / 4
每季度还本 = 0
到期季度还本 = 全部剩余本金
```

特点：

- 前期现金压力最小。
- 到期季度现金压力最大。
- 适合临时周转和等待再融资。

### 2. 等额本金

配置值：`equal_principal`

主要用途：长期贷款。

```text
每季度还本 = 初始本金 / 总还款季度数
每季度利息 = 期初剩余本金 * 年利率 / 4
每季度债务服务 = 每季度还本 + 每季度利息
```

特点：

- 本金稳定下降。
- 前期债务服务较高，后期逐渐降低。
- 账本最清楚，适合作为第一版长期贷款默认方式。

### 3. 宽限期后等额本金

配置值：`grace_then_equal_principal`

主要用途：有建设期或现金流缓冲需求的长期贷款。

```text
宽限期内：
  每季度利息 = 期初贷款本金 * 年利率 / 4
  每季度还本 = 0

宽限期后：
  每季度还本 = 初始本金 / (总还款季度数 - 宽限季度数)
  每季度利息 = 期初剩余本金 * 年利率 / 4
```

特点：

- 工程期现金压力更轻。
- 宽限期结束后还本压力集中释放。
- 适合测试“先建设、后偿还”的机场扩建节奏。

## 第一版字段

贷款配置字段：

- `loan_id`
- `loan_name`
- `loan_type`：`short_term` 或 `long_term`
- `enabled`：可选，默认启用。
- `start_year`
- `start_quarter`
- `principal_million_cny`
- `annual_interest_rate_pct`：可选；如果不填，则按利率模型在提款季度锁定利率。
- `tenor_quarters`
- `repayment_style`
  - `bullet_principal`
  - `equal_principal`
  - `grace_then_equal_principal`
- `grace_period_quarters`：仅宽限期模式需要。
- `purpose_note`

暂不需要：

- 抵押物。
- 银行评级。
- 项目绑定。
- 提前还款。
- 再融资。
- 违约和交叉违约。

## 利率模型

如果贷款没有显式填写 `annual_interest_rate_pct`，代码会在提款季度锁定年利率：

```text
贷款年利率
  = 区域宏观 10 年收益率
  + 短期/长期参考调整
  + 短期/长期利差
  + 高收益利差压力项
  + 城市风险利差
  + 资产负债率利差
```

字段来源：

- `input_10y_yield_pct` 来自季度经营层承接的区域宏观利率。
- `input_hy_spread_bps` 用于反映信用环境恶化时的压力。
- `loan_rate_model` 写在城市财务配置里，可以按城市覆盖。

第一版采用提款时锁定利率，不做浮动利率。宏观利率会影响新发贷款，不会追溯改变已提款贷款。

## 资产负债率定价

资产负债率口径：

```text
资产负债率 = 总负债 / 总资产
```

新增贷款定价使用“提款后资产负债率”，因为提款后现金增加，总资产增加，同时贷款本金增加，总负债增加。

当前采用分段线性曲线，而不是阶梯跳变。控制点如下：

| 提款后资产负债率控制点 | 新增贷款利率额外上升 |
|---:|---:|
| `45%` | `+0 bps` |
| `60%` | `+60 bps` |
| `70%` | `+150 bps` |
| `80%` | `+300 bps` |

区间内线性插值：

```text
45% - 60%：从 +0 bps 平滑上升到 +60 bps
60% - 70%：从 +60 bps 平滑上升到 +150 bps
70% - 80%：从 +150 bps 平滑上升到 +300 bps
```

举例：

- `50%` 资产负债率，额外利差约 `+20 bps`。
- `65%` 资产负债率，额外利差约 `+105 bps`。
- `75%` 资产负债率，额外利差约 `+225 bps`。
- `>= 80%` 不继续加价，而是禁止提款。

禁贷条件：

```text
如果提款前资产负债率 >= 80%，禁止新增贷款。
如果提款后资产负债率 >= 80%，禁止本次提款。
```

说明：

- 当前只按资产负债率做第一版信用约束，不接 DSCR、利息覆盖倍数、评级和抵押物。
- 如果贷款配置显式填写 `annual_interest_rate_pct`，视为合同利率已经定好，代码不会再自动追加资产负债率利差。
- 北京当前三笔测试贷款的资产负债率都很低，因此不会触发杠杆利差，也不会触发禁贷。

## 会计和现金流口径

提款：

```text
现金增加
短期/长期负债增加
不影响利润
```

付息：

```text
现金减少
利息费用增加
会计利润减少
留存收益减少
```

还本：

```text
现金减少
贷款本金减少
不影响利润
```

现金公式：

```text
period_financing_cash_flow
  = loan_drawdown
  - principal_repayment

period_end_cash
  = period_begin_cash
  + free_cash_flow_before_financing
  + period_financing_cash_flow
  - interest_payment
```

其中 `free_cash_flow_before_financing` 已经扣除 capex、拆除费用和当期现金所得税；现金所得税包含季度预缴以及 Q4 年度汇算补退。利息现金支出在贷款层单独扣除。

财务状态层输出：

- `period_interest_expense_million_cny`
- `period_interest_payment_million_cny`
- `period_principal_repayment_million_cny`
- `period_loan_drawdown_million_cny`
- `period_debt_service_million_cny`
- `short_term_debt_million_cny`
- `long_term_debt_million_cny`
- `loan_active_ids`
- `loan_drawdown_ids`
- `loan_principal_repayment_ids`
- `loan_weighted_interest_rate_pct`
- `loan_drawdown_weighted_interest_rate_pct`
- `loan_drawdown_leverage_before_pct`
- `loan_drawdown_leverage_after_pct`
- `loan_drawdown_leverage_spread_bps`
- `loan_blocked_ids`
- `loan_blocked_reasons`

债务分类第一版按 `loan_type` 分短期/长期，后续资产负债表更细时再做“一年内到期长期债务”的滚动重分类。

## 北京测试样例

动态测试融资事务 v0.1 复用本章的一般贷款引擎，向玩家提供三种标准产品：短期周转贷款（4/8/12 季、到期一次还本）、长期建设贷款（40/60/80 季、等额本金）和宽限期建设贷款（60/80 季、8/16 季宽限后等额本金）。确认提款后，贷款行动写入 seed 绑定行动日志并转换为 `general_loans`；经营报告债务与融资台账读取同一季度输出。首版每季最多一笔，融资额限制为 10-1000 亿元，不允许撤销、提前还款或置换。

北京动态测试的期限利差：短期周转 4/8/12 季分别 `+0/+15/+30bp`；长期建设 40/60/80 季分别 `+0/+20/+45bp`；宽限期建设 60/80 季同样为 `+20/+45bp`，并对 8/16 季宽限额外加 `+10/+25bp`。这些结构性利差与当季 10 年利率、信用压力和提款后杠杆加点共同构成界面报价；确认提款后全部锁定。

北京样板当前启用三笔测试贷款，用来验证三种还款方式，不代表正式开局必须负债：

- 短期贷款：`2030Q1` 提款，`2` 年，到期一次还本，按季度付息。
- 长期贷款 A：`2056Q1` 提款，`20` 年，按季度等额本金。
- 长期贷款 B：`2065Q3` 提款，`15` 年，前 `16` 个季度只付息，之后按季度等额本金。

资产负债表界面会显示贷款提款、还本、付息、债务服务、短债、长债、活跃贷款、资产负债率、提款前后杠杆、杠杆利差和被拒贷款。

## 后续扩展

以下内容等贷款账本稳定后再设计：

- 项目贷款。
- 更精细的债务上限和银行审批。
- 信用评级。
- DSCR / 利息覆盖倍数约束。
- 浮动利率。
- 提前还款。
- 再融资。
- 债务违约。
- 债券市场。
