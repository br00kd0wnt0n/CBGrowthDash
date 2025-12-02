import { useState, useEffect } from 'react'
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine } from 'recharts'
import { api, type HistoricalDataResponse, type ForecastRequest, type ForecastResponse, type AIInsightsResponse, type AIScenario } from '../services/api'
import './Dashboard.css'

// Number formatting utility (currently unused but available for future use)
// function formatNumber(num: number): string {
//   return num.toLocaleString('en-US')
// }

// Tooltip component
function HelpTooltip({ text }: { text: string }) {
  return (
    <div className="tooltip-container">
      <span className="tooltip-icon">?</span>
      <div className="tooltip-content">{text}</div>
    </div>
  )
}

// Scenario with forecast data
interface ScenarioWithForecast extends AIScenario {
  forecast?: ForecastResponse;
  visible: boolean;
  color: string;
}

export function Dashboard() {
  // State
  const [historicalData, setHistoricalData] = useState<HistoricalDataResponse | null>(null)
  const [forecastResults, setForecastResults] = useState<ForecastResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [aiLoading, setAiLoading] = useState(false)

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
  const [contentMix, setContentMix] = useState({
    Instagram: { "Short Video": 40, "Image": 30, "Carousel": 20, "Long Video": 5, "Story/Live": 5 },
    TikTok: { "Short Video": 90, "Image": 0, "Carousel": 0, "Long Video": 5, "Story/Live": 5 },
    YouTube: { "Short Video": 30, "Image": 0, "Carousel": 0, "Long Video": 60, "Story/Live": 10 },
    Facebook: { "Short Video": 30, "Image": 40, "Carousel": 20, "Long Video": 5, "Story/Live": 5 }
  })
  const [preset, setPreset] = useState('Balanced')
  const [months, setMonths] = useState(12)

  // AI Insights state
  const [aiInsights, setAiInsights] = useState<AIInsightsResponse | null>(null)
  const [scenarios, setScenarios] = useState<ScenarioWithForecast[]>([])
  const [expandedContentMix, setExpandedContentMix] = useState<string | null>(null)

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
  }, [currentFollowers, postsPerWeek, platformAllocation, contentMix, preset, months])

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

  const getAIRecommendations = async () => {
    setAiLoading(true)
    try {
      const request: ForecastRequest = {
        current_followers: currentFollowers,
        posts_per_week_total: postsPerWeek,
        platform_allocation: platformAllocation,
        content_mix_by_platform: contentMix,
        months,
        preset
      }

      const insights = await api.getAIInsights(request)
      setAiInsights(insights)

      // Initialize scenarios with forecasts
      const scenariosWithData: ScenarioWithForecast[] = insights.scenarios.map((scenario, idx) => ({
        ...scenario,
        visible: false,
        color: ['#4eb7ac', '#f06090', '#ffb84d'][idx] || '#4eb7ac'
      }))

      // Run forecasts for each scenario
      for (const scenario of scenariosWithData) {
        try {
          const scenarioRequest: ForecastRequest = {
            current_followers: currentFollowers,
            posts_per_week_total: scenario.posts_per_week,
            platform_allocation: scenario.platform_allocation,
            content_mix_by_platform: contentMix,
            months,
            preset: scenario.name
          }
          const forecast = await api.runForecast(scenarioRequest)
          scenario.forecast = forecast
        } catch (err) {
          console.error(`Failed to forecast scenario ${scenario.name}:`, err)
        }
      }

      setScenarios(scenariosWithData)
    } catch (err) {
      console.error('Failed to get AI recommendations:', err)
    } finally {
      setAiLoading(false)
    }
  }

  const toggleScenario = (index: number) => {
    setScenarios(prev => prev.map((s, i) =>
      i === index ? { ...s, visible: !s.visible } : s
    ))
  }

  const updatePlatformAllocation = (platform: string, value: number) => {
    setPlatformAllocation(prev => ({ ...prev, [platform]: value }))
  }

  const updateContentMix = (platform: string, contentType: string, value: number) => {
    setContentMix(prev => ({
      ...prev,
      [platform]: {
        ...prev[platform as keyof typeof prev],
        [contentType]: value
      }
    }))
  }

  const updateFollowerCount = (platform: string, value: string) => {
    const numValue = parseInt(value) || 0
    setCurrentFollowers(prev => ({ ...prev, [platform]: numValue }))
  }

  // Chart data - combine manual + visible scenarios
  const chartData = forecastResults?.monthly_data.map((item, idx) => {
    const dataPoint: any = {
      month: `M${item.month}`,
      Manual: Math.round(item.total)
    }

    // Add visible scenario lines
    scenarios.forEach(scenario => {
      if (scenario.visible && scenario.forecast) {
        dataPoint[scenario.name] = Math.round(scenario.forecast.monthly_data[idx]?.total || 0)
      }
    })

    return dataPoint
  }) || []

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
            <h3 className="section-header">
              Strategy Controls
              <HelpTooltip text="Adjust posting frequency, timeline, and strategy approach to test different growth scenarios" />
            </h3>

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
            <h3 className="section-header">
              Current Followers
              <HelpTooltip text="Enter the current follower count for each platform. These are your starting numbers for the forecast." />
            </h3>
            {Object.keys(currentFollowers).map(platform => (
              <div key={platform} className="follower-input-group">
                <label className="platform-name">{platform}</label>
                <input
                  type="number"
                  value={currentFollowers[platform as keyof typeof currentFollowers]}
                  onChange={e => updateFollowerCount(platform, e.target.value)}
                  className="follower-input"
                />
              </div>
            ))}
          </div>

          <div className="panel-section">
            <h3 className="section-header">
              Platform Allocation
              <HelpTooltip text="Set what percentage of your total weekly posts go to each platform. Must total 100%." />
            </h3>
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

          <div className="panel-section">
            <h3 className="section-header">
              Content Mix
              <HelpTooltip text="Define the content type distribution for each platform. Click platform names to expand." />
            </h3>
            {Object.keys(contentMix).map(platform => (
              <div key={platform} className="content-mix-section">
                <button
                  className="content-mix-header"
                  onClick={() => setExpandedContentMix(expandedContentMix === platform ? null : platform)}
                >
                  <span className="platform-name">{platform}</span>
                  <span className="expand-icon">{expandedContentMix === platform ? '▼' : '▶'}</span>
                </button>
                {expandedContentMix === platform && (
                  <div className="content-mix-controls">
                    {Object.keys(contentMix[platform as keyof typeof contentMix]).map(contentType => {
                      const platformMix = contentMix[platform as keyof typeof contentMix]
                      const value = platformMix[contentType as keyof typeof platformMix]
                      return (
                        <div key={contentType} className="content-mix-item">
                          <label>{contentType}</label>
                          <input
                            type="range"
                            min="0"
                            max="100"
                            value={value}
                            onChange={e => updateContentMix(platform, contentType, parseInt(e.target.value))}
                            className="slider content-slider"
                          />
                          <span className="content-value">{value}%</span>
                        </div>
                      )
                    })}
                  </div>
                )}
              </div>
            ))}
          </div>

          <div className="panel-section ai-section">
            <h3 className="section-header">
              <span>🤖 AI Insights</span>
              <HelpTooltip text="Get AI-powered recommendations for 3 alternative strategies: Optimized, Aggressive, and Conservative" />
            </h3>
            <button
              onClick={getAIRecommendations}
              disabled={aiLoading}
              className="ai-button"
            >
              {aiLoading ? 'Analyzing...' : '✨ Get AI Recommendations'}
            </button>

            {aiInsights && (
              <div className="ai-results">
                <div className="ai-analysis">{aiInsights.analysis}</div>

                <div className="ai-insights-list">
                  {aiInsights.key_insights.map((insight, idx) => (
                    <div key={idx} className="insight-item">💡 {insight}</div>
                  ))}
                </div>
              </div>
            )}

            <div className="insight-card">
              <div className="insight-label">Oversaturation Risk</div>
              <div className="insight-value" style={{color: riskColor}}>
                {riskLevel}
              </div>
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

            {scenarios.length > 0 && (
              <div className="scenario-toggles">
                <label className="scenario-toggle">
                  <input type="checkbox" checked disabled />
                  <span style={{color: 'var(--text-primary)'}}>Manual (Your Settings)</span>
                </label>
                {scenarios.map((scenario, idx) => (
                  <label key={idx} className="scenario-toggle">
                    <input
                      type="checkbox"
                      checked={scenario.visible}
                      onChange={() => toggleScenario(idx)}
                    />
                    <span style={{color: scenario.color}}>{scenario.name}</span>
                  </label>
                ))}
              </div>
            )}

            <ResponsiveContainer width="100%" height={400}>
              <LineChart data={chartData}>
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
                <Line type="monotone" dataKey="Manual" stroke="var(--text-primary)" strokeWidth={4} dot={false} />
                {scenarios.map((scenario, idx) =>
                  scenario.visible && (
                    <Line
                      key={idx}
                      type="monotone"
                      dataKey={scenario.name}
                      stroke={scenario.color}
                      strokeWidth={3}
                      dot={false}
                      strokeDasharray="5 5"
                    />
                  )
                )}
              </LineChart>
            </ResponsiveContainer>
          </div>

          {scenarios.length > 0 && (
            <div className="scenarios-comparison">
              <h3 className="section-header">AI Scenario Comparison</h3>
              <div className="scenarios-grid">
                {scenarios.map((scenario, idx) => (
                  <div key={idx} className="scenario-card" style={{borderColor: scenario.color}}>
                    <div className="scenario-header">
                      <h4 style={{color: scenario.color}}>{scenario.name}</h4>
                      <span className={`risk-badge risk-${scenario.risk_level.toLowerCase()}`}>
                        {scenario.risk_level} RISK
                      </span>
                    </div>
                    <div className="scenario-stats">
                      <div className="stat">
                        <span className="stat-label">Posts/Week</span>
                        <span className="stat-value">{scenario.posts_per_week}</span>
                      </div>
                      <div className="stat">
                        <span className="stat-label">Expected</span>
                        <span className="stat-value">{scenario.expected_outcome}</span>
                      </div>
                    </div>
                    <div className="scenario-reasoning">{scenario.reasoning}</div>
                    <div className="scenario-allocation">
                      {Object.entries(scenario.platform_allocation).map(([platform, percent]) => (
                        <div key={platform} className="allocation-bar">
                          <span className="allocation-label">{platform}</span>
                          <div className="allocation-bar-bg">
                            <div className="allocation-bar-fill" style={{width: `${percent}%`, background: scenario.color}}></div>
                          </div>
                          <span className="allocation-percent">{percent}%</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

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
              <h3 className="section-header">
                Historical Context
                <HelpTooltip text="Past performance data showing average engagement and sentiment metrics" />
              </h3>
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
                    {(() => {
                      if (historicalData.sentiment.length === 0) return 'N/A'
                      const latest = historicalData.sentiment[historicalData.sentiment.length - 1]
                      const positive = latest.Positive || 0
                      const neutral = latest.Neutral || 0
                      const negative = latest.Negative || 0
                      const total = positive + neutral + negative
                      if (total === 0) return 'N/A'
                      return ((positive / total) * 100).toFixed(0) + '% Positive'
                    })()}
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
