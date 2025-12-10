import { useState, useEffect } from 'react'
import { api } from './services/api'
import { Dashboard } from './components/Dashboard'
import './App.css'

function App() {
  const [status, setStatus] = useState<{text: string, online: boolean}>({text: 'Connecting...', online: false})
  const [showInfo, setShowInfo] = useState(false)

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
          </div>
        </div>
        <div className="header-right">
          <button className="underhood-btn" onClick={() => window.dispatchEvent(new CustomEvent('openPresetOverlay'))}>Save / Load</button>
          <button className="underhood-btn" onClick={() => setShowInfo(true)}>Under the hood</button>
          <div className={`status-lockup ${status.online ? 'online' : 'offline'}`}>
            <img src="/logo.png" alt="Ralph" className="lockup-logo" />
            <div className="status-indicator" />
            <span className="lockup-text">{status.online ? 'Connected' : 'Offline'}</span>
          </div>
        </div>
      </header>

      <Dashboard />

      {showInfo && (
        <div className="modal-backdrop" role="dialog" aria-modal="true">
          <div className="modal">
            <div className="modal-header">
              <h2>Under the hood</h2>
              <button className="modal-close" aria-label="Close" onClick={() => setShowInfo(false)}>×</button>
            </div>
            <div className="modal-body">
              <h3>Forecast model</h3>
              <ul>
                <li>Multiplicative growth each week = Baseline monthly rate (platform) ÷ 4 × (1 + sensitivity × engagement × frequency effect × content multiplier × diversity × consistency × oversaturation penalty), capped by a monthly upper bound.</li>
                <li>Frequency effect is saturating; consistency boosts when posting within a healthy band; oversaturation reduces effectiveness beyond soft/hard caps.</li>
                <li>Content multiplier reflects format/platform fit (e.g., IG Carousels, TT Shorts, YT Long Video).</li>
                <li>Engagement index is built from historical mentions normalized by max and a sentiment uplift.</li>
              </ul>
              <h3>Per‑post additive followers</h3>
              <ul>
                <li>Additive weekly follows from organic posts = posts/week × per‑post gain × engagement quality × frequency quality × content multiplier.</li>
              </ul>
              <h3>Paid funnel (CPM → impressions → follows)</h3>
              <ul>
                <li>Impressions/week = (Paid Funnel Budget ÷ CPM) × 1000, allocated by Paid Allocation.</li>
                <li>Follows = impressions × view‑through rate (vtr) × engagement rate (er) × follow conversion (fcr), modestly scaled by content suitability.</li>
              </ul>
              <h3>Budget (CPF‑based)</h3>
              <ul>
                <li>Paid/Creator/Acquisition weekly followers = budget ÷ CPF (mid). CPF min/max drive optimistic/pessimistic bands.</li>
                <li>Confidence band on the forecast uses CPF min (optimistic) and CPF max (pessimistic).</li>
              </ul>
              <h3>Acquisition breakdown</h3>
              <ul>
                <li>Organic added = multiplicative + per‑post additive. Paid added = paid funnel + CPF‑based budgets.</li>
                <li>Shown per week internally; aggregated monthly for the UI.</li>
              </ul>
              <h3>ROI and CPF</h3>
              <ul>
                <li>Total spend = (Paid Funnel Budget + Paid/Creator/Acquisition Budgets) × weeks.</li>
                <li>Blended CPF = total spend ÷ total added followers.</li>
                <li>ROI = (Added Followers × Value per New Follower − Spend) ÷ Spend.</li>
              </ul>
              <h3>Historical context</h3>
              <ul>
                <li>Mentions, sentiment, and tags are read from historical CSVs or live CSV URLs (if configured).</li>
              </ul>
              <h3>AI Strategy Assessment</h3>
              <ul>
                <li>Objective: provide pragmatic, high‑impact guidance across posting cadence, platform allocation, content mix, and audience alignment.</li>
                <li>Convergence‑friendly: small gaps within practical tolerances are treated as acceptable (±2% allocation, ±3% content mix). This prevents nitpicky churn.</li>
                <li>No tail‑chasing: avoids reversing previous advice unless the estimated improvement exceeds ~1% of projected followers.</li>
                <li>Estimated impact: suggested changes are simulated against the same forecast engine; the UI shows the expected % change vs. current configuration.</li>
                <li>Healthy band bias: forecast favors quality over quantity. Posting within each platform’s healthy band improves per‑post effectiveness; oversaturation is gently penalized.</li>
                <li>Structured changes: when available, “Apply Optimizations” uses precise recommended changes (posts/week, allocation, content mix) rather than parsing text.</li>
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default App
