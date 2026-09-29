<?php
defined('MOODLE_INTERNAL') || die();

/**
 * Create the "Academic advisor" system role that grants the caseload view.
 */
function xmldb_local_xairisk_install() {
    global $DB;
    // Moodle registers db/access.php only after this hook runs, so register it now.
    update_capabilities('local_xairisk');
    if (!$DB->record_exists('role', ['shortname' => 'xairiskadvisor'])) {
        $roleid = create_role('Academic advisor', 'xairiskadvisor',
            'Advisor role for the role-aware XAI at-risk dashboard (caseload view).');
        set_role_contextlevels($roleid, [CONTEXT_SYSTEM]);
        assign_capability('local/xairisk:viewcaseload', CAP_ALLOW, $roleid, context_system::instance()->id, true);
    }
    return true;
}
