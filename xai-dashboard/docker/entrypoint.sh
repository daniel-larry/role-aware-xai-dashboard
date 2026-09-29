#!/bin/sh
# Build features, model and SHAP cache on first start (artifacts volume persists them).
set -e
if [ ! -f "$ARTIFACTS_DIR/shap_values.npy" ]; then
  mkdir -p /tmp/oulad "$ARTIFACTS_DIR"
  python -c "import zipfile; zipfile.ZipFile('/data/oulad-dataset.zip').extractall('/tmp/oulad')"
  cd /app/ml
  python data_layer.py /tmp/oulad "$ARTIFACTS_DIR"
  python prediction_engine.py "$ARTIFACTS_DIR"
  python explainability.py "$ARTIFACTS_DIR"
fi
cd /app/api
exec gunicorn -w 1 -b 0.0.0.0:8000 --timeout 120 app:app
