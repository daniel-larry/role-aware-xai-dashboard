"""Prediction Engine: evaluation (GroupKFold by course presentation) and final model training.

Protocol (thesis, Chapter 3 Section 3.4): four-fold GroupKFold grouped by code_presentation,
fixed XGBoost configuration, no resampling, no hyperparameter search, threshold 0.5.
Random Forest and Gradient Boosting are compared under the identical pipeline.
The prototype model is selected on recall, with F1 as a secondary metric.
"""
import datetime
import json
import os
import sys

import joblib
import numpy as np
import pandas as pd
import sklearn
import xgboost
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import GradientBoostingClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from xgboost import XGBClassifier

from data_layer import CATEGORICAL, NUMERIC

SEED = 42
THRESHOLD = 0.5
XGB_PARAMS = dict(n_estimators=300, max_depth=5, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8,
                  random_state=SEED, eval_metric='logloss', n_jobs=-1)


def preprocessor():
    return ColumnTransformer([
        ('num', SimpleImputer(strategy='median'), NUMERIC),
        ('cat', Pipeline([('impute', SimpleImputer(strategy='most_frequent')),
                          ('onehot', OneHotEncoder(handle_unknown='ignore', sparse_output=False))]), CATEGORICAL),
    ])


def models():
    return {
        'XGBoost': XGBClassifier(**XGB_PARAMS),
        'Random Forest': RandomForestClassifier(n_estimators=300, random_state=SEED, n_jobs=-1),
        'Gradient Boosting': GradientBoostingClassifier(random_state=SEED),
    }


def pipeline(model):
    return Pipeline([('preprocess', preprocessor()), ('model', model)])


def metrics(y, p):
    pred = (p >= THRESHOLD).astype(int)
    tn, fp, fn, tp = confusion_matrix(y, pred).ravel()
    return {'accuracy': accuracy_score(y, pred), 'precision': precision_score(y, pred),
            'recall': recall_score(y, pred), 'f1': f1_score(y, pred), 'auc': roc_auc_score(y, p),
            'specificity': tn / (tn + fp), 'confusion_matrix': [[int(tn), int(fp)], [int(fn), int(tp)]],
            'n': int(len(y))}


def evaluate(ft):
    X, y, groups = ft[NUMERIC + CATEGORICAL], ft['at_risk'].values, ft['code_presentation'].values
    cv = GroupKFold(n_splits=4)
    results, oof_store = {}, {}
    for name, m in models().items():
        oof = np.zeros(len(y))
        for tr, te in cv.split(X, y, groups):
            p = pipeline(m).fit(X.iloc[tr], y[tr])
            oof[te] = p.predict_proba(X.iloc[te])[:, 1]
        results[name] = metrics(y, oof)
        oof_store[name] = oof
        print(f"{name:18s} acc={results[name]['accuracy']:.4f} prec={results[name]['precision']:.4f} "
              f"rec={results[name]['recall']:.4f} f1={results[name]['f1']:.4f} auc={results[name]['auc']:.4f}")
    per_pres = {}
    for pres in sorted(set(groups)):
        mask = groups == pres
        per_pres[pres] = metrics(y[mask], oof_store['XGBoost'][mask])
        per_pres[pres]['at_risk_share'] = float(y[mask].mean())
    return results, per_pres, oof_store['XGBoost']


def main(art_dir):
    ft = pd.read_csv(os.path.join(art_dir, 'features.csv'))
    results, per_pres, oof = evaluate(ft)
    selected = max(results, key=lambda k: results[k]['recall'])  # recall-first selection criterion
    final = pipeline(XGBClassifier(**XGB_PARAMS)).fit(ft[NUMERIC + CATEGORICAL], ft['at_risk'])
    joblib.dump(final, os.path.join(art_dir, 'model.joblib'))
    ft.assign(oof_probability=oof).to_csv(os.path.join(art_dir, 'features_scored.csv'), index=False)
    manifest = {
        'model_version': datetime.datetime.utcnow().strftime('xgb-%Y%m%d-%H%M%S'),
        'trained_at': datetime.datetime.utcnow().isoformat() + 'Z',
        'feature_dictionary_version': '1.0',
        'model': 'XGBoost', 'params': XGB_PARAMS, 'threshold': THRESHOLD,
        'protocol': 'GroupKFold(4) grouped by code_presentation; no resampling; no hyperparameter search',
        'selection_criterion': 'recall (F1 secondary)', 'selected_by_criterion': selected,
        'libraries': {'scikit-learn': sklearn.__version__, 'xgboost': xgboost.__version__,
                      'pandas': pd.__version__, 'numpy': np.__version__, 'python': sys.version.split()[0]},
        'comparison': results, 'per_presentation': per_pres,
        'n_training_rows': int(len(ft)),
    }
    json.dump(manifest, open(os.path.join(art_dir, 'manifest.json'), 'w'), indent=1, default=float)
    print('selected by recall:', selected, '| saved model + manifest', manifest['model_version'])


if __name__ == '__main__':
    main(sys.argv[1])
