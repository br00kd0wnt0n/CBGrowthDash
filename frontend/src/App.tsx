import { useState, useEffect } from 'react'
import { api } from './services/api'
import './App.css'

function App() {
  const [status, setStatus] = useState<string>('Loading...')

  useEffect(() => {
    api.health()
      .then(data => setStatus(`API Status: ${data.status} (v${data.version})`))
      .catch(() => setStatus('API Offline'))
  }, [])

  return (
    <div className="app">
      <header className="header">
        <h1>Care Bears Growth Dashboard</h1>
        <p className="subtitle">Social Media Growth Forecasting</p>
      </header>

      <main className="main">
        <div className="status-card">
          <div className="status-indicator" />
          <p>{status}</p>
        </div>

        <div className="info-card">
          <h2>Dashboard Under Construction</h2>
          <p>React + FastAPI architecture deployed on Railway</p>
          <ul>
            <li>✅ Backend API ready</li>
            <li>✅ Forecast service implemented</li>
            <li>🚧 Frontend UI in progress</li>
            <li>🚧 Charts & visualizations coming soon</li>
          </ul>
        </div>
      </main>
    </div>
  )
}

export default App
