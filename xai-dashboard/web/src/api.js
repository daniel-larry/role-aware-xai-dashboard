const KEY = 'xai-dashboard-session'

export function getSession() {
  try { return JSON.parse(sessionStorage.getItem(KEY)) } catch { return null }
}

export function setSession(s) {
  try { s ? sessionStorage.setItem(KEY, JSON.stringify(s)) : sessionStorage.removeItem(KEY) } catch { /* storage blocked */ }
}

export async function login(username, password) {
  const r = await fetch('/api/login', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  })
  const data = await r.json()
  if (!r.ok) throw new Error(data.error || 'Login failed')
  return data
}

export async function get(path, token) {
  const r = await fetch(path, { headers: { Authorization: `Bearer ${token}` } })
  if (r.status === 401) throw Object.assign(new Error('Session expired'), { status: 401 })
  if (r.status === 403) throw Object.assign(new Error('Not permitted for this role'), { status: 403 })
  if (!r.ok) throw new Error(`Request failed (${r.status})`)
  return r.json()
}
