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
      <header className="header">
        <div className="header-content">
          <h1>Care Bears Growth Dashboard</h1>
          <p className="subtitle">Social Media Growth Forecasting & Analytics</p>
        </div>
        <div className="header-logos">
          <img src="/CB_logo_FINAL_FullColor.png" alt="Care Bears" className="logo" />
          <img src="/logo.png" alt="Ralph" className="logo" />
        </div>
        <div className={`status-badge ${status.online ? 'online' : 'offline'}`} style={{marginLeft: 'auto'}}>
          <div className="status-indicator" />
          <span>API {status.online ? 'Connected' : 'Offline'} {status.text}</span>
        </div>
      </header>

      <main className="main">
        <Dashboard />
      </main>
    </div>
  )
}

export default App
