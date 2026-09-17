import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CLEAN_DIR = BASE_DIR / 'cleaned'
CLEAN_PATH = CLEAN_DIR / 'cleaned_data.csv'
LONG_PATH = CLEAN_DIR / 'cleaned_long_weekly.csv'
REPORT_PATH = BASE_DIR / 'data_audit_report.md'

clean = pd.read_csv(CLEAN_PATH)
long_df = pd.read_csv(LONG_PATH)

lines = []
lines.append('# data_audit_report')
lines.append('')
lines.append(f'- rows_cols: {clean.shape[0]} x {clean.shape[1]}')
lines.append(f'- duplicate_rows: {int(clean.duplicated().sum())}')
lines.append('')

missing_rate = clean.isna().mean().sort_values(ascending=False)
lines.append('## 缺失率(Top 15)')
lines.append('')
lines.append('| 字段 | 缺失率 |')
lines.append('|---|---:|')
for col, rate in missing_rate.head(15).items():
    lines.append(f'| {col} | {rate:.3f} |')
lines.append('')

lines.append('## 范围检查')
lines.append('')
lines.append('| 字段 | 最小值 | 最大值 | 异常计数 | 说明 |')
lines.append('|---|---:|---:|---:|---|')

def count_outside(series, low=None, high=None):
    s = series.dropna()
    if low is None and high is None:
        return 0
    mask = pd.Series([False] * len(s))
    if low is not None:
        mask = mask | (s < low)
    if high is not None:
        mask = mask | (s > high)
    return int(mask.sum())

lines.append(f"| celebrity_age_during_season | {clean['celebrity_age_during_season'].min()} | {clean['celebrity_age_during_season'].max()} | {count_outside(clean['celebrity_age_during_season'], 10, 100)} | 合理区间[10,100] |")
lines.append(f"| season | {clean['season'].min()} | {clean['season'].max()} | {count_outside(clean['season'], 1, 100)} | 合理区间[1,100] |")
lines.append(f"| placement | {clean['placement'].min()} | {clean['placement'].max()} | {count_outside(clean['placement'], 1, 100)} | 合理区间[1,100] |")

score_cols = [c for c in clean.columns if c.startswith('week') and c.endswith('_score')]
score_min = clean[score_cols].min().min()
score_max = clean[score_cols].max().max()
neg_count = int((clean[score_cols] < 0).sum().sum())
lines.append(f"| judge_scores | {score_min} | {score_max} | {neg_count} | 负值应为0 |")
lines.append('')

lines.append('## 约束与一致性')
lines.append('')
place_results = clean[clean['results'].str.contains('Place')].copy()
place_results['place_num'] = place_results['results'].str.extract(r'(\d+)').astype(int)
mis_place = int((place_results['placement'] != place_results['place_num']).sum())
lines.append(f'- results 与 placement 不一致条数: {mis_place}')

season_checks = clean.groupby('season')['placement'].agg(['min', 'max', 'nunique', 'count'])
issue = season_checks[(season_checks['min'] != 1) | (season_checks['nunique'] != season_checks['count'])]
lines.append(f'- season 内 placement 非唯一或起点非1: {len(issue)} 个season')

missing_state_non_us = clean[clean['celebrity_homecountry/region'] != 'United States']['celebrity_homestate'].isna().mean()
missing_state_us = clean[clean['celebrity_homecountry/region'] == 'United States']['celebrity_homestate'].isna().mean()
lines.append(f'- homestate 缺失率: 非美国 {missing_state_non_us:.3f}, 美国 {missing_state_us:.3f}')
lines.append('')

lines.append('## 结构化字段检查')
lines.append('')
status_counts = clean['status'].value_counts(dropna=False)
lines.append('| status | 计数 |')
lines.append('|---|---:|')
for k, v in status_counts.items():
    lines.append(f'| {k} | {int(v)} |')
lines.append('')

exit_missing = clean['exit_week'].isna().mean()
lines.append(f'- exit_week 缺失率: {exit_missing:.3f}')
lines.append(f"- exit_week_inferred=1: {int(clean['exit_week_inferred'].sum())}")
lines.append(f"- zero_placeholder=1: {int(clean['zero_placeholder'].sum())}")
lines.append('')

lines.append('## 长表审计')
lines.append('')
lines.append(f'- long_rows_cols: {long_df.shape[0]} x {long_df.shape[1]}')
lines.append(f"- long_active_rate: {long_df['active'].mean():.3f}")
lines.append(f"- long_judge_total_na_rate: {long_df['judge_total'].isna().mean():.3f}")
lines.append(f"- long_zero_placeholder_rate: {long_df['zero_placeholder'].mean():.3f}")
lines.append('')

lines.append('## 关键统计量')
lines.append('')
lines.append(f"- age_mean: {clean['celebrity_age_during_season'].mean():.2f}")
lines.append(f"- age_median: {clean['celebrity_age_during_season'].median():.2f}")
lines.append(f"- avg_scores_overall_mean: {clean[score_cols].mean(axis=1).mean():.2f}")
lines.append(f"- avg_scores_overall_std: {clean[score_cols].mean(axis=1).std():.2f}")

REPORT_PATH.write_text('\n'.join(lines), encoding='utf-8')
print('audit done')
