"""Data Layer: builds one feature row per (student, module, presentation) from the seven OULAD tables.

Output columns match the 24-column feature set described in the thesis (17 numeric, 7 categorical)
plus identifiers and the binary target. Engagement features use deadline-anchored windows
(7, 14 and 28 days before each assessment deadline); a leakage guard asserts that no window
draws on activity dated on or after its deadline.
"""
import json
import os
import sys

import numpy as np
import pandas as pd

KEYS = ['code_module', 'code_presentation', 'id_student']
NUMERIC = ['num_of_prev_attempts', 'studied_credits', 'date_registration', 'withdrew_before_start',
           'module_presentation_length', 'n_assessments_submitted', 'mean_score', 'min_score',
           'mean_days_late', 'n_late_submissions', 'n_banked', 'clicks_7d_before_deadline',
           'clicks_14d_before_deadline', 'clicks_28d_before_deadline', 'total_clicks', 'active_days',
           'mean_daily_clicks']
CATEGORICAL = ['code_module', 'gender', 'region', 'highest_education', 'imd_band', 'age_band', 'disability']
WINDOWS = (7, 14, 28)

FEATURE_DICTIONARY = {
    'num_of_prev_attempts': ('Previous attempts', 'Number of previous attempts at this module'),
    'studied_credits': ('Credits studied', 'Total credits of the modules the student is studying'),
    'date_registration': ('Registration timing', 'Registration day relative to the module start'),
    'withdrew_before_start': ('Withdrew before start', 'Unregistered on or before the module start day'),
    'module_presentation_length': ('Presentation length', 'Length of the module presentation in days'),
    'n_assessments_submitted': ('Assessments submitted', 'Number of assessments submitted'),
    'mean_score': ('Mean assessment score', 'Mean score of submitted assessments'),
    'min_score': ('Lowest assessment score', 'Lowest score of submitted assessments'),
    'mean_days_late': ('Mean days late', 'Mean days submitted after the deadline (0 if on time)'),
    'n_late_submissions': ('Late submissions', 'Number of submissions after the deadline'),
    'n_banked': ('Banked results', 'Assessment results carried over from a previous presentation'),
    'clicks_7d_before_deadline': ('Clicks, 7 days before deadlines', 'VLE clicks in the 7 days before each deadline'),
    'clicks_14d_before_deadline': ('Clicks, 14 days before deadlines', 'VLE clicks in the 14 days before each deadline'),
    'clicks_28d_before_deadline': ('Clicks, 28 days before deadlines', 'VLE clicks in the 28 days before each deadline'),
    'total_clicks': ('Total VLE clicks', 'Total clicks in the virtual learning environment'),
    'active_days': ('Active days', 'Number of days with any VLE activity'),
    'mean_daily_clicks': ('Mean clicks per active day', 'Total clicks divided by active days'),
    'code_module': ('Module', 'Module code'),
    'gender': ('Gender', 'Gender'),
    'region': ('Region', 'Geographic region'),
    'highest_education': ('Highest prior education', 'Highest prior education'),
    'imd_band': ('IMD band', 'Index of multiple deprivation band'),
    'age_band': ('Age band', 'Age band'),
    'disability': ('Disability', 'Declared disability'),
}


def read(raw, name, **kw):
    return pd.read_csv(os.path.join(raw, name + '.csv'), na_values=['?'], **kw)


def build(raw_dir):
    info = read(raw_dir, 'studentInfo')
    reg = read(raw_dir, 'studentRegistration')
    courses = read(raw_dir, 'courses')
    ass = read(raw_dir, 'assessments')
    sa = read(raw_dir, 'studentAssessment')

    df = info.merge(reg, on=KEYS, how='left').merge(courses, on=['code_module', 'code_presentation'], how='left')
    df['withdrew_before_start'] = (df['date_unregistration'].notna() & (df['date_unregistration'] <= 0)).astype(int)
    df['at_risk'] = df['final_result'].isin(['Withdrawn', 'Fail']).astype(int)

    # ---------------- assessment features ----------------
    sa = sa.merge(ass, on='id_assessment', how='left')
    sa['days_late'] = (sa['date_submitted'] - sa['date']).clip(lower=0)
    g = sa.groupby(KEYS)
    af = pd.DataFrame({
        'n_assessments_submitted': g.size(),
        'mean_score': g['score'].mean(),
        'min_score': g['score'].min(),
        'mean_days_late': g['days_late'].mean(),
        'n_late_submissions': g['days_late'].apply(lambda s: int((s > 0).sum())),
        'n_banked': g['is_banked'].sum(),
    }).reset_index()
    df = df.merge(af, on=KEYS, how='left')
    for c in ('n_assessments_submitted', 'n_late_submissions', 'n_banked'):
        df[c] = df[c].fillna(0).astype(int)

    # ---------------- engagement features (chunked clickstream) ----------------
    daily = []
    for chunk in pd.read_csv(os.path.join(raw_dir, 'studentVle.csv'), chunksize=2_000_000,
                             usecols=KEYS + ['date', 'sum_click']):
        daily.append(chunk.groupby(KEYS + ['date'], as_index=False)['sum_click'].sum())
    daily = pd.concat(daily).groupby(KEYS + ['date'], as_index=False)['sum_click'].sum()
    tot = daily.groupby(KEYS).agg(total_clicks=('sum_click', 'sum'), active_days=('date', 'nunique')).reset_index()
    df = df.merge(tot, on=KEYS, how='left')

    deadlines = ass[['code_module', 'code_presentation', 'date']].dropna().drop_duplicates()
    deadlines = deadlines.rename(columns={'date': 'deadline'})
    joined = daily.merge(deadlines, on=['code_module', 'code_presentation'], how='inner')
    for w in WINDOWS:
        inwin = joined[(joined['date'] >= joined['deadline'] - w) & (joined['date'] < joined['deadline'])]
        # leakage guard: every counted click is strictly before its deadline
        assert (inwin['date'] < inwin['deadline']).all(), 'leakage: window includes activity on/after deadline'
        s = inwin.groupby(KEYS)['sum_click'].sum().rename(f'clicks_{w}d_before_deadline').reset_index()
        df = df.merge(s, on=KEYS, how='left')
    for c in ['total_clicks', 'active_days'] + [f'clicks_{w}d_before_deadline' for w in WINDOWS]:
        df[c] = df[c].fillna(0)
    df['mean_daily_clicks'] = np.where(df['active_days'] > 0, df['total_clicks'] / df['active_days'].replace(0, 1), 0.0)

    out = df[KEYS + NUMERIC + [c for c in CATEGORICAL if c != 'code_module'] + ['final_result', 'at_risk']]
    return out


def main(raw_dir, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    ft = build(raw_dir)
    assert len(ft) == 32593, len(ft)
    ft.to_csv(os.path.join(out_dir, 'features.csv'), index=False)
    dictionary = {'version': '1.0', 'numeric': NUMERIC, 'categorical': CATEGORICAL,
                  'features': {k: {'label': v[0], 'description': v[1]} for k, v in FEATURE_DICTIONARY.items()}}
    json.dump(dictionary, open(os.path.join(out_dir, 'feature_dictionary.json'), 'w'), indent=1)
    print('feature table', ft.shape, 'at-risk share', round(ft['at_risk'].mean(), 4))


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
