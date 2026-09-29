#!/bin/sh
# Load all OULAD courses, students and enrolments into Canvas (SIS import) and add the dashboard
# to every course as an External URL module item (iframe, no LTI).
#   CANVAS_URL=http://localhost:3000 CANVAS_TOKEN=<admin API token> sh lms/canvas/setup.sh
set -e
: "${CANVAS_URL:?}" "${CANVAS_TOKEN:?}"
DASHBOARD_URL=${DASHBOARD_URL:-http://localhost:8000/}
OUT=$(dirname "$0")/../sync/out/canvas
AUTH="Authorization: Bearer $CANVAS_TOKEN"

(cd "$OUT" && rm -f ../canvas_sis.zip && zip -q ../canvas_sis.zip terms.csv courses.csv users.csv enrollments.csv)
curl -sf -H "$AUTH" -F attachment=@"$OUT/../canvas_sis.zip" -F import_type=instructure_csv \
     "$CANVAS_URL/api/v1/accounts/1/sis_imports" > /tmp/sis.json
ID=$(python3 -c "import json;print(json.load(open('/tmp/sis.json'))['id'])")
echo "SIS import $ID started"
while :; do
  STATE=$(curl -sf -H "$AUTH" "$CANVAS_URL/api/v1/accounts/1/sis_imports/$ID" | python3 -c "import sys,json;d=json.load(sys.stdin);print(d['workflow_state'],d.get('progress'))")
  echo "  $STATE"; case "$STATE" in imported*|failed*) break;; esac; sleep 5
done

for SIS in $(tail -n +2 "$OUT/courses.csv" | cut -d, -f1); do
  CID="sis_course_id:$SIS"
  MID=$(curl -sf -H "$AUTH" -X POST "$CANVAS_URL/api/v1/courses/$CID/modules" -d "module[name]=At-risk insights" \
        | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")
  curl -sf -H "$AUTH" -X POST "$CANVAS_URL/api/v1/courses/$CID/modules/$MID/items" \
       -d "module_item[type]=ExternalUrl" -d "module_item[title]=At-risk insights dashboard" \
       -d "module_item[external_url]=$DASHBOARD_URL" -d "module_item[new_tab]=false" >/dev/null
  curl -sf -H "$AUTH" -X PUT "$CANVAS_URL/api/v1/courses/$CID/modules/$MID" -d "module[published]=true" >/dev/null
  echo "  dashboard added to $SIS"
done
echo "Canvas setup complete."
