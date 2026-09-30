# Role-aware XAI dashboard for at-risk student prediction

This repository holds my MSc thesis and the working prototype described in it. The prototype predicts
which students are at risk of failing or withdrawing, using the Open University Learning Analytics
Dataset (OULAD), and explains each prediction with SHAP and LIME. The same predictions are shown in
three different ways: to an instructor, an academic advisor, or an administrator. Each view shows the
level of detail that role needs. The dashboard runs on its own, inside Moodle through a local plugin,
and inside Canvas as an embedded course page.

## The thesis

- [Thesis_2_revised.docx](Thesis_2_revised.docx): the full thesis (Word)
- [Thesis_2_revised_preview.pdf](Thesis_2_revised_preview.pdf): a PDF copy for reading in the browser
- [Thesis_2_REVISION_NOTES.md](Thesis_2_REVISION_NOTES.md): what changed in response to each
  supervisor comment

Chapter 4 of the thesis describes how the prototype was built. Chapter 5 reports the results.

## Starting the prototype with Docker

You only need [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine
with the Compose plugin). Everything else, including the dataset, is already in the repository.

```bash
git clone https://github.com/daniel-larry/role-aware-xai-dashboard.git
cd role-aware-xai-dashboard/xai-dashboard
docker compose up -d
```

The first start takes a few minutes, because the API container builds the feature table from the
OULAD archive, trains the XGBoost model, and computes the SHAP values. You can follow its progress
with `docker compose logs -f api`. Once gunicorn reports "Listening at", open
<http://localhost:8000> and sign in as `instructor`, `advisor` or `admin`. The password for all
three is `DASHBOARD_PASSWORD` in `xai-dashboard/.env`. Later starts reuse the trained model and
take only a few seconds.

**About the `.env` file.** I committed `xai-dashboard/.env` on purpose, so that reviewers can run
the prototype without setting anything up. It only holds test passwords for these local containers,
and none of them are used anywhere else. If you want to deploy the system for real, replace every
value in it first. `.env.example` shows the variables it needs.

To stop everything, run `docker compose down`. To start again from a clean state, including a
fresh model, run `docker compose down -v`.

## Seeing it inside Moodle (optional)

`docker compose up -d` also starts Moodle at <http://localhost:8080>. It is empty at first. To load
the 22 OULAD courses, 28,785 students and 32,593 enrolments, and to install the plugin, run these
from the `xai-dashboard` folder. The first command needs Python 3 with pandas installed on your
machine (`pip install pandas`).

```bash
set -a; . ./.env; set +a
unzip -o ../oulad-dataset.zip -d /tmp/oulad
python3 lms/sync/make_import_files.py /tmp/oulad lms/sync/out
docker compose exec moodle sh /scripts/setup.sh
```

The student upload is slow, around 30 minutes, but it is safe to run again if it gets interrupted.
When it finishes, sign in to Moodle as `instructor`, `advisor` or `manager`, with `STAFF_PASSWORD`
from `.env`. An instructor finds **At-risk insights** under a course's *More* menu. The advisor and
the manager find **Advisor caseload** and **Institution overview**. The Moodle administrator
account is `admin` with `MOODLE_ADMIN_PASSWORD`.

## Seeing it inside Canvas (optional)

Canvas is a large image (about 6.4 GB), so it only starts if you ask for it:

```bash
docker compose --profile canvas up -d
CANVAS_URL=http://localhost:3000 CANVAS_TOKEN=canvas-docker CANVAS_CONTAINER=xai-dashboard-canvas-1 \
    sh lms/canvas/setup.sh
```

This needs the import files from the Moodle step above, as well as `curl` and `zip`. It creates the
same courses in Canvas and adds an *At-risk insights* module to each one, which opens the dashboard
for that course. Sign in to Canvas at <http://localhost:3000> as `instructor` with `STAFF_PASSWORD`.
`canvas-docker` is the demo token built into that public test image. Only use it on your own
machine.

## If something goes wrong

- **Port already in use.** Something else on your machine is using 8000, 8080 or 3000. Stop that
  program, or change the port on the left-hand side of the `ports:` lines in `docker-compose.yml`.
- **<http://localhost:8000> does not load on the first start.** The API only starts listening after
  the first training run finishes. Watch `docker compose logs -f api` until gunicorn reports
  "Listening at", then reload the page.
- **Canvas stops working after a restart.** Remove its stale process file:
  `docker exec xai-dashboard-canvas-1 bash -c 'rm -f /opt/canvas/canvas-lms/tmp/pids/server.pid && supervisorctl restart canvas_web'`

## What is where

| Path | Contents |
| --- | --- |
| `xai-dashboard/ml/` | Feature engineering, model training and evaluation, and the SHAP/LIME explanation code |
| `xai-dashboard/api/` | Flask API, with sign-in and role checks |
| `xai-dashboard/web/` | React dashboard with the three role views |
| `xai-dashboard/lms/` | The Moodle plugin (`local_xairisk`) and the Moodle and Canvas setup scripts |
| `xai-dashboard/docs/screenshots/` | Screenshots from a real run, used as the thesis figures |
| `xai-dashboard/artifacts/` | The feature dictionary and the model manifest (version, settings, metrics) |
| `oulad-dataset.zip` | The OULAD dataset, CC BY 4.0 (see [OULAD_SOURCE.md](OULAD_SOURCE.md)) |
| `rf_*`, `run_info.txt`, `console_last30.txt` | Outputs of an earlier Random Forest explainability run, kept for reference |

The prototype is a research tool built on a public, anonymised dataset. It has not been evaluated
with instructors, advisors or administrators, and it should not be used to make decisions about
real students.
