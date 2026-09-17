# cleaning_log

- raw_file: 2026_MCM_Problem_C_Data.csv
- rows_cols_raw: 421 x 53
- rows_cols_clean: 421 x 57

## 规则记录

| 规则ID | 字段 | 检测逻辑 | 处理方式 | 影响行数 | 影响单元格 | 典型示例 |
|---|---|---|---|---:|---:|---|
| R1 | 文本字段(全部) | 首尾空格 | strip() 去除空格 | 2 | 2 | row 42 celebrity_name: 'Floyd Mayweather Jr. ' -> 'Floyd Mayweather Jr.' |
| R2 | 文本字段(全部) | 空字符串 | 转为 NaN | 0 | 0 | 无 |
| R3 | celebrity_industry | 拼写异常(Beauty Pagent) | 统一为 Beauty Pageant | 1 | 1 | row 32 celebrity_industry: 'Beauty Pagent' -> 'Beauty Pageant' |
| R4 | week*_judge*_score | 原始值=0 | 新增 zero_placeholder(行级标记) | 303 | 4671 | 任意原始0的位置被标记 |
| R5 | week*_judge*_score | 值=0 | 改为 NaN(占位) | 303 | 4671 | row 2 week4_judge1_score: 0 -> NaN |
| R6 | 数值字段(全部) | 无法解析为数值 | 强制转为 NaN | 0 | 0 | 无 |
| R7 | results | 文本解析(Eliminated/Withdrew/Place) | 生成 status/exit_week/exit_week_inferred | 421 | 421 | row 24 results: 'Withdrew' -> status=withdrew, exit_week=5 |
| R8 | week*_judge*_score | 宽表到长表 | 生成 cleaned_long_weekly.csv(judge_total/num_judges/active) | 4631 | 2777 | 全NaN周次保持为NaN(不误判为0) |

## 典型实例(>=5)

- row 42 | Floyd Mayweather Jr. | celebrity_name: Floyd Mayweather Jr.  -> Floyd Mayweather Jr. | 理由: 去除首尾空格
- row 398 | Dwight Howard | celebrity_name: Dwight Howard  -> Dwight Howard | 理由: 去除首尾空格
- row 32 | Shandi Finnessey | celebrity_industry: Beauty Pagent -> Beauty Pageant | 理由: 拼写规范化
- row 2 | Evander Holyfield | week4_judge1_score: 0 -> nan | 理由: 0分视为“未评分/未出场”
- row 2 | Evander Holyfield | week4_judge2_score: 0 -> nan | 理由: 0分视为“未评分/未出场”
- row 204 | Diana Nyad | exit_week: 由分数推断可能为1 -> 2 | 理由: results 显式给出 Eliminated Week 2
- 
- [2026-01-30] Modeling-time cleaning additions (Plan A):
- Rule R9 | field: ballroom_partner | issue: parenthetical notes or multiple names ("/", "(week 9)") | action: remove parentheses, split on "/" and keep primary name; add pro_switch_flag | rows affected: 66
- Examples:
- row 517 | ballroom_partner: "Alan Bersten (Rashad Jennings week 9)" -> "Alan Bersten"
- row 588 | ballroom_partner: "Emma Slater/Kaitlyn Bristowe (week 9)" -> "Emma Slater"
