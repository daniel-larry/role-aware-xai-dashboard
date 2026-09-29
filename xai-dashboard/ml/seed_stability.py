"""Robustness check (thesis Section 5.7): is the SHAP order of total_clicks and clicks_28d_before_deadline stable?

Refits the final model with several random seeds and reports each feature's mean |SHAP| and rank, plus the
Spearman correlations among the engagement features.   Usage: python seed_stability.py <artifacts_dir>
"""
import os
import sys

import joblib
import numpy as np
import pandas as pd
import shap
from sklearn.base import clone

from data_layer import CATEGORICAL, NUMERIC
from explainability import transformed_names

PAIR = ('total_clicks', 'clicks_28d_before_deadline')
ENGAGEMENT = ['total_clicks', 'clicks_28d_before_deadline', 'clicks_14d_before_deadline',
              'clicks_7d_before_deadline', 'active_days', 'mean_daily_clicks']


def main(art_dir, seeds=(42, 1, 2, 3, 4, 5, 6, 7)):
    ft = pd.read_csv(os.path.join(art_dir, 'features.csv'))
    print(ft[ENGAGEMENT].corr(method='spearman').round(2).to_string(), '\n')
    base = joblib.load(os.path.join(art_dir, 'model.joblib'))
    X, y = ft[NUMERIC + CATEGORICAL], ft.at_risk
    above = 0
    for seed in seeds:
        pipe = clone(base).set_params(model__random_state=seed).fit(X, y)
        sv = shap.TreeExplainer(pipe.named_steps['model']).shap_values(pipe.named_steps['preprocess'].transform(X))
        imp = dict(zip(transformed_names(pipe), np.abs(sv).mean(axis=0)))
        a, b = imp[PAIR[0]], imp[PAIR[1]]
        above += b > a
        print(f'seed {seed}: {PAIR[0]} {a:.4f}, {PAIR[1]} {b:.4f}, combined {a + b:.4f}')
    print(f'\n{PAIR[1]} ranks above {PAIR[0]} in {above} of {len(seeds)} fits')


if __name__ == '__main__':
    main(sys.argv[1])
