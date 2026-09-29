<?php
// Advisor view: caseload across all courses, with the reasoning averaged over the caseload.
require_once(__DIR__ . '/../../config.php');

use local_xairisk\api_client;
use local_xairisk\view;

$presentation = optional_param('presentation', '2014J', PARAM_ALPHANUM);

require_login();
$context = context_system::instance();
require_capability('local/xairisk:viewcaseload', $context);

$PAGE->set_url(new moodle_url('/local/xairisk/caseload.php', ['presentation' => $presentation]));
$PAGE->set_context($context);
$PAGE->set_pagelayout('standard');
$PAGE->set_title(get_string('caseload', 'local_xairisk'));
$PAGE->set_heading(get_string('caseload', 'local_xairisk'));

echo $OUTPUT->header();

$options = [];
foreach (['2013B', '2013J', '2014B', '2014J'] as $p) {
    $options[$p] = $p;
}
echo html_writer::div($OUTPUT->single_select($PAGE->url, 'presentation', $options, $presentation, null), 'xai-filter');

try {
    $d = api_client::get('advisor', '/api/advisor/caseload', ['presentation' => $presentation]);
} catch (moodle_exception $e) {
    echo $OUTPUT->notification($e->getMessage(), 'error');
    echo $OUTPUT->footer();
    exit;
}

$courses = $DB->get_records_list('course', 'shortname', array_unique(array_column($d['students'], 'course_shortname')), '', 'id, shortname');
$cid = [];
foreach ($courses as $c) {
    $cid[$c->shortname] = $c->id;
}

$mods = '';
foreach ($d['by_module'] as $m => $n) {
    $w = $d['n'] ? $n / $d['n'] * 100 : 0;
    $mods .= html_writer::div(html_writer::span(s($m)) . html_writer::span(html_writer::span('', '', ['style' => "width:{$w}%"]), 'xai-mbar')
        . html_writer::span($n), 'xai-mrow');
}

$table = new html_table();
$table->head = ['Student', 'Course', 'Risk', 'Assessments submitted'];
$table->attributes['class'] = 'generaltable xai-table';
foreach ($d['students'] as $s) {
    $course = isset($cid[$s['course_shortname']])
        ? html_writer::link(new moodle_url('/course/view.php', ['id' => $cid[$s['course_shortname']]]), s($s['course_shortname']))
        : s($s['course_shortname']);
    $table->data[] = [s($s['lms_username']), $course, view::risk_chip($s['probability'], true), $s['n_assessments_submitted']];
}

$left = view::stats(['students at or above ' . $d['watch_threshold'] => $d['n'], 'modules' => count($d['by_module'])])
    . html_writer::div($mods, 'xai-modules') . html_writer::tag('h4', 'Highest-risk students') . html_writer::div(html_writer::table($table), 'xai-x');
$right = view::trail('Caseload reasoning trail', 'Mean SHAP contribution across the caseload (log-odds)', $d['trail'])
    . view::note(get_string('cohortcaveat', 'local_xairisk'));

echo html_writer::div(html_writer::div($left, 'xai-card') . html_writer::div($right, 'xai-card'), 'xai-grid');
echo $OUTPUT->footer();
