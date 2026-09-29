<?php
defined('MOODLE_INTERNAL') || die();

$capabilities = [
    // Instructor view: per-student risk and SHAP/LIME explanations for one course.
    'local/xairisk:viewcourse' => [
        'riskbitmask' => RISK_PERSONAL,
        'captype' => 'read',
        'contextlevel' => CONTEXT_COURSE,
        'archetypes' => ['editingteacher' => CAP_ALLOW, 'teacher' => CAP_ALLOW, 'manager' => CAP_ALLOW],
    ],
    // Advisor view: caseload across all courses, cohort-averaged explanations.
    'local/xairisk:viewcaseload' => [
        'riskbitmask' => RISK_PERSONAL,
        'captype' => 'read',
        'contextlevel' => CONTEXT_SYSTEM,
        'archetypes' => [],
    ],
    // Administrator view: institution-wide performance and full-population explanations.
    'local/xairisk:viewoverview' => [
        'captype' => 'read',
        'contextlevel' => CONTEXT_SYSTEM,
        'archetypes' => ['manager' => CAP_ALLOW],
    ],
];
