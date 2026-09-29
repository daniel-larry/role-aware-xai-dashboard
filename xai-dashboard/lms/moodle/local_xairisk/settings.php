<?php
defined('MOODLE_INTERNAL') || die();

if ($hassiteconfig) {
    $settings = new admin_settingpage('local_xairisk', get_string('pluginname', 'local_xairisk'));
    $settings->add(new admin_setting_configtext('local_xairisk/apiurl', get_string('apiurl', 'local_xairisk'),
        get_string('apiurl_desc', 'local_xairisk'), 'http://xai-api:8000', PARAM_URL));
    $settings->add(new admin_setting_configpasswordunmask('local_xairisk/servicekey',
        get_string('servicekey', 'local_xairisk'), get_string('servicekey_desc', 'local_xairisk'), ''));
    $ADMIN->add('localplugins', $settings);
}
