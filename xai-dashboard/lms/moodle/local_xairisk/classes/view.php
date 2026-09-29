<?php
namespace local_xairisk;

defined('MOODLE_INTERNAL') || die();

use html_writer;

/**
 * Shared rendering helpers. The same reasoning-trail component is used at three levels of
 * aggregation: individual (instructor), cohort-averaged (advisor) and full population (administrator).
 */
class view {
    public static function pct(float $p): string {
        if ($p >= 0.9995) {
            return '>99.9%';
        }
        if ($p <= 0.0005) {
            return '<0.1%';
        }
        return number_format($p * 100, 1) . '%';
    }

    public static function risk_chip(float $p, bool $flagged): string {
        return html_writer::span(self::pct($p), 'xai-chip ' . ($flagged ? 'xai-hi' : 'xai-lo'));
    }

    /**
     * @param array $items each with 'label' and a numeric value under $key (optional 'direction')
     */
    public static function trail(string $title, string $subtitle, array $items, string $key = 'contribution',
            bool $showsign = true): string {
        $max = 1e-9;
        foreach ($items as $d) {
            $max = max($max, abs((float)$d[$key]));
        }
        $rows = '';
        foreach ($items as $d) {
            $v = (float)$d[$key];
            $signed = $v * (isset($d['direction']) ? (int)$d['direction'] : 1);
            $w = abs($v) / $max * 50;
            $up = $signed >= 0;
            $style = $up ? "left:50%;width:{$w}%" : "right:50%;width:{$w}%";
            $bar = html_writer::span('', 'xai-axis') . html_writer::span('', 'xai-bar ' . ($up ? 'xai-risk' : 'xai-protect'),
                ['style' => $style]);
            $val = ($showsign && $v >= 0 ? '+' : '') . number_format($v, 3);
            $rows .= html_writer::tag('li',
                html_writer::span(s($d['label']), 'xai-label', ['title' => $d['label']]) .
                html_writer::span($bar, 'xai-track') .
                html_writer::span($val, 'xai-val'));
        }
        $legend = html_writer::div(
            html_writer::span(html_writer::tag('i', '', ['class' => 'xai-sw xai-risk']) . ' pushes towards at-risk') . ' ' .
            html_writer::span(html_writer::tag('i', '', ['class' => 'xai-sw xai-protect']) . ' pushes away from at-risk'),
            'xai-legend');
        return html_writer::div(
            html_writer::tag('h4', s($title)) . html_writer::div(s($subtitle), 'xai-muted') .
            html_writer::tag('ul', $rows, ['class' => 'xai-trail']) . $legend, 'xai-trailbox');
    }

    public static function note(string $text): string {
        return html_writer::div(s($text), 'xai-note');
    }

    public static function stats(array $pairs): string {
        $out = '';
        foreach ($pairs as $label => $value) {
            $out .= html_writer::div(html_writer::tag('b', s($value)) . html_writer::span(s($label)), 'xai-stat');
        }
        return html_writer::div($out, 'xai-stats');
    }
}
