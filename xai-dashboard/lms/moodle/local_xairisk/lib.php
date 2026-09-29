<?php
defined('MOODLE_INTERNAL') || die();

/**
 * Add "At-risk insights" to the course navigation for users who may see it.
 */
function local_xairisk_extend_navigation_course(navigation_node $navigation, stdClass $course, context_course $context) {
    if (!has_capability('local/xairisk:viewcourse', $context)) {
        return;
    }
    if (!\local_xairisk\api_client::oulad_course($course->shortname)) {
        return;
    }
    $url = new moodle_url('/local/xairisk/course.php', ['id' => $course->id]);
    $navigation->add(get_string('courseinsights', 'local_xairisk'), $url, navigation_node::TYPE_CUSTOM,
        null, 'local_xairisk_course', new pix_icon('i/report', ''));
}

/**
 * Add advisor and administrator entries to the site navigation.
 */
function local_xairisk_extend_navigation(global_navigation $navigation) {
    if (!isloggedin() || isguestuser()) {
        return;
    }
    $sys = context_system::instance();
    if (has_capability('local/xairisk:viewcaseload', $sys)) {
        $navigation->add(get_string('caseload', 'local_xairisk'), new moodle_url('/local/xairisk/caseload.php'),
            navigation_node::TYPE_CUSTOM, null, 'local_xairisk_caseload', new pix_icon('i/users', ''))->showinflatnavigation = true;
    }
    if (has_capability('local/xairisk:viewoverview', $sys)) {
        $navigation->add(get_string('overview', 'local_xairisk'), new moodle_url('/local/xairisk/overview.php'),
            navigation_node::TYPE_CUSTOM, null, 'local_xairisk_overview', new pix_icon('i/stats', ''))->showinflatnavigation = true;
    }
}
