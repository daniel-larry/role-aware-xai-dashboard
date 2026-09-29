import React, { useEffect, useState } from 'react'
import { get } from './api.js'
import ReasoningTrail from './ReasoningTrail.jsx'

const f = (x) => x.toFixed(3)

export default function AdminView({ token, onExpired }) {
  const [d, setD] = useState(null)
  const [err, setErr] = useState('')

  useEffect(() => {
    get('/api/admin/overview', token).then(setD).catch((e) => (e.status === 401 ? onExpired() : setErr(e.message)))
  }, [])

  if (err) return <div className="error">{err}</div>
  if (!d) return <div className="muted">Loading…</div>
  const [[tn, fp], [fn, tp]] = d.confusion_matrix
  return (
    <div>
      <div className="view-head">
        <div>
          <h2>Institution overview</h2>
          <p className="muted">Model performance across the full population and the factors that drive predictions institution-wide.</p>
        </div>
      </div>
      <div className="tiles">
        {['accuracy', 'precision', 'recall', 'f1', 'auc'].map((k) => (
          <div key={k} className="tile"><span>{k === 'f1' ? 'F1-score' : k === 'auc' ? 'ROC-AUC' : k[0].toUpperCase() + k.slice(1)}</span><b>{f(d.metrics[k])}</b></div>))}
        <div className="tile"><span>Population</span><b>{d.population.toLocaleString()}</b></div>
      </div>
      <p className="muted small">Out-of-fold metrics, {d.protocol}. Model version {d.model_version}.</p>
      <div className="grid-2">
        <div className="card">
          <h3>Performance by course presentation</h3>
          <table>
            <thead><tr><th>Presentation</th><th>n</th><th>Accuracy</th><th>Precision</th><th>Recall</th><th>F1</th></tr></thead>
            <tbody>{Object.entries(d.per_presentation).map(([p, m]) => (
              <tr key={p}><td>{p}</td><td>{m.n.toLocaleString()}</td><td>{f(m.accuracy)}</td><td>{f(m.precision)}</td><td>{f(m.recall)}</td><td>{f(m.f1)}</td></tr>))}
            </tbody>
          </table>
          <h3>Confusion matrix (threshold 0.5)</h3>
          <table className="cm">
            <thead><tr><th /><th>Predicted not at risk</th><th>Predicted at risk</th></tr></thead>
            <tbody>
              <tr><th>Not at risk</th><td>{tn.toLocaleString()}</td><td>{fp.toLocaleString()}</td></tr>
              <tr><th>At risk</th><td>{fn.toLocaleString()}</td><td>{tp.toLocaleString()}</td></tr>
            </tbody>
          </table>
          <h3>Model comparison</h3>
          <table>
            <thead><tr><th>Model</th><th>Accuracy</th><th>Precision</th><th>Recall</th><th>F1</th></tr></thead>
            <tbody>{Object.entries(d.comparison).map(([k, m]) => (
              <tr key={k}><td>{k}{k === 'XGBoost' ? ' (in use)' : ''}</td><td>{f(m.accuracy)}</td><td>{f(m.precision)}</td><td>{f(m.recall)}</td><td>{f(m.f1)}</td></tr>))}
            </tbody>
          </table>
        </div>
        <div className="card">
          <ReasoningTrail title="Full-population reasoning trail" subtitle="Mean absolute SHAP value; colour shows the usual direction"
            items={d.global_trail} valueKey="mean_abs_shap" showSign={false} />
          <p className="note">Aggregate attributions describe how the model behaves across the institution. They are not an account of why students withdraw or fail.</p>
        </div>
      </div>
    </div>
  )
}
