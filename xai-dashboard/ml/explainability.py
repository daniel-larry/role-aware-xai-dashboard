"""Explainability Module.

Global service: TreeSHAP computed once per model version with the final fitted model over all
32,593 observations and cached (per-row values plus aggregates). Local service: SHAP from the
cache and LIME computed on demand for a single prediction, so the two can be shown side by side.
"""
import json
import os
import sys

import joblib
import numpy as np
import pandas as pd
import shap
from lime.lime_tabular import LimeTabularExplainer

from data_layer import CATEGORICAL, NUMERIC

SEED = 42


def transformed_names(pipe):
    pre = pipe.named_steps['preprocess']
    names = list(NUMERIC)
    ohe = pre.named_transformers_['cat'].named_steps['onehot']
    for col, cats in zip(CATEGORICAL, ohe.categories_):
        names += [f'{col}={c}' for c in cats]
    return names


def build_global_cache(art_dir):
    pipe = joblib.load(os.path.join(art_dir, 'model.joblib'))
    ft = pd.read_csv(os.path.join(art_dir, 'features.csv'))
    X = ft[NUMERIC + CATEGORICAL]
    Xt = pipe.named_steps['preprocess'].transform(X)
    names = transformed_names(pipe)
    explainer = shap.TreeExplainer(pipe.named_steps['model'])
    sv = explainer.shap_values(Xt)  # log-odds units
    np.save(os.path.join(art_dir, 'shap_values.npy'), sv.astype(np.float32))
    mean_abs = np.abs(sv).mean(axis=0)
    corr = [float(np.corrcoef(Xt[:, j], sv[:, j])[0, 1]) if Xt[:, j].std() > 0 and sv[:, j].std() > 0 else 0.0
            for j in range(len(names))]
    order = np.argsort(-mean_abs)
    glob = [{'feature': names[j], 'mean_abs_shap': float(mean_abs[j]), 'value_shap_corr': corr[j]} for j in order]
    probs = pipe.predict_proba(X)[:, 1]
    np.save(os.path.join(art_dir, 'probabilities.npy'), probs.astype(np.float32))
    meta = {'feature_names': names, 'expected_value': float(np.ravel(explainer.expected_value)[0]),
            'global_importance': glob, 'n_rows': int(len(ft))}
    json.dump(meta, open(os.path.join(art_dir, 'shap_global.json'), 'w'), indent=1)
    return meta


class Explainer:
    """Runtime explanation service used by the API."""

    def __init__(self, art_dir):
        self.pipe = joblib.load(os.path.join(art_dir, 'model.joblib'))
        self.ft = pd.read_csv(os.path.join(art_dir, 'features.csv'))
        self.shap = np.load(os.path.join(art_dir, 'shap_values.npy'))
        self.prob = np.load(os.path.join(art_dir, 'probabilities.npy'))
        self.meta = json.load(open(os.path.join(art_dir, 'shap_global.json')))
        self.names = self.meta['feature_names']
        self.Xt = self.pipe.named_steps['preprocess'].transform(self.ft[NUMERIC + CATEGORICAL])
        self.model = self.pipe.named_steps['model']
        self.lime = LimeTabularExplainer(
            self.Xt, feature_names=self.names, class_names=['not at risk', 'at risk'],
            categorical_features=[i for i, n in enumerate(self.names) if '=' in n],
            discretize_continuous=True, random_state=SEED, mode='classification')

    def local_shap(self, i, k=5):
        v = self.shap[i]
        order = np.argsort(-np.abs(v))[:k]
        return [{'feature': self.names[j], 'value': float(self.Xt[i, j]), 'contribution': float(v[j])} for j in order]

    def local_lime(self, i, k=5, num_samples=1000):
        # Reset the sampler so the same student always gets the same explanation.
        rs = np.random.RandomState(SEED)
        self.lime.random_state = self.lime.base.random_state = rs
        if self.lime.discretizer is not None:
            self.lime.discretizer.random_state = rs
        exp = self.lime.explain_instance(self.Xt[i], self.model.predict_proba, num_features=k,
                                         num_samples=num_samples, labels=(1,))
        return [{'condition': cond, 'contribution': float(w)} for cond, w in exp.as_list(label=1)]

    def cohort_mean(self, idx, k=10):
        v = self.shap[idx].mean(axis=0)
        order = np.argsort(-np.abs(v))[:k]
        return [{'feature': self.names[j], 'contribution': float(v[j])} for j in order]


if __name__ == '__main__':
    meta = build_global_cache(sys.argv[1])
    for g in meta['global_importance'][:15]:
        print(f"{g['feature']:45s} {g['mean_abs_shap']:.4f}  corr={g['value_shap_corr']:+.3f}")
