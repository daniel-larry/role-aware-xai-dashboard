#!/bin/sh
# Load all OULAD courses, students and enrolments into Canvas (SIS import) and add the dashboard
# to every course as an External URL module item (iframe, no LTI).
#   CANVAS_URL=http://localhost:3000 CANVAS_TOKEN=<admin API token> [CANVAS_CONTAINER=xai-dashboard-canvas-1] sh lms/canvas/setup.sh
set -e
: "${CANVAS_URL:?}" "${CANVAS_TOKEN:?}"
DASHBOARD_URL=${DASHBOARD_URL:-http://localhost:8000/}
OUT=$(dirname "$0")/../sync/out/canvas
AUTH="Authorization: Bearer $CANVAS_TOKEN"

# The local canvas-docker image ships with SIS imports switched off and the API cannot enable them.
# Set CANVAS_CONTAINER (e.g. xai-dashboard-canvas-1) to switch them on; hosted Canvas usually has them on.
if [ -n "$CANVAS_CONTAINER" ]; then
  docker exec "$CANVAS_CONTAINER" bash -lc 'cd /opt/canvas/canvas-lms && $GEM_HOME/bin/bundle exec rails runner \
    "a=Account.default; a.allow_sis_import=true; a.save!"' >/dev/null 2>&1
fi

(cd "$OUT" && rm -f ../canvas_sis.zip && zip -q ../canvas_sis.zip terms.csv courses.csv users.csv enrollments.csv)
curl -sf -H "$AUTH" -F attachment=@"$OUT/../canvas_sis.zip" -F import_type=instructure_csv \
     "$CANVAS_URL/api/v1/accounts/1/sis_imports" > /tmp/sis.json
ID=$(python3 -c "import json;print(json.load(open('/tmp/sis.json'))['id'])")
echo "SIS import $ID started"
while :; do
  STATE=$(curl -sf -H "$AUTH" "$CANVAS_URL/api/v1/accounts/1/sis_imports/$ID" | python3 -c "import sys,json;d=json.load(sys.stdin);print(d['workflow_state'],d.get('progress'))")
  echo "  $STATE"; case "$STATE" in imported*|failed*) break;; esac; sleep 5
done

# Resolve Canvas course ids by course code (sis_course_id lookups can fail while an import runs).
curl -sf -H "$AUTH" "$CANVAS_URL/api/v1/accounts/1/courses?per_page=100" \
  | python3 -c "import sys,json;[print(c['course_code'],c['id']) for c in json.load(sys.stdin)]" > /tmp/canvas_courses.txt
for SIS in $(tail -n +2 "$OUT/courses.csv" | cut -d, -f1); do
  CID=$(awk -v c="$SIS" '$1==c{print $2}' /tmp/canvas_courses.txt)
  [ -n "$CID" ] || { echo "  $SIS not found in Canvas"; continue; }
  if curl -sf -H "$AUTH" "$CANVAS_URL/api/v1/courses/$CID/modules?per_page=100" | grep -q '"name":"At-risk insights"'; then
    echo "  $SIS already has the dashboard"; continue
  fi
  MID=$(curl -sf -H "$AUTH" -X POST "$CANVAS_URL/api/v1/courses/$CID/modules" -d "module[name]=At-risk insights" \
        | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")
  IID=$(curl -sf -H "$AUTH" -X POST "$CANVAS_URL/api/v1/courses/$CID/modules/$MID/items" \
       -d "module_item[type]=ExternalUrl" -d "module_item[title]=At-risk insights dashboard" \
       -d "module_item[external_url]=${DASHBOARD_URL}?course=$SIS" -d "module_item[new_tab]=false" \
        | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")
  curl -sf -H "$AUTH" -X PUT "$CANVAS_URL/api/v1/courses/$CID/modules/$MID/items/$IID" -d "module_item[published]=true" >/dev/null
  curl -sf -H "$AUTH" -X PUT "$CANVAS_URL/api/v1/courses/$CID/modules/$MID" -d "module[published]=true" >/dev/null
  curl -sf -H "$AUTH" -X PUT "$CANVAS_URL/api/v1/courses/$CID" -d "offer=true" >/dev/null
  echo "  dashboard added to $SIS"
done
echo "Canvas setup complete."
