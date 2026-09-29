import React, { useEffect, useState } from 'react'
import { get } from './api.js'
import ReasoningTrail from './ReasoningTrail.jsx'

const pct = (p) => (p >= 0.9995 ? '>99.9%' : p <= 0.0005 ? '<0.1%' : `${(p * 100).toFixed(1)}%`)

export default function InstructorView({ token, onExpired }) {
  const [meta, setMeta] = useState(null)
  const [course, setCourse] = useState('')
  const [list, setList] = useState(null)
  const [sel, setSel] = useState(null)
  const [exp, setExp] = useState(null)
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState('')

  const fail = (e) => (e.status === 401 ? onExpired() : setErr(e.message))

  useEffect(() => {
    get('/api/meta', token).then((m) => {
      setMeta(m)
      // An LMS embed can preselect its course with ?course=FFF-2014J.
      const want = (new URLSearchParams(window.location.search).get('course') || '').replace('-', '|')
      const all = m.module_presentations.map((x) => `${x.code_module}|${x.code_presentation}`)
      setCourse(all.includes(want) ? want : all[0])
    }).catch(fail)
  }, [])

  useEffect(() => {
    if (!course) return
    const [m, p] = course.split('|')
    setList(null); setSel(null); setExp(null)
    get(`/api/instructor/students?module=${m}&presentation=${p}`, token).then(setList).catch(fail)
  }, [course])

  function open(s) {
    setSel(s); setExp(null); setLoading(true)
    get(`/api/instructor/students/${encodeURIComponent(s.key)}/explanation`, token)
      .then(setExp).catch(fail).finally(() => setLoading(false))
  }

  if (!meta) return <div className="muted">Loading…</div>
  return (
    <div>
      <div className="view-head">
        <div>
          <h2>My course</h2>
          <p className="muted">Individual students in the selected module presentation, ranked by predicted risk. Select a student to see why the model flagged them.</p>
        </div>
        <label className="select">Module presentation
          <select value={course} onChange={(e) => setCourse(e.target.value)}>
            {meta.module_presentations.map((c) => (
              <option key={c.code_module + c.code_presentation} value={`${c.code_module}|${c.code_presentation}`}>
                {c.code_module} {c.code_presentation} ({c.n})
              </option>))}
          </select>
        </label>
      </div>
      {err && <div className="error">{err}</div>}
      <div className="grid-2 instructor">
        <div className="card">
          {list ? (
            <>
              <div className="stats">
                <div><b>{list.n}</b><span>students</span></div>
                <div><b>{list.n_flagged}</b><span>flagged (≥ {meta.threshold})</span></div>
              </div>
              <div className="table-wrap">
                <table>
                  <thead><tr><th>Student</th><th>Risk</th><th>Assessments</th><th>Mean score</th><th>Active days</th></tr></thead>
                  <tbody>
                    {list.students.slice(0, 200).map((s) => (
                      <tr key={s.key} className={sel?.key === s.key ? 'active' : ''} onClick={() => open(s)}>
                        <td>{s.id_student}</td>
                        <td><span className={`risk-chip ${s.flagged ? 'hi' : 'lo'}`}>{pct(s.probability)}</span></td>
                        <td>{s.n_assessments_submitted}</td>
                        <td>{s.mean_score ?? '–'}</td>
                        <td>{s.active_days}</td>
                      </tr>))}
                  </tbody>
                </table>
              </div>
            </>) : <div className="muted">Loading students…</div>}
        </div>
        <div className="card">
          {!sel && <div className="empty muted">Select a student to see their reasoning trail.</div>}
          {sel && (
            <>
              <h3>Student {sel.id_student} <span className={`risk-chip ${sel.flagged ? 'hi' : 'lo'}`}>{pct(sel.probability)} at risk</span></h3>
              {loading && <div className="muted">Computing SHAP and LIME explanations…</div>}
              {exp && (
                <>
                  <div className="stack">
                    <ReasoningTrail title="SHAP" subtitle="Top 5 contributions (log-odds)" items={exp.shap} />
                    <ReasoningTrail title="LIME" subtitle="Top 5 local surrogate weights" items={exp.lime} />
                  </div>
                  <p className="note">SHAP and LIME share {Math.round(exp.overlap * 5)} of their top 5 features for this student.
                    Where they agree, the explanation is more firmly characterised; where they differ, read it with more caution.
                    Contributions describe the model&apos;s reasoning, not the causes of the student&apos;s situation.</p>
                  <p className="muted small">Model version {exp.model_version}</p>
                </>)}
            </>)}
        </div>
      </div>
    </div>
  )
}
