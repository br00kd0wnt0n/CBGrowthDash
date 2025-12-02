import { useState, useEffect } from 'react'
import { api } from './services/api'
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
      </header>

      <main className="main">
        <div className="grid">
          <div className="card">
            <div className="card-header">
              <div className="card-icon primary">📊</div>
              <div>
                <h3 className="card-title">API Status</h3>
              </div>
            </div>
            <div className="card-content">
              <div className={`status-badge ${status.online ? 'online' : 'offline'}`}>
                <div className="status-indicator" />
                <span>{status.online ? 'Connected' : 'Disconnected'} {status.text}</span>
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <div className="card-icon secondary">🎯</div>
              <div>
                <h3 className="card-title">Platform Coverage</h3>
              </div>
            </div>
            <div className="card-content">
              <ul className="feature-list">
                <li className="feature-item">
                  <span className="feature-icon">📸</span>
                  <span>Instagram</span>
                </li>
                <li className="feature-item">
                  <span className="feature-icon">🎵</span>
                  <span>TikTok</span>
                </li>
                <li className="feature-item">
                  <span className="feature-icon">▶️</span>
                  <span>YouTube</span>
                </li>
                <li className="feature-item">
                  <span className="feature-icon">👥</span>
                  <span>Facebook</span>
                </li>
              </ul>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <div className="card-icon accent">✨</div>
              <div>
                <h3 className="card-title">Features</h3>
              </div>
            </div>
            <div className="card-content">
              <ul className="feature-list">
                <li className="feature-item">
                  <span className="feature-icon">✅</span>
                  <span>Growth Forecasting</span>
                </li>
                <li className="feature-item">
                  <span className="feature-icon">✅</span>
                  <span>Historical Analytics</span>
                </li>
                <li className="feature-item">
                  <span className="feature-icon">✅</span>
                  <span>Content Mix Optimization</span>
                </li>
                <li className="feature-item">
                  <span className="feature-icon">🚧</span>
                  <span>Interactive Charts</span>
                </li>
              </ul>
            </div>
          </div>

          <div className="card">
            <div className="card-header">
              <div className="card-icon warning">🚀</div>
              <div>
                <h3 className="card-title">Deployment</h3>
              </div>
            </div>
            <div className="card-content">
              <ul className="feature-list">
                <li className="feature-item">
                  <span className="feature-icon">✅</span>
                  <span>FastAPI Backend</span>
                </li>
                <li className="feature-item">
                  <span className="feature-icon">✅</span>
                  <span>React + TypeScript</span>
                </li>
                <li className="feature-item">
                  <span className="feature-icon">✅</span>
                  <span>Railway Hosting</span>
                </li>
                <li className="feature-item">
                  <span className="feature-icon">✅</span>
                  <span>GitHub Integration</span>
                </li>
              </ul>
            </div>
          </div>
        </div>

        <div className="card" style={{textAlign: 'center', padding: '3rem'}}>
          <div className="metric">
            <div className="metric-value">Coming Soon</div>
            <div className="metric-label">Interactive Forecast Dashboard</div>
          </div>
          <p style={{color: 'var(--text-secondary)', marginTop: '1.5rem', marginBottom: '2rem'}}>
            Full dashboard with charts, forecast forms, and real-time analytics
          </p>
          <button className="button button-primary">
            <span>🎨</span>
            <span>Dashboard in Development</span>
          </button>
        </div>
      </main>
    </div>
  )
}

export default App
