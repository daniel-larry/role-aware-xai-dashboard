<?php
// Instructor view: students of this course ranked by predicted risk, with SHAP and LIME for one student.
require_once(__DIR__ . '/../../config.php');

use local_xairisk\api_client;
use local_xairisk\view;

$courseid = required_param('id', PARAM_INT);
$studentkey = optional_param('student', '', PARAM_RAW_TRIMMED);

$course = get_course($courseid);
require_login($course);
$context = context_course::instance($course->id);
require_capability('local/xairisk:viewcourse', $context);

$PAGE->set_url(new moodle_url('/local/xairisk/course.php', ['id' => $course->id]));
$PAGE->set_context($context);
$PAGE->set_pagelayout('incourse');
$PAGE->set_title(get_string('courseinsights', 'local_xairisk') . ': ' . format_string($course->shortname));
$PAGE->set_heading(format_string($course->fullname));

echo $OUTPUT->header();
echo $OUTPUT->heading(get_string('courseinsights', 'local_xairisk'));

$map = api_client::oulad_course($course->shortname);
if (!$map) {
    echo $OUTPUT->notification(get_string('notlinked', 'local_xairisk'), 'warning');
    echo $OUTPUT->footer();
    exit;
}
[$module, $presentation] = $map;

try {
    $list = api_client::get('instructor', '/api/instructor/students', ['module' => $module, 'presentation' => $presentation]);
    $exp = null;
    if ($studentkey !== '') {
        if (strpos($studentkey, "{$module}|{$presentation}|") !== 0) {
            throw new moodle_exception('invalidparameter');
        }
        $exp = api_client::get('instructor', '/api/instructor/students/' . rawurlencode($studentkey) . '/explanation');
    }
} catch (moodle_exception $e) {
    echo $OUTPUT->notification($e->getMessage(), 'error');
    echo $OUTPUT->footer();
    exit;
}

// Link rows to the real Moodle user accounts enrolled in this course.
$usernames = array_column($list['students'], 'lms_username');
$users = $usernames ? $DB->get_records_list('user', 'username', $usernames, '', 'id, username') : [];
$byname = [];
foreach ($users as $u) {
    $byname[$u->username] = $u->id;
}

$table = new html_table();
$table->head = ['Student', 'Risk', 'Assessments submitted', 'Mean score', 'Active days', ''];
$table->attributes['class'] = 'generaltable xai-table';
foreach (array_slice($list['students'], 0, 300) as $s) {
    $name = s($s['lms_username']);
    if (isset($byname[$s['lms_username']])) {
        $name = html_writer::link(new moodle_url('/user/view.php', ['id' => $byname[$s['lms_username']], 'course' => $course->id]), $name);
    }
    $link = html_writer::link(new moodle_url($PAGE->url, ['student' => $s['key']]), 'Explain', ['class' => 'btn btn-sm btn-outline-primary']);
    $row = new html_table_row([$name, view::risk_chip($s['probability'], $s['flagged']), $s['n_assessments_submitted'],
        $s['mean_score'] ?? '–', $s['active_days'], $link]);
    if ($studentkey === $s['key']) {
        $row->attributes['class'] = 'xai-selected';
    }
    $table->data[] = $row;
}

$left = view::stats([get_string('students', 'local_xairisk') => $list['n'], get_string('flagged', 'local_xairisk') . ' (≥ 0.5)' => $list['n_flagged']])
    . html_writer::div(html_writer::div(html_writer::table($table), 'xai-x'), 'xai-scroll');

if ($exp) {
    $st = $exp['student'];
    $right = html_writer::tag('h3', 'Student ' . s($st['lms_username']) . ' ' . view::risk_chip($st['probability'], $st['flagged']))
        . view::trail('SHAP', 'Top 5 contributions (log-odds)', $exp['shap'])
        . view::trail('LIME', 'Top 5 local surrogate weights', $exp['lime'])
        . view::note('SHAP and LIME share ' . round($exp['overlap'] * 5) . ' of their top 5 features for this student. '
            . 'Where they agree, the explanation is more firmly characterised; where they differ, read it with more caution. '
            . get_string('caveat', 'local_xairisk'))
        . html_writer::div('Model version ' . s($exp['model_version']), 'xai-muted');
} else {
    $right = html_writer::div(get_string('selectstudent', 'local_xairisk'), 'xai-empty');
}

echo html_writer::div(html_writer::div($left, 'xai-card') . html_writer::div($right, 'xai-card'), 'xai-grid');
echo $OUTPUT->footer();
