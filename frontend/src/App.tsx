import { useState, useEffect } from 'react'
import { api } from './services/api'
import { Dashboard } from './components/Dashboard'
import './App.css'

function App() {
  const [status, setStatus] = useState<{text: string, online: boolean}>({text: 'Connecting...', online: false})

  useEffect(() => {
    api.health()
      .then(data => setStatus({text: `v${data.version}`, online: true}))
      .catch(() => setStatus({text: 'Offline', online: false}))
  }, [])

  return (
    <div className="app">
      <header className="header-compact">
        <div className="header-left">
          <img src="/CB_logo_FINAL_FullColor.png" alt="Care Bears" className="logo-small" />
          <div className="header-title">
            <h1>Growth Forecast Dashboard</h1>
            <span className="period">DEC 2025</span>
          </div>
        </div>
        <div className="header-right">
          <div className={`status-lockup ${status.online ? 'online' : 'offline'}`}>
            <img src="/logo.png" alt="Ralph" className="lockup-logo" />
            <div className="status-indicator" />
            <span className="lockup-text">{status.online ? 'Connected' : 'Offline'}</span>
          </div>
        </div>
      </header>

      <Dashboard />
    </div>
  )
}

export default App
