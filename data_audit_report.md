# data_audit_report

- rows_cols: 421 x 57
- duplicate_rows: 0

## 缺失率(Top 15)

| 字段 | 缺失率 |
|---|---:|
| week11_judge4_score | 0.981 |
| week10_judge4_score | 0.933 |
| week11_judge2_score | 0.912 |
| week11_judge1_score | 0.912 |
| week11_judge3_score | 0.912 |
| week8_judge4_score | 0.869 |
| week9_judge4_score | 0.867 |
| week1_judge4_score | 0.808 |
| week7_judge4_score | 0.800 |
| week2_judge4_score | 0.793 |
| week5_judge4_score | 0.793 |
| week6_judge4_score | 0.765 |
| week4_judge4_score | 0.755 |
| week3_judge4_score | 0.746 |
| week10_judge2_score | 0.741 |

## 范围检查

| 字段 | 最小值 | 最大值 | 异常计数 | 说明 |
|---|---:|---:|---:|---|
| celebrity_age_during_season | 14 | 82 | 0 | 合理区间[10,100] |
| season | 1 | 34 | 0 | 合理区间[1,100] |
| placement | 1 | 16 | 0 | 合理区间[1,100] |
| judge_scores | 2.0 | 13.3333 | 0 | 负值应为0 |

## 约束与一致性

- results 与 placement 不一致条数: 0
- season 内 placement 非唯一或起点非1: 2 个season
- homestate 缺失率: 非美国 1.000, 美国 0.000

## 结构化字段检查

| status | 计数 |
|---|---:|
| eliminated | 298 |
| finalist | 113 |
| withdrew | 10 |

- exit_week 缺失率: 0.000
- exit_week_inferred=1: 123
- zero_placeholder=1: 303

## 长表审计

- long_rows_cols: 4631 x 17
- long_active_rate: 0.600
- long_judge_total_na_rate: 0.400
- long_zero_placeholder_rate: 0.307

## 关键统计量

- age_mean: 38.79
- age_median: 36.00
- avg_scores_overall_mean: 7.40
- avg_scores_overall_std: 1.33