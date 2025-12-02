import { useState, useEffect } from 'react'
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { api, type HistoricalDataResponse, type ForecastRequest, type ForecastResponse } from '../services/api'
import './Dashboard.css'

type Tab = 'overview' | 'historical' | 'forecast' | 'results'

export function Dashboard() {
  const [activeTab, setActiveTab] = useState<Tab>('overview')
  const [historicalData, setHistoricalData] = useState<HistoricalDataResponse | null>(null)
  const [forecastResults, setForecastResults] = useState<ForecastResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Forecast form state
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

  useEffect(() => {
    if (activeTab === 'historical' && !historicalData) {
      loadHistoricalData()
    }
  }, [activeTab])

  const loadHistoricalData = async () => {
    setLoading(true)
    setError(null)
    try {
      const data = await api.getHistoricalData()
      setHistoricalData(data)
    } catch (err) {
      setError('Failed to load historical data')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const runForecast = async () => {
    setLoading(true)
    setError(null)
    try {
      const contentMix = {
        Instagram: {
          "Short Video": 40,
          "Image": 30,
          "Carousel": 20,
          "Long Video": 5,
          "Story/Live": 5
        },
        TikTok: {
          "Short Video": 90,
          "Image": 0,
          "Carousel": 0,
          "Long Video": 5,
          "Story/Live": 5
        },
        YouTube: {
          "Short Video": 30,
          "Image": 0,
          "Carousel": 0,
          "Long Video": 60,
          "Story/Live": 10
        },
        Facebook: {
          "Short Video": 30,
          "Image": 40,
          "Carousel": 20,
          "Long Video": 5,
          "Story/Live": 5
        }
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
      setActiveTab('results')
    } catch (err) {
      setError('Failed to run forecast')
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  const renderOverview = () => (
    <div className="overview">
      <div className="overview-stats">
        <div className="stat-card">
          <div className="stat-icon" style={{background: 'linear-gradient(135deg, var(--fountain-blue), var(--primary))'}}>📊</div>
          <div className="stat-content">
            <div className="stat-value">{(Object.values(currentFollowers).reduce((a, b) => a + b, 0) / 1000000).toFixed(1)}M</div>
            <div className="stat-label">Total Followers</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon" style={{background: 'linear-gradient(135deg, var(--bittersweet), var(--secondary))'}}>📈</div>
          <div className="stat-content">
            <div className="stat-value">{postsPerWeek}</div>
            <div className="stat-label">Posts per Week</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon" style={{background: 'linear-gradient(135deg, var(--froly), var(--accent))'}}>🎯</div>
          <div className="stat-content">
            <div className="stat-value">4</div>
            <div className="stat-label">Platforms</div>
          </div>
        </div>
        <div className="stat-card">
          <div className="stat-icon" style={{background: 'linear-gradient(135deg, var(--texas-rose), var(--mustard))'}}>⚡</div>
          <div className="stat-content">
            <div className="stat-value">{preset}</div>
            <div className="stat-label">Strategy</div>
          </div>
        </div>
      </div>

      <div className="quick-actions">
        <button className="action-button primary" onClick={() => setActiveTab('historical')}>
          <span className="action-icon">📊</span>
          <div>
            <div className="action-title">View Analytics</div>
            <div className="action-desc">Historical trends & sentiment</div>
          </div>
        </button>
        <button className="action-button secondary" onClick={() => setActiveTab('forecast')}>
          <span className="action-icon">🚀</span>
          <div>
            <div className="action-title">Run Forecast</div>
            <div className="action-desc">Predict growth & optimize</div>
          </div>
        </button>
        {forecastResults && (
          <button className="action-button accent" onClick={() => setActiveTab('results')}>
            <span className="action-icon">📈</span>
            <div>
              <div className="action-title">View Results</div>
              <div className="action-desc">Latest forecast projections</div>
            </div>
          </button>
        )}
      </div>
    </div>
  )

  const renderHistorical = () => {
    if (loading) return <div className="loading"><div className="spinner" /></div>
    if (error) return <div className="error">{error}</div>
    if (!historicalData) return null

    const mentionsChart = historicalData.mentions.map((item, idx) => ({
      week: new Date(item.Time).toLocaleDateString('en-US', {month: 'short', day: 'numeric'}),
      mentions: item.Mentions,
      engagement: historicalData.engagement_index[idx] * 100
    }))

    const sentimentChart = historicalData.sentiment.map(item => ({
      week: new Date(item.Time).toLocaleDateString('en-US', {month: 'short', day: 'numeric'}),
      positive: item.Positive,
      neutral: item.Neutral,
      negative: item.Negative
    }))

    return (
      <div className="historical-data">
        <div className="chart-section">
          <h3 className="chart-title">Mentions & Engagement Trends</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={mentionsChart}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="week" stroke="var(--text-secondary)" />
              <YAxis stroke="var(--text-secondary)" />
              <Tooltip
                contentStyle={{background: 'var(--bg-primary)', border: '1px solid var(--border)', borderRadius: '8px'}}
              />
              <Legend />
              <Line type="monotone" dataKey="mentions" stroke="var(--fountain-blue)" strokeWidth={3} dot={{fill: 'var(--fountain-blue)'}} />
              <Line type="monotone" dataKey="engagement" stroke="var(--froly)" strokeWidth={2} dot={{fill: 'var(--froly)'}} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        <div className="chart-section">
          <h3 className="chart-title">Sentiment Analysis</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={sentimentChart}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="week" stroke="var(--text-secondary)" />
              <YAxis stroke="var(--text-secondary)" />
              <Tooltip
                contentStyle={{background: 'var(--bg-primary)', border: '1px solid var(--border)', borderRadius: '8px'}}
              />
              <Legend />
              <Bar dataKey="positive" fill="var(--fountain-blue)" radius={[4, 4, 0, 0]} />
              <Bar dataKey="neutral" fill="var(--texas-rose)" radius={[4, 4, 0, 0]} />
              <Bar dataKey="negative" fill="var(--bittersweet)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    )
  }

  const renderForecast = () => (
    <div className="forecast-form">
      <div className="form-section">
        <h3 className="section-title">Current Follower Counts</h3>
        <div className="form-grid">
          {Object.keys(currentFollowers).map(platform => (
            <div key={platform} className="form-field">
              <label>{platform}</label>
              <input
                type="number"
                value={currentFollowers[platform as keyof typeof currentFollowers]}
                onChange={e => setCurrentFollowers({...currentFollowers, [platform]: parseInt(e.target.value) || 0})}
              />
            </div>
          ))}
        </div>
      </div>

      <div className="form-section">
        <h3 className="section-title">Posting Strategy</h3>
        <div className="form-grid">
          <div className="form-field">
            <label>Posts per Week (Total)</label>
            <input
              type="number"
              value={postsPerWeek}
              onChange={e => setPostsPerWeek(parseInt(e.target.value) || 0)}
            />
          </div>
          <div className="form-field">
            <label>Forecast Months</label>
            <input
              type="number"
              min="3"
              max="24"
              value={months}
              onChange={e => setMonths(parseInt(e.target.value) || 12)}
            />
          </div>
          <div className="form-field">
            <label>Strategy Preset</label>
            <select value={preset} onChange={e => setPreset(e.target.value)}>
              <option>Conservative</option>
              <option>Balanced</option>
              <option>Ambitious</option>
            </select>
          </div>
        </div>
      </div>

      <div className="form-section">
        <h3 className="section-title">Platform Allocation (%)</h3>
        <div className="form-grid">
          {Object.keys(platformAllocation).map(platform => (
            <div key={platform} className="form-field">
              <label>{platform}</label>
              <input
                type="number"
                min="0"
                max="100"
                value={platformAllocation[platform as keyof typeof platformAllocation]}
                onChange={e => setPlatformAllocation({...platformAllocation, [platform]: parseInt(e.target.value) || 0})}
              />
            </div>
          ))}
        </div>
      </div>

      <button className="submit-button" onClick={runForecast} disabled={loading}>
        {loading ? 'Running Forecast...' : '🚀 Run Growth Forecast'}
      </button>
    </div>
  )

  const renderResults = () => {
    if (!forecastResults) return <div className="empty-state">No forecast results yet. Run a forecast to see projections.</div>

    const chartData = forecastResults.monthly_data.map(item => ({
      month: `Month ${item.month}`,
      Instagram: Math.round(item.Instagram),
      TikTok: Math.round(item.TikTok),
      YouTube: Math.round(item.YouTube),
      Facebook: Math.round(item.Facebook),
      total: Math.round(item.total)
    }))

    return (
      <div className="results">
        <div className="results-summary">
          <div className="result-card">
            <div className="result-label">Projected Total</div>
            <div className="result-value">{(forecastResults.projected_total / 1000000).toFixed(2)}M</div>
          </div>
          <div className="result-card">
            <div className="result-label">Growth Goal</div>
            <div className="result-value">{(forecastResults.goal / 1000000).toFixed(2)}M</div>
          </div>
          <div className="result-card">
            <div className="result-label">Progress to Goal</div>
            <div className="result-value">{forecastResults.progress_to_goal.toFixed(1)}%</div>
          </div>
        </div>

        <div className="chart-section">
          <h3 className="chart-title">Growth Projections by Platform</h3>
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="month" stroke="var(--text-secondary)" />
              <YAxis stroke="var(--text-secondary)" />
              <Tooltip
                contentStyle={{background: 'var(--bg-primary)', border: '1px solid var(--border)', borderRadius: '8px'}}
              />
              <Legend />
              <Line type="monotone" dataKey="Instagram" stroke="var(--froly)" strokeWidth={3} />
              <Line type="monotone" dataKey="TikTok" stroke="var(--fountain-blue)" strokeWidth={3} />
              <Line type="monotone" dataKey="YouTube" stroke="var(--bittersweet)" strokeWidth={3} />
              <Line type="monotone" dataKey="Facebook" stroke="var(--texas-rose)" strokeWidth={3} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    )
  }

  return (
    <div className="dashboard">
      <div className="tabs">
        <button className={`tab ${activeTab === 'overview' ? 'active' : ''}`} onClick={() => setActiveTab('overview')}>
          <span>📊</span> Overview
        </button>
        <button className={`tab ${activeTab === 'historical' ? 'active' : ''}`} onClick={() => setActiveTab('historical')}>
          <span>📈</span> Historical Data
        </button>
        <button className={`tab ${activeTab === 'forecast' ? 'active' : ''}`} onClick={() => setActiveTab('forecast')}>
          <span>🚀</span> Forecast
        </button>
        <button className={`tab ${activeTab === 'results' ? 'active' : ''}`} onClick={() => setActiveTab('results')} disabled={!forecastResults}>
          <span>🎯</span> Results
        </button>
      </div>

      <div className="tab-content">
        {activeTab === 'overview' && renderOverview()}
        {activeTab === 'historical' && renderHistorical()}
        {activeTab === 'forecast' && renderForecast()}
        {activeTab === 'results' && renderResults()}
      </div>

      {error && (
        <div className="toast error">
          <span>⚠️</span> {error}
        </div>
      )}
    </div>
  )
}
