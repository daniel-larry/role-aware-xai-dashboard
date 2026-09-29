# Role-aware XAI dashboard (prototype)

Predicts at-risk students on OULAD with XGBoost and explains predictions with SHAP and LIME,
delivered through three role-gated views (instructor, advisor, administrator).

## Run locally

```bash
# 1. data + model (OULAD CSVs extracted from ../oulad-dataset.zip into /path/to/oulad)
pip install pandas numpy scikit-learn xgboost shap lime flask pyjwt joblib
cd ml
python data_layer.py /path/to/oulad ../artifacts        # feature table (32,593 rows)
python prediction_engine.py ../artifacts                # GroupKFold(4) evaluation + final model + manifest
python explainability.py ../artifacts                   # cached global TreeSHAP

# 2. frontend
cd ../web && npm install && npx vite build

# 3. API + dashboard on http://localhost:8000
cd ../api && python app.py
```

Demo accounts: `instructor` / `advisor` / `admin` (passwords set via `INSTRUCTOR_PASSWORD`,
`ADVISOR_PASSWORD`, `ADMIN_PASSWORD`; development defaults are in `api/app.py`).
Allowed embedding origins for LMS iframes are set with `FRAME_ANCESTORS`.

`artifacts/manifest.json` records the model version, configuration, library versions and
out-of-fold metrics of the committed run.
