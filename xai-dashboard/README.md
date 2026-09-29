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

## Run everything in Docker (API + Moodle plugin + Canvas iframe)

Tested on Moodle 5.2.3 (`erseco/alpine-moodle`) and `lbjay/canvas-docker`.

```bash
cp .env.example .env            # set real secrets
python lms/sync/make_import_files.py /path/to/oulad lms/sync/out   # 22 courses, 28,785 students, 32,593 enrolments
docker compose up -d            # api on :8000, Moodle on :8080 (first start trains the model, ~5 min)
docker compose exec moodle sh /scripts/setup.sh    # plugin config, categories, courses, users, enrolments, roles
docker compose --profile canvas up -d               # Canvas on :3000 (optional, 6.4 GB image)
CANVAS_URL=http://localhost:3000 CANVAS_TOKEN=canvas-docker CANVAS_CONTAINER=xai-dashboard-canvas-1 \
    sh lms/canvas/setup.sh                          # SIS import + dashboard module in every course
```

The student upload into Moodle takes roughly 30 minutes and the Canvas SIS import longer; both
can be re-run safely. Behind a TLS-intercepting proxy, build the API image with
`docker build --secret id=ca,src=<ca-bundle.crt> -f docker/Dockerfile.api -t xai-dashboard-api .`

If the machine restarts while Canvas is running, its web server may refuse to start because of a
stale pid file; fix with
`docker exec xai-dashboard-canvas-1 bash -c 'rm -f /opt/canvas/canvas-lms/tmp/pids/server.pid && supervisorctl restart canvas_web'`.
An interrupted SIS import is marked failed; re-run `lms/canvas/setup.sh` to resume it.

Accounts after setup (passwords from `.env`):

| System | Username | Role | Sees |
|---|---|---|---|
| Moodle | `instructor` / `instructor_aaa` ... `instructor_ggg` | Teacher in all / one module's courses | **At-risk insights** under the course's *More* menu |
| Moodle | `advisor` | Academic advisor (system) | **Advisor caseload** |
| Moodle | `manager` | Manager (system) | **Institution overview** |
| Moodle | `s<id_student>` | Student (cannot log in) | nothing |
| Canvas | `instructor` | Teacher in all courses | *At-risk insights* module (dashboard iframe) |
| Dashboard | `instructor` / `advisor` / `admin` | `DASHBOARD_PASSWORD` | the matching view |

`CANVAS_TOKEN=canvas-docker` is the public demo token built into the `lbjay/canvas-docker`
image; never use that image or token outside a local machine.

In Moodle, login, enrolment and roles are Moodle's own; the plugin calls the API
server-to-server with `SERVICE_KEY`, and an instructor only ever sees students of a course they
teach. In Canvas every course gets an *At-risk insights* module whose External URL item embeds
the dashboard (no LTI), opened on that course via `?course=FFF-2014J`.

Screenshots from a real run are in `docs/screenshots/` (regenerate with `tools/*_screenshots.mjs`).
