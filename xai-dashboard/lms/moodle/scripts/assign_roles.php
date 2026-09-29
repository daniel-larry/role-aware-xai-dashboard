<?php
// Assign the system-level roles used by the dashboard: advisor -> Academic advisor, manager -> Manager.
define('CLI_SCRIPT', true);
require('/var/www/html/config.php');

$sys = context_system::instance();
$pairs = ['advisor' => 'xairiskadvisor', 'manager' => 'manager'];
foreach ($pairs as $username => $roleshort) {
    $user = $DB->get_record('user', ['username' => $username], '*', MUST_EXIST);
    $role = $DB->get_record('role', ['shortname' => $roleshort], '*', MUST_EXIST);
    role_assign($role->id, $user->id, $sys->id);
    mtrace("assigned {$roleshort} to {$username}");
}
