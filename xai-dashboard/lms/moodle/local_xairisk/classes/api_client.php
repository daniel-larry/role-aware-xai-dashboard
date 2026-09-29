<?php
namespace local_xairisk;

defined('MOODLE_INTERNAL') || die();

require_once($GLOBALS['CFG']->libdir . '/filelib.php');

/**
 * Server-to-server client for the prediction and explanation API.
 *
 * Moodle authenticates the user and decides their role from Moodle capabilities; the API trusts
 * the acting role only when the request carries the shared service key.
 */
class api_client {
    /**
     * @param string $role instructor | advisor | administrator
     * @param string $path API path starting with /api/
     * @param array $params query parameters
     * @return array decoded JSON
     * @throws \moodle_exception
     */
    public static function get(string $role, string $path, array $params = []): array {
        global $USER;
        $base = rtrim((string)get_config('local_xairisk', 'apiurl'), '/');
        $key = (string)get_config('local_xairisk', 'servicekey');
        if ($base === '' || $key === '') {
            throw new \moodle_exception('apierror', 'local_xairisk', '', 'plugin not configured');
        }
        $url = $base . $path . ($params ? '?' . http_build_query($params) : '');
        $curl = new \curl(['ignoresecurity' => true]); // Internal service on the Docker network.
        $curl->setHeader([
            'X-Service-Key: ' . $key,
            'X-Acting-Role: ' . $role,
            'X-Acting-User: ' . fullname($USER),
            'Accept: application/json',
        ]);
        $body = $curl->get($url, [], ['CURLOPT_TIMEOUT' => 60]);
        $info = $curl->get_info();
        $code = $info['http_code'] ?? 0;
        if ($curl->get_errno() || $code !== 200) {
            throw new \moodle_exception('apierror', 'local_xairisk', '', $code ?: $curl->error);
        }
        $data = json_decode($body, true);
        if (!is_array($data)) {
            throw new \moodle_exception('apierror', 'local_xairisk', '', 'invalid response');
        }
        return $data;
    }

    /**
     * Map a Moodle course short name such as "FFF-2014J" to the OULAD module and presentation.
     *
     * @return array|null [module, presentation]
     */
    public static function oulad_course(string $shortname): ?array {
        if (preg_match('/^([A-Z]{3})-(\d{4}[A-Z])$/', $shortname, $m)) {
            return [$m[1], $m[2]];
        }
        return null;
    }
}
