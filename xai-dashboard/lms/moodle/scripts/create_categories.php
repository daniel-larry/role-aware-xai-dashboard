<?php
// Create the course categories named in /import/courses.csv (e.g. "OULAD / AAA") so uploadcourse can resolve them.
define('CLI_SCRIPT', true);
require('/var/www/html/config.php');

$fh = fopen('/import/courses.csv', 'r');
$head = fgetcsv($fh);
$col = array_search('category_path', $head);
$paths = [];
while (($row = fgetcsv($fh)) !== false) {
    $paths[$row[$col]] = true;
}
fclose($fh);

foreach (array_keys($paths) as $path) {
    $parent = 0;
    foreach (array_map('trim', explode('/', $path)) as $name) {
        $id = $DB->get_field('course_categories', 'id', ['name' => $name, 'parent' => $parent]);
        if (!$id) {
            $id = core_course_category::create(['name' => $name, 'parent' => $parent])->id;
            mtrace("created category {$path}");
        }
        $parent = $id;
    }
}
