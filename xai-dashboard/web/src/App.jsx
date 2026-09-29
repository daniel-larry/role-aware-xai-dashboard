import React, { useState } from 'react'
import { getSession, setSession } from './api.js'
import Login from './Login.jsx'
import InstructorView from './InstructorView.jsx'
import AdvisorView from './AdvisorView.jsx'
import AdminView from './AdminView.jsx'

const ROLE_LABEL = { instructor: 'Instructor', advisor: 'Academic Advisor', administrator: 'Administrator' }

export default function App() {
  const [session, setS] = useState(getSession())
  const update = (s) => { setSession(s); setS(s) }

  if (!session) return <Login onLogin={update} />

  const View = { instructor: InstructorView, advisor: AdvisorView, administrator: AdminView }[session.role]
  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">Role-Aware XAI Dashboard <span className="muted">at-risk prediction</span></div>
        <div className="who">
          <span className="role-pill">{ROLE_LABEL[session.role]}</span>
          <span className="muted">{session.name}</span>
          <button className="link" onClick={() => update(null)}>Sign out</button>
        </div>
      </header>
      <main className="content">
        <View token={session.token} onExpired={() => update(null)} />
      </main>
    </div>
  )
}
