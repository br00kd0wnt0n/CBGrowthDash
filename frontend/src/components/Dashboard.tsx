import { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts'
import { api, type HistoricalDataResponse, type ForecastRequest, type ForecastResponse } from '../services/api'
import './Dashboard.css'

export function Dashboard() {
  // State
  const [historicalData, setHistoricalData] = useState<HistoricalDataResponse | null>(null)
  const [forecastResults, setForecastResults] = useState<ForecastResponse | null>(null)
  const [loading, setLoading] = useState(false)

  // Form state with real-time updates
  const [currentFollowers, setCurrentFollowers] = useState({
    Instagram: 384000,
    TikTok: 572700,
    YouTube: 381000,
    Facebook: 590000
  })
  const [postsPerWeek, setPostsPerWeek] = useState(28)
  const [platformAllocation, setPlatformAllocation] = useState({
    Instagram: 35,
    TikTok: 35,
    YouTube: 15,
    Facebook: 15
  })
  const [preset, setPreset] = useState('Balanced')
  const [months, setMonths] = useState(12)

  const totalFollowers = Object.values(currentFollowers).reduce((a, b) => a + b, 0)
  const goalFollowers = totalFollowers * 2 // Double in 12 months
  const projectedTotal = forecastResults?.projected_total || 0
  const progressPercent = goalFollowers > 0 ? (projectedTotal / goalFollowers) * 100 : 0

  // Load historical data on mount
  useEffect(() => {
    loadHistoricalData()
    runForecast() // Initial forecast
  }, [])

  // Auto-run forecast when inputs change (with debounce)
  useEffect(() => {
    const timer = setTimeout(() => {
      runForecast()
    }, 500)
    return () => clearTimeout(timer)
  }, [currentFollowers, postsPerWeek, platformAllocation, preset, months])

  const loadHistoricalData = async () => {
    try {
      const data = await api.getHistoricalData()
      setHistoricalData(data)
    } catch (err) {
      console.error('Failed to load historical data:', err)
    }
  }

  const runForecast = async () => {
    setLoading(true)
    try {
      const contentMix = {
        Instagram: { "Short Video": 40, "Image": 30, "Carousel": 20, "Long Video": 5, "Story/Live": 5 },
        TikTok: { "Short Video": 90, "Image": 0, "Carousel": 0, "Long Video": 5, "Story/Live": 5 },
        YouTube: { "Short Video": 30, "Image": 0, "Carousel": 0, "Long Video": 60, "Story/Live": 10 },
        Facebook: { "Short Video": 30, "Image": 40, "Carousel": 20, "Long Video": 5, "Story/Live": 5 }
      }

      const request: ForecastRequest = {
        current_followers: currentFollowers,
        posts_per_week_total: postsPerWeek,
        platform_allocation: platformAllocation,
        content_mix_by_platform: contentMix,
        months,
        preset
      }

      const results = await api.runForecast(request)
      setForecastResults(results)
    } catch (err) {
      console.error('Failed to run forecast:', err)
    } finally {
      setLoading(false)
    }
  }

  const updatePlatformAllocation = (platform: string, value: number) => {
    setPlatformAllocation(prev => ({ ...prev, [platform]: value }))
  }

  // Chart data
  const forecastChart = forecastResults?.monthly_data.map(item => ({
    month: `M${item.month}`,
    Instagram: Math.round(item.Instagram),
    TikTok: Math.round(item.TikTok),
    YouTube: Math.round(item.YouTube),
    Facebook: Math.round(item.Facebook),
    total: Math.round(item.total)
  })) || []

  const riskLevel = postsPerWeek > 35 ? 'HIGH' : postsPerWeek > 28 ? 'MEDIUM' : 'LOW'
  const riskColor = riskLevel === 'HIGH' ? 'var(--bittersweet)' : riskLevel === 'MEDIUM' ? 'var(--texas-rose)' : 'var(--fountain-blue)'

  return (
    <div className="unified-dashboard">
      {/* KPI Progress Bar */}
      <div className="kpi-bar">
        <div className="kpi-section">
          <div className="kpi-label">CURRENT</div>
          <div className="kpi-value current">{(totalFollowers / 1000000).toFixed(2)}M</div>
        </div>
        <div className="kpi-arrow">→</div>
        <div className="kpi-section">
          <div className="kpi-label">12-MONTH GOAL</div>
          <div className="kpi-value goal">{(goalFollowers / 1000000).toFixed(2)}M</div>
        </div>
        <div className="kpi-separator"></div>
        <div className="kpi-section projected">
          <div className="kpi-label">PROJECTED</div>
          <div className="kpi-value">{(projectedTotal / 1000000).toFixed(2)}M</div>
          <div className="progress-badge" style={{
            background: progressPercent >= 95 ? 'var(--fountain-blue)' : progressPercent >= 80 ? 'var(--texas-rose)' : 'var(--bittersweet)'
          }}>
            {progressPercent.toFixed(0)}%
          </div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="dashboard-grid">
        {/* Left Panel: Controls */}
        <div className="control-panel">
          <div className="panel-section">
            <h3 className="section-header">Strategy Controls</h3>

            <div className="control-group">
              <label>Posts Per Week</label>
              <input
                type="range"
                min="14"
                max="50"
                value={postsPerWeek}
                onChange={e => setPostsPerWeek(parseInt(e.target.value))}
                className="slider"
              />
              <div className="control-value">{postsPerWeek} posts/week</div>
            </div>

            <div className="control-group">
              <label>Forecast Period</label>
              <input
                type="range"
                min="3"
                max="24"
                value={months}
                onChange={e => setMonths(parseInt(e.target.value))}
                className="slider"
              />
              <div className="control-value">{months} months</div>
            </div>

            <div className="control-group">
              <label>Strategy Preset</label>
              <select value={preset} onChange={e => setPreset(e.target.value)} className="preset-select">
                <option>Conservative</option>
                <option>Balanced</option>
                <option>Ambitious</option>
              </select>
            </div>
          </div>

          <div className="panel-section">
            <h3 className="section-header">Platform Allocation</h3>
            {Object.keys(platformAllocation).map(platform => (
              <div key={platform} className="platform-control">
                <div className="platform-header">
                  <span className="platform-name">{platform}</span>
                  <span className="platform-percent">{platformAllocation[platform as keyof typeof platformAllocation]}%</span>
                </div>
                <input
                  type="range"
                  min="0"
                  max="50"
                  value={platformAllocation[platform as keyof typeof platformAllocation]}
                  onChange={e => updatePlatformAllocation(platform, parseInt(e.target.value))}
                  className="slider platform-slider"
                />
              </div>
            ))}
          </div>

          <div className="panel-section ai-section">
            <h3 className="section-header">
              <span>🤖 AI Insights</span>
              <span className="badge">Beta</span>
            </h3>
            <div className="ai-placeholder">
              <div className="insight-card">
                <div className="insight-label">Oversaturation Risk</div>
                <div className="insight-value" style={{color: riskColor}}>
                  {riskLevel}
                </div>
              </div>
              <div className="insight-card">
                <div className="insight-label">Optimization Score</div>
                <div className="insight-value">Coming Soon</div>
              </div>
              <p className="ai-note">
                AI-powered strategy recommendations will analyze your posting frequency, content mix,
                and historical performance to suggest optimal configurations.
              </p>
            </div>
          </div>
        </div>

        {/* Right Panel: Visualizations */}
        <div className="viz-panel">
          <div className="chart-container main-chart">
            <div className="chart-header">
              <h2>Growth Forecast - {months} Months</h2>
              {loading && <span className="loading-indicator">Calculating...</span>}
            </div>
            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={forecastChart}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="month" stroke="var(--text-secondary)" />
                <YAxis stroke="var(--text-secondary)" tickFormatter={(value) => `${(value / 1000000).toFixed(1)}M`} />
                <Tooltip
                  contentStyle={{background: 'var(--bg-primary)', border: '1px solid var(--border)', borderRadius: '8px'}}
                  formatter={(value: number) => [(value / 1000).toFixed(0) + 'K', '']}
                />
                <Legend />
                <ReferenceLine
                  y={goalFollowers}
                  stroke="var(--fountain-blue)"
                  strokeDasharray="5 5"
                  label={{ value: 'Goal', position: 'right', fill: 'var(--fountain-blue)' }}
                />
                <Line type="monotone" dataKey="Instagram" stroke="var(--froly)" strokeWidth={3} dot={false} />
                <Line type="monotone" dataKey="TikTok" stroke="var(--fountain-blue)" strokeWidth={3} dot={false} />
                <Line type="monotone" dataKey="YouTube" stroke="var(--bittersweet)" strokeWidth={3} dot={false} />
                <Line type="monotone" dataKey="Facebook" stroke="var(--texas-rose)" strokeWidth={3} dot={false} />
                <Line type="monotone" dataKey="total" stroke="var(--text-primary)" strokeWidth={4} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          <div className="metrics-row">
            <div className="metric-card">
              <div className="metric-label">Current Reach</div>
              <div className="metric-value">{(totalFollowers / 1000000).toFixed(2)}M</div>
              <div className="metric-subtitle">Across 4 platforms</div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Weekly Posts</div>
              <div className="metric-value">{postsPerWeek}</div>
              <div className="metric-subtitle">{(postsPerWeek * 4.33).toFixed(0)} per month</div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Growth Target</div>
              <div className="metric-value">+{((goalFollowers - totalFollowers) / 1000000).toFixed(2)}M</div>
              <div className="metric-subtitle">100% increase</div>
            </div>
            <div className="metric-card">
              <div className="metric-label">Forecast Accuracy</div>
              <div className="metric-value">{progressPercent >= 95 ? '✓' : '⚠'}</div>
              <div className="metric-subtitle">{progressPercent >= 95 ? 'On track' : 'Needs adjustment'}</div>
            </div>
          </div>

          {historicalData && (
            <div className="historical-section">
              <h3 className="section-header">Historical Context</h3>
              <div className="historical-grid">
                <div className="historical-card">
                  <div className="historical-label">Avg Weekly Mentions</div>
                  <div className="historical-value">
                    {(historicalData.mentions.reduce((sum, item) => sum + item.Mentions, 0) / historicalData.mentions.length).toFixed(0)}
                  </div>
                </div>
                <div className="historical-card">
                  <div className="historical-label">Engagement Index</div>
                  <div className="historical-value">
                    {(historicalData.engagement_index.reduce((a, b) => a + b, 0) / historicalData.engagement_index.length * 100).toFixed(1)}%
                  </div>
                </div>
                <div className="historical-card">
                  <div className="historical-label">Sentiment</div>
                  <div className="historical-value">
                    {historicalData.sentiment.length > 0 ?
                      ((historicalData.sentiment[historicalData.sentiment.length - 1].Positive /
                        (historicalData.sentiment[historicalData.sentiment.length - 1].Positive +
                         historicalData.sentiment[historicalData.sentiment.length - 1].Neutral +
                         historicalData.sentiment[historicalData.sentiment.length - 1].Negative)) * 100).toFixed(0) + '% Positive'
                      : 'N/A'}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
