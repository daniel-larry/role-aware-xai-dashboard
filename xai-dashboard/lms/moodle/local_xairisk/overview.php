<?php
// Administrator view: institution-wide performance and full-population reasoning trail.
require_once(__DIR__ . '/../../config.php');

use local_xairisk\api_client;
use local_xairisk\view;

require_login();
$context = context_system::instance();
require_capability('local/xairisk:viewoverview', $context);

$PAGE->set_url(new moodle_url('/local/xairisk/overview.php'));
$PAGE->set_context($context);
$PAGE->set_pagelayout('standard');
$PAGE->set_title(get_string('overview', 'local_xairisk'));
$PAGE->set_heading(get_string('overview', 'local_xairisk'));

echo $OUTPUT->header();

try {
    $d = api_client::get('administrator', '/api/admin/overview');
} catch (moodle_exception $e) {
    echo $OUTPUT->notification($e->getMessage(), 'error');
    echo $OUTPUT->footer();
    exit;
}

$f = function($x) {
    return number_format((float)$x, 3);
};
$tiles = '';
foreach (['accuracy' => 'Accuracy', 'precision' => 'Precision', 'recall' => 'Recall', 'f1' => 'F1-score', 'auc' => 'ROC-AUC'] as $k => $l) {
    $tiles .= html_writer::div(html_writer::span($l) . html_writer::tag('b', $f($d['metrics'][$k])), 'xai-tile');
}
$tiles .= html_writer::div(html_writer::span('Population') . html_writer::tag('b', number_format($d['population'])), 'xai-tile');
echo html_writer::div($tiles, 'xai-tiles');
echo html_writer::div('Out-of-fold metrics, ' . s($d['protocol']) . '. Model version ' . s($d['model_version']) . '.', 'xai-muted');

$per = new html_table();
$per->head = ['Presentation', 'n', 'Accuracy', 'Precision', 'Recall', 'F1'];
$per->attributes['class'] = 'generaltable xai-table';
foreach ($d['per_presentation'] as $p => $m) {
    $per->data[] = [s($p), number_format($m['n']), $f($m['accuracy']), $f($m['precision']), $f($m['recall']), $f($m['f1'])];
}
[[$tn, $fp], [$fn, $tp]] = $d['confusion_matrix'];
$cm = new html_table();
$cm->head = ['', 'Predicted not at risk', 'Predicted at risk'];
$cm->attributes['class'] = 'generaltable xai-table';
$cm->data = [['Not at risk', number_format($tn), number_format($fp)], ['At risk', number_format($fn), number_format($tp)]];
$cmp = new html_table();
$cmp->head = ['Model', 'Accuracy', 'Precision', 'Recall', 'F1'];
$cmp->attributes['class'] = 'generaltable xai-table';
foreach ($d['comparison'] as $k => $m) {
    $cmp->data[] = [s($k) . ($k === 'XGBoost' ? ' (in use)' : ''), $f($m['accuracy']), $f($m['precision']), $f($m['recall']), $f($m['f1'])];
}

$left = html_writer::tag('h4', 'Performance by course presentation') . html_writer::table($per)
    . html_writer::tag('h4', 'Confusion matrix (threshold 0.5)') . html_writer::table($cm)
    . html_writer::tag('h4', 'Model comparison') . html_writer::table($cmp);
$right = view::trail('Full-population reasoning trail', 'Mean absolute SHAP value; colour shows the usual direction',
        $d['global_trail'], 'mean_abs_shap', false)
    . view::note(get_string('popcaveat', 'local_xairisk'));

echo html_writer::div(html_writer::div($left, 'xai-card') . html_writer::div($right, 'xai-card'), 'xai-grid');
echo $OUTPUT->footer();
