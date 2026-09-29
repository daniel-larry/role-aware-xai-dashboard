import React from 'react'

/* Shared reasoning-trail component: signed contributions as diverging bars.
   Positive values push towards "at risk", negative values away from it. Used at three levels of
   aggregation (individual, cohort-averaged, full population). */
export default function ReasoningTrail({ title, subtitle, items, valueKey = 'contribution', unit, signed = true, showSign = true }) {
  const max = Math.max(1e-9, ...items.map((d) => Math.abs(d[valueKey])))
  return (
    <div className="trail">
      <div className="trail-head">
        <h3>{title}</h3>
        {subtitle && <div className="muted small">{subtitle}</div>}
      </div>
      <ul>
        {items.map((d, i) => {
          const v = d[valueKey] * (d.direction ?? 1)
          const w = (Math.abs(d[valueKey]) / max) * 50
          const up = signed ? v >= 0 : true
          return (
            <li key={i}>
              <span className="trail-label" title={d.label}>{d.label}</span>
              <span className="trail-bar">
                <span className="axis" />
                <span className={`bar ${up ? 'risk' : 'protect'}`}
                  style={up ? { left: '50%', width: `${w}%` } : { right: '50%', width: `${w}%` }} />
              </span>
              <span className="trail-val">{d[valueKey] >= 0 && signed && showSign ? '+' : ''}{d[valueKey].toFixed(3)}</span>
            </li>
          )
        })}
      </ul>
      <div className="legend small">
        <span><i className="sw risk" /> pushes towards at-risk</span>
        <span><i className="sw protect" /> pushes away from at-risk</span>
        {unit && <span className="muted">{unit}</span>}
      </div>
    </div>
  )
}
