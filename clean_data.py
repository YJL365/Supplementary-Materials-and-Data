import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BASE_DIR = Path(__file__).resolve().parent
RAW_PATH = BASE_DIR / 'raw' / '2026_MCM_Problem_C_Data.csv'
CLEAN_DIR = BASE_DIR / 'cleaned'
CLEAN_PATH = CLEAN_DIR / 'cleaned_data.csv'
LONG_PATH = CLEAN_DIR / 'cleaned_long_weekly.csv'
LOG_PATH = BASE_DIR / 'cleaning_log.md'
FIG_DIR = BASE_DIR / 'derived' / 'figures'
CLEAN_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

raw = pd.read_csv(RAW_PATH)
clean = raw.copy()

log_entries = []
example_records = []

# R1: strip whitespace in object columns
obj_cols = clean.select_dtypes(include='object').columns
before_obj = clean[obj_cols].copy()
clean[obj_cols] = clean[obj_cols].apply(lambda col: col.str.strip())
changed_mask = (before_obj != clean[obj_cols]) & ~(before_obj.isna() & clean[obj_cols].isna())
rows_affected = int(changed_mask.any(axis=1).sum())
cell_affected = int(changed_mask.sum().sum())
example = ''
if cell_affected > 0:
    idxs = np.argwhere(changed_mask.values)
    idx, col_idx = idxs[0]
    col = obj_cols[col_idx]
    example = f"row {int(idx)} {col}: '{before_obj.iloc[idx, col_idx]}' -> '{clean.iloc[idx, col_idx]}'"
    for i in range(min(2, len(idxs))):
        r, c = idxs[i]
        example_records.append({
            'row_index': int(r),
            'celebrity_name': clean.loc[r, 'celebrity_name'],
            'field': obj_cols[c],
            'before': before_obj.iloc[r, c],
            'after': clean.iloc[r, c],
            'reason': '去除首尾空格'
        })
log_entries.append({
    'rule_id': 'R1',
    'field': '文本字段(全部)',
    'detection': '首尾空格',
    'action': 'strip() 去除空格',
    'rows_affected': rows_affected,
    'cells_affected': cell_affected,
    'example': example or '无'
})

# R2: blank strings -> NaN
blank_mask = clean[obj_cols].apply(lambda col: col.str.strip().eq(''))
blank_cells = int(blank_mask.sum().sum())
blank_rows = int(blank_mask.any(axis=1).sum())
if blank_cells > 0:
    clean[obj_cols] = clean[obj_cols].mask(blank_mask, np.nan)
example = ''
if blank_cells > 0:
    idxs = np.argwhere(blank_mask.values)
    idx, col_idx = idxs[0]
    col = obj_cols[col_idx]
    example = f"row {int(idx)} {col}: '' -> NaN"
    example_records.append({
        'row_index': int(idx),
        'celebrity_name': clean.loc[idx, 'celebrity_name'],
        'field': col,
        'before': '',
        'after': np.nan,
        'reason': '空字符串视为缺失'
    })
log_entries.append({
    'rule_id': 'R2',
    'field': '文本字段(全部)',
    'detection': '空字符串',
    'action': '转为 NaN',
    'rows_affected': blank_rows,
    'cells_affected': blank_cells,
    'example': example or '无'
})

# R3: industry typo normalization (optional micro-fix)
industry_before = clean['celebrity_industry'].copy()
clean['celebrity_industry'] = clean['celebrity_industry'].replace({
    'Beauty Pagent': 'Beauty Pageant'
})
industry_changed = (industry_before != clean['celebrity_industry']).sum()
example = '无'
if industry_changed > 0:
    idx = industry_before[industry_before != clean['celebrity_industry']].index[0]
    example = f"row {int(idx)} celebrity_industry: '{industry_before.loc[idx]}' -> '{clean.loc[idx, 'celebrity_industry']}'"
    example_records.append({
        'row_index': int(idx),
        'celebrity_name': clean.loc[idx, 'celebrity_name'],
        'field': 'celebrity_industry',
        'before': industry_before.loc[idx],
        'after': clean.loc[idx, 'celebrity_industry'],
        'reason': '拼写规范化'
    })
log_entries.append({
    'rule_id': 'R3',
    'field': 'celebrity_industry',
    'detection': '拼写异常(Beauty Pagent)',
    'action': '统一为 Beauty Pageant',
    'rows_affected': int(industry_changed),
    'cells_affected': int(industry_changed),
    'example': example
})

# Score columns
score_cols = [c for c in clean.columns if c.startswith('week') and c.endswith('_score')]
weeks = sorted({int(c.split('_')[0].replace('week', '')) for c in score_cols})

# R4: add zero_placeholder flag (based on raw zeros)
zero_placeholder_row = (raw[score_cols] == 0).any(axis=1).astype(int)
clean['zero_placeholder'] = zero_placeholder_row
log_entries.append({
    'rule_id': 'R4',
    'field': 'week*_judge*_score',
    'detection': '原始值=0',
    'action': '新增 zero_placeholder(行级标记)',
    'rows_affected': int(zero_placeholder_row.sum()),
    'cells_affected': int((raw[score_cols] == 0).sum().sum()),
    'example': '任意原始0的位置被标记'
})

# R5: 0 scores -> NaN
zero_mask = clean[score_cols] == 0
zero_cells = int(zero_mask.sum().sum())
zero_rows = int(zero_mask.any(axis=1).sum())
idxs = np.argwhere(zero_mask.values)
if zero_cells > 0:
    for i in range(min(2, len(idxs))):
        r, c = idxs[i]
        col = score_cols[c]
        example_records.append({
            'row_index': int(r),
            'celebrity_name': clean.loc[r, 'celebrity_name'],
            'field': col,
            'before': 0,
            'after': np.nan,
            'reason': '0分视为“未评分/未出场”'
        })
    clean[score_cols] = clean[score_cols].mask(zero_mask, np.nan)
example = ''
if zero_cells > 0:
    r, c = idxs[0]
    example = f"row {int(r)} {score_cols[int(c)]}: 0 -> NaN"
log_entries.append({
    'rule_id': 'R5',
    'field': 'week*_judge*_score',
    'detection': '值=0',
    'action': '改为 NaN(占位)',
    'rows_affected': zero_rows,
    'cells_affected': zero_cells,
    'example': example or '无'
})

# R6: numeric coercion
num_cols = clean.columns.difference(obj_cols)
before_nonnull = clean[num_cols].notna().sum().sum()
clean[num_cols] = clean[num_cols].apply(pd.to_numeric, errors='coerce')
after_nonnull = clean[num_cols].notna().sum().sum()
coerce_cells = int(before_nonnull - after_nonnull)
log_entries.append({
    'rule_id': 'R6',
    'field': '数值字段(全部)',
    'detection': '无法解析为数值',
    'action': '强制转为 NaN',
    'rows_affected': 0 if coerce_cells == 0 else int((clean[num_cols].isna().sum(axis=1) > (raw[num_cols].isna().sum(axis=1))).sum()),
    'cells_affected': coerce_cells,
    'example': '无' if coerce_cells == 0 else '存在非数值'
})

# R7: parse results -> status/exit_week
season_last_week = {}
for season, group in clean.groupby('season'):
    last_week = None
    for w in weeks:
        cols = [c for c in score_cols if c.startswith(f'week{w}_')]
        if group[cols].notna().any(axis=None):
            last_week = w
    season_last_week[season] = last_week

status_list = []
exit_week_list = []
exit_week_inferred = []

for idx, row in clean.iterrows():
    res = str(row['results'])
    if res.startswith('Eliminated Week'):
        status_list.append('eliminated')
        try:
            exit_week = int(res.split('Eliminated Week')[-1].strip())
        except ValueError:
            exit_week = np.nan
        exit_week_list.append(exit_week)
        exit_week_inferred.append(0)
    elif res == 'Withdrew':
        status_list.append('withdrew')
        row_last = None
        for w in weeks:
            cols = [c for c in score_cols if c.startswith(f'week{w}_')]
            if row[cols].notna().any():
                row_last = w
        exit_week_list.append(row_last)
        exit_week_inferred.append(1)
    elif 'Place' in res:
        status_list.append('finalist')
        exit_week_list.append(season_last_week.get(row['season'], np.nan))
        exit_week_inferred.append(1)
    else:
        status_list.append('unknown')
        exit_week_list.append(np.nan)
        exit_week_inferred.append(1)

clean['status'] = status_list
clean['exit_week'] = pd.Series(exit_week_list, dtype='Int64')
clean['exit_week_inferred'] = exit_week_inferred

# Log status/exit_week creation
example = '无'
withdrew_rows = clean[clean['status'] == 'withdrew']
if not withdrew_rows.empty:
    widx = withdrew_rows.index[0]
    example = (
        f"row {int(widx)} results: 'Withdrew' -> "
        f"status=withdrew, exit_week={int(clean.loc[widx, 'exit_week'])}"
    )
log_entries.append({
    'rule_id': 'R7',
    'field': 'results',
    'detection': '文本解析(Eliminated/Withdrew/Place)',
    'action': '生成 status/exit_week/exit_week_inferred',
    'rows_affected': int(clean.shape[0]),
    'cells_affected': int(clean['exit_week'].notna().sum()),
    'example': example
})

# Example: Diana Nyad consistency (if exists)
nyad = clean[(clean['celebrity_name'] == 'Diana Nyad') & (clean['season'] == 18)]
if not nyad.empty:
    idx = nyad.index[0]
    example_records.append({
        'row_index': int(idx),
        'celebrity_name': clean.loc[idx, 'celebrity_name'],
        'field': 'exit_week',
        'before': '由分数推断可能为1',
        'after': int(clean.loc[idx, 'exit_week']) if pd.notna(clean.loc[idx, 'exit_week']) else np.nan,
        'reason': 'results 显式给出 Eliminated Week 2'
    })

# Save cleaned data
clean.to_csv(CLEAN_PATH, index=False)

# Build long weekly table for modeling
long_frames = []
base_cols = [
    'season', 'celebrity_name', 'ballroom_partner', 'celebrity_industry',
    'celebrity_homestate', 'celebrity_homecountry/region',
    'celebrity_age_during_season', 'results', 'placement',
    'status', 'exit_week', 'exit_week_inferred'
]

for w in weeks:
    cols = [c for c in score_cols if c.startswith(f'week{w}_')]
    scores = clean[cols]
    judge_total = scores.sum(axis=1, min_count=1)
    num_judges = scores.count(axis=1)

    raw_scores = raw[cols]
    zero_placeholder_week = raw_scores.notna().any(axis=1) & (raw_scores.fillna(0) == 0).all(axis=1)

    df_w = clean[base_cols].copy()
    df_w['week'] = w
    df_w['judge_total'] = judge_total
    df_w['num_judges'] = num_judges
    df_w['zero_placeholder'] = zero_placeholder_week.astype(int)
    df_w['active'] = (clean['exit_week'].notna()) & (w <= clean['exit_week'])
    df_w['active'] = df_w['active'].astype(int)

    long_frames.append(df_w)

long_df = pd.concat(long_frames, ignore_index=True)
long_df.to_csv(LONG_PATH, index=False)

log_entries.append({
    'rule_id': 'R8',
    'field': 'week*_judge*_score',
    'detection': '宽表到长表',
    'action': '生成 cleaned/cleaned_long_weekly.csv(judge_total/num_judges/active)',
    'rows_affected': int(long_df.shape[0]),
    'cells_affected': int(long_df['judge_total'].notna().sum()),
    'example': '全NaN周次保持为NaN(不误判为0)'
})

# Cleaning log
lines = []
lines.append('# cleaning_log')
lines.append('')
lines.append(f'- raw_file: {RAW_PATH.name}')
lines.append(f'- rows_cols_raw: {raw.shape[0]} x {raw.shape[1]}')
lines.append(f'- rows_cols_clean: {clean.shape[0]} x {clean.shape[1]}')
lines.append('')
lines.append('## 规则记录')
lines.append('')
lines.append('| 规则ID | 字段 | 检测逻辑 | 处理方式 | 影响行数 | 影响单元格 | 典型示例 |')
lines.append('|---|---|---|---|---:|---:|---|')
for e in log_entries:
    lines.append(
        f"| {e['rule_id']} | {e['field']} | {e['detection']} | {e['action']} | "
        f"{e['rows_affected']} | {e['cells_affected']} | {e['example']} |"
    )

lines.append('')
lines.append('## 典型实例(>=5)')
lines.append('')
if len(example_records) < 5:
    idxs = np.argwhere((raw[score_cols] == 0).values)
    for i in range(len(example_records), min(5, len(idxs))):
        r, c = idxs[i]
        col = score_cols[c]
        example_records.append({
            'row_index': int(r),
            'celebrity_name': clean.loc[r, 'celebrity_name'],
            'field': col,
            'before': 0,
            'after': np.nan,
            'reason': '0分视为“未评分/未出场”'
        })

for ex in example_records[:6]:
    lines.append(
        f"- row {ex['row_index']} | {ex['celebrity_name']} | {ex['field']}: {ex['before']} -> {ex['after']} | 理由: {ex['reason']}"
    )

LOG_PATH.write_text('\n'.join(lines), encoding='utf-8')

# Figures (same as before)
weekly_mean = []
weekly_n = []
for w in weeks:
    cols = [c for c in score_cols if c.startswith(f'week{w}_')]
    row_mean = clean[cols].mean(axis=1)
    weekly_mean.append(row_mean.mean())
    weekly_n.append(int(row_mean.notna().sum()))

plt.figure(figsize=(8, 4.5))
plt.plot(weeks, weekly_mean, marker='o', color='#1f77b4')
for x, y, n in zip(weeks, weekly_mean, weekly_n):
    if not np.isnan(y):
        plt.text(x, y, f"n={n}", fontsize=8, ha='center', va='bottom')
plt.title('Mean Judge Score by Week')
plt.xlabel('Week')
plt.ylabel('Mean score (per judge)')
plt.tight_layout()
plt.savefig(FIG_DIR / 'trend_weekly_mean_score.png', dpi=300)
plt.savefig(FIG_DIR / 'trend_weekly_mean_score.pdf')
plt.close()

plt.figure(figsize=(6.5, 4.5))
plt.hist(clean['celebrity_age_during_season'].dropna(), bins=15, color='#ff7f0e', edgecolor='black', alpha=0.85)
plt.title('Distribution of Celebrity Age During Season')
plt.xlabel('Age')
plt.ylabel('Count')
plt.tight_layout()
plt.savefig(FIG_DIR / 'dist_age.png', dpi=300)
plt.savefig(FIG_DIR / 'dist_age.pdf')
plt.close()

missing_rate = clean.isna().mean().sort_values(ascending=False)
plt.figure(figsize=(9, 6))
missing_rate.plot(kind='bar', color='#2ca02c')
plt.title('Missing Rate by Column')
plt.xlabel('Column')
plt.ylabel('Missing rate')
plt.tight_layout()
plt.savefig(FIG_DIR / 'missing_rate_bar.png', dpi=300)
plt.savefig(FIG_DIR / 'missing_rate_bar.pdf')
plt.close()

mean_score = clean[score_cols].mean(axis=1)
plt.figure(figsize=(7, 5))
plt.scatter(clean['celebrity_age_during_season'], mean_score, alpha=0.6, color='#9467bd')
plt.title('Age vs Mean Judge Score')
plt.xlabel('Age during season')
plt.ylabel('Mean judge score')

outlier_mask = (clean['celebrity_age_during_season'] <= 18) | (clean['celebrity_age_during_season'] >= 75)
for _, row in clean[outlier_mask].iterrows():
    plt.annotate(row['celebrity_name'], (row['celebrity_age_during_season'], mean_score.loc[row.name]),
                 fontsize=7, alpha=0.9)
plt.tight_layout()
plt.savefig(FIG_DIR / 'outlier_age_vs_score.png', dpi=300)
plt.savefig(FIG_DIR / 'outlier_age_vs_score.pdf')
plt.close()

print('cleaning done')
