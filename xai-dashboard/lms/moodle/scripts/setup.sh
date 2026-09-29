#!/bin/sh
# Run inside the Moodle container:  docker compose exec moodle sh /scripts/setup.sh
# Installs the plugin, loads all OULAD courses, students, enrolments and staff, assigns roles,
# and points the plugin at the API.
set -e
cd /var/www/html
: "${SERVICE_KEY:?set SERVICE_KEY (same value as the api service)}"

php admin/cli/upgrade.php --non-interactive                       # installs local_xairisk
php admin/cli/cfg.php --component=local_xairisk --name=apiurl --set=http://api:8000
php admin/cli/cfg.php --component=local_xairisk --name=servicekey --set="$SERVICE_KEY"

php admin/tool/uploadcourse/cli/uploadcourse.php --mode=createnew --updatemode=nothing \
    --file=/import/courses.csv --delimiter=comma
php admin/tool/uploaduser/cli/uploaduser.php --file=/import/staff.csv --delimiter=comma --uutype=0
php admin/tool/uploaduser/cli/uploaduser.php --file=/import/users.csv --delimiter=comma --uutype=0

php /scripts/assign_roles.php
php admin/cli/purge_caches.php
echo "Moodle setup complete."
