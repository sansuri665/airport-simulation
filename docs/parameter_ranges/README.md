# Parameter Range Docs

这个目录存放重要调参范围和代码索引。修改宏观、区域宏观、区域航空需求/供给、城市机场客流、季度机场经营参数前，优先看这里。

## 重要文档

- `IMPORTANT_Macro_Regional_Aviation_Parameter_Range_Guide.md`：前四层参数范围、代码入口和调参注意事项。
- `IMPORTANT_City_Airport_Market_Parameter_Range_Guide.md`：城市机场客流层参数范围、区域模板、槽位规则和特殊机场覆盖原则。
- `IMPORTANT_City_Airport_Quarterly_Operations_Parameter_Range_Guide.md`：季度机场经营层参数范围，重点记录翻新费用、工期、施工期容量折扣和维护年龄前推的区域/城市差异。
- `IMPORTANT_City_Airport_Financial_State_Layer_Guide.md`：城市机场财务状态层、资产负债表、现金流、折旧和留存收益的会计边界。
- `IMPORTANT_City_Airport_Loan_System_Guide.md`：城市机场一般贷款系统规划，记录短期贷款、长期贷款、还款方式、利息、还本和资产负债表接入边界。
- `IMPORTANT_City_Airport_Valuation_Forecast_Model_Guide.md`：城市机场估值、游戏内预测、商业销售预测和合同签约模型总草案。
- `../airport_operations/City_Airport_Potential_Passenger_Forecast_System_Plan.md`：城市有效客流预测系统计划，记录潜在/航司供给取小值、分项结构、初级/中级/高级/神级预测、seed 曲线降质、预测误差和下游边界。

## 边界

这里记录的是调参记忆和安全边界，不是最终经济标定。更细的商业合同和资产负债表参数仍可继续放在 `airport_operations/` 或后续独立参数文档中。
