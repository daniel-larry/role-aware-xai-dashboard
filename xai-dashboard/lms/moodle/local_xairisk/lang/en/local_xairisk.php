<?php
defined('MOODLE_INTERNAL') || die();

$string['pluginname'] = 'At-risk insights (role-aware XAI)';
$string['xairisk:viewcourse'] = 'View at-risk predictions and explanations for a course';
$string['xairisk:viewcaseload'] = 'View the advisor caseload across courses';
$string['xairisk:viewoverview'] = 'View the institution-wide model overview';
$string['apiurl'] = 'Prediction API URL';
$string['apiurl_desc'] = 'Base URL of the prediction and explanation API, as reachable from the Moodle server.';
$string['servicekey'] = 'Service key';
$string['servicekey_desc'] = 'Shared secret sent to the API. Must match SERVICE_KEY on the API server.';
$string['courseinsights'] = 'At-risk insights';
$string['caseload'] = 'Advisor caseload';
$string['overview'] = 'Institution overview';
$string['notlinked'] = 'This course is not linked to a prediction model (course short name must look like FFF-2014J).';
$string['apierror'] = 'The prediction service could not be reached: {$a}';
$string['students'] = 'students';
$string['flagged'] = 'flagged';
$string['selectstudent'] = 'Select a student to see why the model flagged them.';
$string['caveat'] = 'Contributions describe the model\'s reasoning, not the causes of the student\'s situation. The decision about what to do stays with you.';
$string['cohortcaveat'] = 'This shows what is common across the caseload, not the situation of any one student.';
$string['popcaveat'] = 'Aggregate attributions describe how the model behaves across the institution. They are not an account of why students withdraw or fail.';
$string['privacy:metadata'] = 'The plugin sends no personal data to the API: it requests predictions by course short name and displays results for anonymised OULAD identifiers.';
