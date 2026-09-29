"""Flask API: authentication, role-based access control, prediction and explanation endpoints.

Roles: instructor (per-student detail), advisor (cohort-averaged caseload), administrator
(full-population view). Role separation is enforced here on every endpoint, independently of the UI.
The dashboard may be embedded in an LMS page (iframe / External URL); allowed framing origins are
controlled by the FRAME_ANCESTORS environment variable.
"""
import datetime
import functools
import json
import os
import sys

import jwt
import numpy as np
from flask import Flask, abort, g, jsonify, request, send_from_directory
from werkzeug.security import check_password_hash, generate_password_hash

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'ml'))
from explainability import Explainer  # noqa: E402

ART = os.environ.get('ARTIFACTS_DIR', os.path.join(os.path.dirname(__file__), '..', 'artifacts'))
STATIC = os.environ.get('STATIC_DIR', os.path.join(os.path.dirname(__file__), '..', 'web', 'dist'))
SECRET = os.environ.get('JWT_SECRET', 'change-me-in-production')
WATCH_THRESHOLD = float(os.environ.get('WATCH_THRESHOLD', '0.5'))
FRAME_ANCESTORS = os.environ.get('FRAME_ANCESTORS', "'self' http://localhost:* http://127.0.0.1:*")

USERS = {  # demonstration accounts, one per role; passwords stored as salted hashes
    'instructor': {'role': 'instructor', 'name': 'Demo Instructor',
                   'hash': generate_password_hash(os.environ.get('INSTRUCTOR_PASSWORD', 'instructor123'))},
    'advisor': {'role': 'advisor', 'name': 'Demo Advisor',
                'hash': generate_password_hash(os.environ.get('ADVISOR_PASSWORD', 'advisor123'))},
    'admin': {'role': 'administrator', 'name': 'Demo Administrator',
              'hash': generate_password_hash(os.environ.get('ADMIN_PASSWORD', 'admin123'))},
}

app = Flask(__name__, static_folder=None)
E = Explainer(ART)
MANIFEST = json.load(open(os.path.join(ART, 'manifest.json')))
DICTIONARY = json.load(open(os.path.join(ART, 'feature_dictionary.json')))
FT = E.ft
KEY = (FT['code_module'] + '|' + FT['code_presentation'] + '|' + FT['id_student'].astype(str)).values
INDEX = {k: i for i, k in enumerate(KEY)}


def label(feature):
    feats = DICTIONARY['features']
    if '=' in feature:
        col, val = feature.split('=', 1)
        return f"{feats.get(col, {}).get('label', col)}: {val}"
    return feats.get(feature, {}).get('label', feature)


def lime_label(condition):
    for name in sorted(E.names, key=len, reverse=True):
        if name in condition:
            if '=' in name:  # one-hot indicator: "col=val=1" means the student is in that category
                col, val = name.split('=', 1)
                col_label = label(col) if col in DICTIONARY['features'] else col
                is_in = condition.endswith('=1') or condition.endswith('> 0.50')
                return f"{DICTIONARY['features'].get(col, {}).get('label', col)} {'is' if is_in else 'is not'} {val}"
            return condition.replace(name, label(name))
    return condition


@app.after_request
def headers(resp):
    resp.headers['Content-Security-Policy'] = f'frame-ancestors {FRAME_ANCESTORS}'
    resp.headers['X-Content-Type-Options'] = 'nosniff'
    return resp


def require(*roles):
    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*a, **kw):
            auth = request.headers.get('Authorization', '')
            if not auth.startswith('Bearer '):
                abort(401)
            try:
                claims = jwt.decode(auth[7:], SECRET, algorithms=['HS256'])
            except jwt.PyJWTError:
                abort(401)
            if claims.get('role') not in roles:
                abort(403)
            g.user = claims
            return fn(*a, **kw)
        return wrapper
    return deco


@app.post('/api/login')
def login():
    body = request.get_json(force=True, silent=True) or {}
    u = USERS.get(body.get('username', ''))
    if not u or not check_password_hash(u['hash'], body.get('password', '')):
        return jsonify(error='Invalid username or password'), 401
    exp = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=8)
    token = jwt.encode({'sub': body['username'], 'role': u['role'], 'name': u['name'], 'exp': exp}, SECRET, algorithm='HS256')
    return jsonify(token=token, role=u['role'], name=u['name'])


@app.get('/api/health')
def health():
    return jsonify(status='ok', model_version=MANIFEST['model_version'])


@app.get('/api/meta')
@require('instructor', 'advisor', 'administrator')
def meta():
    pres = FT.groupby(['code_module', 'code_presentation']).size().reset_index(name='n')
    return jsonify(model_version=MANIFEST['model_version'], threshold=MANIFEST['threshold'],
                   watch_threshold=WATCH_THRESHOLD, role=g.user['role'], name=g.user['name'],
                   module_presentations=pres.to_dict(orient='records'))


def student_rows(idx):
    rows = []
    for i in idx:
        r = FT.iloc[i]
        rows.append({'key': KEY[i], 'id_student': int(r['id_student']), 'code_module': r['code_module'],
                     'code_presentation': r['code_presentation'], 'probability': float(E.prob[i]),
                     'flagged': bool(E.prob[i] >= MANIFEST['threshold']),
                     'n_assessments_submitted': int(r['n_assessments_submitted']),
                     'mean_score': None if np.isnan(r['mean_score']) else round(float(r['mean_score']), 1),
                     'active_days': int(r['active_days'])})
    return rows


@app.get('/api/instructor/students')
@require('instructor')
def instructor_students():
    m, p = request.args.get('module'), request.args.get('presentation')
    mask = (FT['code_module'] == m) & (FT['code_presentation'] == p)
    idx = np.where(mask.values)[0]
    idx = idx[np.argsort(-E.prob[idx])]
    return jsonify(students=student_rows(idx), n=int(len(idx)), n_flagged=int((E.prob[idx] >= MANIFEST['threshold']).sum()))


@app.get('/api/instructor/students/<path:key>/explanation')
@require('instructor')
def instructor_explanation(key):
    i = INDEX.get(key)
    if i is None:
        abort(404)
    shap_items = [{**d, 'label': label(d['feature'])} for d in E.local_shap(i, k=5)]
    lime_items = [{**d, 'label': lime_label(d['condition'])} for d in E.local_lime(i, k=5)]
    shap_set = {d['feature'] for d in shap_items}
    lime_set = {next((n for n in sorted(E.names, key=len, reverse=True) if n in d['condition']), d['condition'])
                for d in lime_items}
    return jsonify(student=student_rows([i])[0], shap=shap_items, lime=lime_items,
                   overlap=len(shap_set & lime_set) / 5, model_version=MANIFEST['model_version'])


@app.get('/api/advisor/caseload')
@require('advisor')
def advisor_caseload():
    p = request.args.get('presentation')
    mask = (E.prob >= WATCH_THRESHOLD) & ((FT['code_presentation'] == p).values if p else True)
    idx = np.where(mask)[0]
    trail = [{**d, 'label': label(d['feature'])} for d in E.cohort_mean(idx, k=10)] if len(idx) else []
    by_module = FT.iloc[idx].groupby('code_module').size().to_dict()
    top = idx[np.argsort(-E.prob[idx])][:25]
    return jsonify(n=int(len(idx)), watch_threshold=WATCH_THRESHOLD, trail=trail,
                   by_module={k: int(v) for k, v in by_module.items()}, students=student_rows(top))


@app.get('/api/admin/overview')
@require('administrator')
def admin_overview():
    comp = MANIFEST['comparison']['XGBoost']
    glob = [{'feature': d['feature'], 'label': label(d['feature']), 'mean_abs_shap': d['mean_abs_shap'],
             'direction': 1 if d['value_shap_corr'] >= 0 else -1} for d in E.meta['global_importance'][:12]]
    per = {k: {m: v[m] for m in ('accuracy', 'precision', 'recall', 'f1', 'n')} for k, v in MANIFEST['per_presentation'].items()}
    return jsonify(model_version=MANIFEST['model_version'], protocol=MANIFEST['protocol'],
                   metrics={m: comp[m] for m in ('accuracy', 'precision', 'recall', 'f1', 'auc', 'specificity')},
                   confusion_matrix=comp['confusion_matrix'], per_presentation=per,
                   comparison={k: {m: v[m] for m in ('accuracy', 'precision', 'recall', 'f1')} for k, v in MANIFEST['comparison'].items()},
                   population=int(len(FT)), n_flagged=int((E.prob >= MANIFEST['threshold']).sum()), global_trail=glob)


@app.get('/', defaults={'path': ''})
@app.get('/<path:path>')
def spa(path):
    if path.startswith('api/'):
        abort(404)
    full = os.path.join(STATIC, path)
    if path and os.path.isfile(full):
        return send_from_directory(STATIC, path)
    return send_from_directory(STATIC, 'index.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8000)))
