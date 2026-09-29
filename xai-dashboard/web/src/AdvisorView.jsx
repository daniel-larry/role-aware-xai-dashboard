import React, { useEffect, useState } from 'react'
import { get } from './api.js'
import ReasoningTrail from './ReasoningTrail.jsx'

const PRESENTATIONS = ['2013B', '2013J', '2014B', '2014J']

export default function AdvisorView({ token, onExpired }) {
  const [pres, setPres] = useState('2014J')
  const [data, setData] = useState(null)
  const [err, setErr] = useState('')

  useEffect(() => {
    setData(null)
    get(`/api/advisor/caseload?presentation=${pres}`, token).then(setData)
      .catch((e) => (e.status === 401 ? onExpired() : setErr(e.message)))
  }, [pres])

  return (
    <div>
      <div className="view-head">
        <div>
          <h2>My caseload</h2>
          <p className="muted">Students across all modules at or above the watch threshold, with the reasoning averaged over the caseload.</p>
        </div>
        <label className="select">Presentation
          <select value={pres} onChange={(e) => setPres(e.target.value)}>
            {PRESENTATIONS.map((p) => <option key={p}>{p}</option>)}
          </select>
        </label>
      </div>
      {err && <div className="error">{err}</div>}
      {!data ? <div className="muted">Loading caseload…</div> : (
        <div className="grid-2">
          <div className="card">
            <div className="stats">
              <div><b>{data.n}</b><span>students at or above {data.watch_threshold}</span></div>
              <div><b>{Object.keys(data.by_module).length}</b><span>modules</span></div>
            </div>
            <div className="modules">
              {Object.entries(data.by_module).map(([m, n]) => (
                <div key={m} className="module-row"><span>{m}</span>
                  <span className="mbar"><span style={{ width: `${(n / data.n) * 100}%` }} /></span><span>{n}</span></div>))}
            </div>
            <h4>Highest-risk students</h4>
            <div className="table-wrap short">
              <table>
                <thead><tr><th>Student</th><th>Module</th><th>Risk</th><th>Assessments</th></tr></thead>
                <tbody>{data.students.map((s) => (
                  <tr key={s.key}><td>{s.id_student}</td><td>{s.code_module}</td>
                    <td><span className="risk-chip hi">{s.probability >= 0.9995 ? '>99.9%' : `${(s.probability * 100).toFixed(1)}%`}</span></td><td>{s.n_assessments_submitted}</td></tr>))}
                </tbody>
              </table>
            </div>
          </div>
          <div className="card">
            <ReasoningTrail title="Caseload reasoning trail" subtitle="Mean SHAP contribution across the caseload (log-odds)" items={data.trail} />
            <p className="note">This shows what is common across the caseload, not the situation of any one student.</p>
          </div>
        </div>)}
    </div>
  )
}
