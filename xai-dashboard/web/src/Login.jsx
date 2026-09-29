import React, { useState } from 'react'
import { login } from './api.js'

export default function Login({ onLogin }) {
  const [username, setU] = useState('')
  const [password, setP] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(e) {
    e.preventDefault()
    setBusy(true); setError('')
    try { onLogin(await login(username, password)) } catch (err) { setError(err.message) } finally { setBusy(false) }
  }

  return (
    <div className="login-wrap">
      <form className="card login" onSubmit={submit}>
        <h1>Role-Aware XAI Dashboard</h1>
        <p className="muted">Sign in to see the view for your role. The view is fixed by your account and cannot be switched without signing in again.</p>
        <label>Username<input value={username} onChange={(e) => setU(e.target.value)} autoComplete="username" /></label>
        <label>Password<input type="password" value={password} onChange={(e) => setP(e.target.value)} autoComplete="current-password" /></label>
        {error && <div className="error">{error}</div>}
        <button className="primary" disabled={busy || !username || !password}>{busy ? 'Signing in…' : 'Sign in'}</button>
        <p className="hint">Demo accounts: instructor, advisor, admin</p>
      </form>
    </div>
  )
}
