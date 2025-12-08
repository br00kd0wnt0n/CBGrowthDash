import { useState, useEffect } from 'react'
import { LineChart, ComposedChart, Area, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, ReferenceLine, LabelList } from 'recharts'
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
  const [postsPerWeek, setPostsPerWeek] = useState(40)
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
  // Paid funnel (CPM) state
  const [enablePaid, setEnablePaid] = useState(false)
  const [paidFunnelBudgetWeek, setPaidFunnelBudgetWeek] = useState(2500)
  const [paidCPM, setPaidCPM] = useState(10)
  const [paidAllocation, setPaidAllocation] = useState({
    Instagram: 35,
    TikTok: 35,
    YouTube: 15,
    Facebook: 15
  })
  // Budget & CPF state
  const [enableBudget, setEnableBudget] = useState(true)
  const [paidBudgetWeek, setPaidBudgetWeek] = useState(641)        // ~$33.3k/year
  const [creatorBudgetWeek, setCreatorBudgetWeek] = useState(641)   // ~$33.3k/year
  const [acquisitionBudgetWeek, setAcquisitionBudgetWeek] = useState(641) // ~$33.3k/year (total = $100k/year)
  const [cpfMin, setCpfMin] = useState(0.50)
  const [cpfMid, setCpfMid] = useState(0.75)
  const [cpfMax, setCpfMax] = useState(1.00)
  const [valuePerFollower, setValuePerFollower] = useState(0)

  // AI Insights state
  const [aiInsights, setAiInsights] = useState<AIInsightsResponse | null>(null)
  const [scenarios, setScenarios] = useState<ScenarioWithForecast[]>([])
  const [expandedContentMix, setExpandedContentMix] = useState<string | null>(null)
  const [historicalTab, setHistoricalTab] = useState<'mentions' | 'sentiment' | 'tags' | 'growth'>('mentions')
  // Confidence band totals (per month)
  const [bandHigh, setBandHigh] = useState<number[] | null>(null) // optimistic (CPF min)
  const [bandLow, setBandLow] = useState<number[] | null>(null)   // pessimistic (CPF max)
  // Followers history for combined chart and mode toggle
  const [followerHistory, setFollowerHistory] = useState<any[] | null>(null)
  const [chartMode, setChartMode] = useState<'historical'|'forecast'|'both'>('both')
  // Platform visibility toggles
  const [showPlatforms, setShowPlatforms] = useState<{Total:boolean; Instagram:boolean; TikTok:boolean; YouTube:boolean; Facebook:boolean}>({
    Total: true,
    Instagram: true,
    TikTok: true,
    YouTube: true,
    Facebook: true,
  })
  // Month selector for acquisition breakdown
  const [selectedBreakdownIndex, setSelectedBreakdownIndex] = useState<number>(0)
  // Collapsible sections
  const [historicalCollapsed, setHistoricalCollapsed] = useState<boolean>(true)
  // Sidebar section collapse states
  const [sidebarCollapsed, setSidebarCollapsed] = useState<{[key:string]:boolean}>({
    strategy: true,
    followers: true,
    platform: true,
    contentMix: true,
    paidMedia: true,
    budget: true,
    aiInsights: true,
    advanced: true,
  })

  const totalFollowers = Object.values(currentFollowers).reduce((a, b) => a + b, 0)
  const goalFollowers = totalFollowers * 2 // Double in 12 months
  const projectedTotal = forecastResults?.projected_total || 0
  const progressPercent = goalFollowers > 0 ? (projectedTotal / goalFollowers) * 100 : 0

  // ROI + CPF calculations
  const weeksHorizon = months * 4
  const weeklySpend = (enablePaid ? paidFunnelBudgetWeek : 0) + (enableBudget ? (paidBudgetWeek + creatorBudgetWeek + acquisitionBudgetWeek) : 0)
  const totalSpend = weeklySpend * weeksHorizon
  const weeksPerMonth = 4.33
  const monthlySpend = weeklySpend * weeksPerMonth
  const annualSpend = weeklySpend * 52
  const annualDisplay = annualSpend >= 1_000_000
    ? `$${(annualSpend/1_000_000).toFixed(1)}M`
    : `$${(annualSpend/1000).toFixed(1)}k`
  const totalAddedFollowers = forecastResults?.monthly_data.reduce((sum, m) => sum + (m.added || 0), 0) || 0
  const blendedCPF = totalAddedFollowers > 0 ? totalSpend / totalAddedFollowers : 0
  const estROI = (valuePerFollower > 0 && totalSpend > 0) ? ((totalAddedFollowers * valuePerFollower - totalSpend) / totalSpend) * 100 : null

  // Load historical data on mount
  useEffect(() => {
    loadHistoricalData()
    // Load follower history (from workbook) for unified chart if available
    api.getFollowersHistory().then(res=> {
      console.log('Follower history loaded:', res.data?.length, 'rows')
      setFollowerHistory(res.data || null)
    }).catch(err => {
      console.error('Failed to load follower history:', err)
      setFollowerHistory(null)
    })
    runForecast() // Initial forecast
    // Auto-generate AI insights on first load
    getAIRecommendations()
  }, [])

  // Auto-run forecast when inputs change (with debounce)
  useEffect(() => {
    const timer = setTimeout(() => {
      runForecast()
    }, 500)
    return () => clearTimeout(timer)
  }, [
    currentFollowers,
    postsPerWeek,
    platformAllocation,
    contentMix,
    preset,
    months,
    // Paid funnel deps
    enablePaid,
    paidFunnelBudgetWeek,
    paidCPM,
    paidAllocation,
    // Budget model deps
    enableBudget,
    paidBudgetWeek,
    creatorBudgetWeek,
    acquisitionBudgetWeek,
    cpfMin,
    cpfMid,
    cpfMax,
  ])

  // Keep paid allocation in sync with organic when paid is disabled
  useEffect(() => {
    if (!enablePaid) {
      setPaidAllocation(platformAllocation as any)
    }
  }, [platformAllocation, enablePaid])

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
      // Compute impressions from CPM if enabled
      const computedImpr = enablePaid && paidCPM > 0 ? Math.round((paidFunnelBudgetWeek / paidCPM) * 1000) : 0

      const request: ForecastRequest = {
        current_followers: currentFollowers,
        posts_per_week_total: postsPerWeek,
        platform_allocation: platformAllocation,
        content_mix_by_platform: contentMix,
        months,
        preset,
        ...(enablePaid ? {
          paid_impressions_per_week_total: computedImpr,
          paid_allocation: paidAllocation,
        } : {}),
        ...(enableBudget ? {
          paid_budget_per_week_total: paidBudgetWeek,
          creator_budget_per_week_total: creatorBudgetWeek,
          acquisition_budget_per_week_total: acquisitionBudgetWeek,
          cpf_paid: { min: cpfMin, mid: cpfMid, max: cpfMax },
          cpf_creator: { min: cpfMin, mid: cpfMid, max: cpfMax },
          cpf_acquisition: { min: cpfMin, mid: cpfMid, max: cpfMax },
        } : {})
      }

      const results = await api.runForecast(request)
      setForecastResults(results)

      // Confidence band using CPF min/max when budget modeling is enabled
      if (enableBudget) {
        const baseBandReq: ForecastRequest = {
          current_followers: currentFollowers,
          posts_per_week_total: postsPerWeek,
          platform_allocation: platformAllocation,
          content_mix_by_platform: contentMix,
          months,
          preset,
          ...(enablePaid ? { paid_impressions_per_week_total: computedImpr, paid_allocation: paidAllocation } : {}),
          paid_budget_per_week_total: paidBudgetWeek,
          creator_budget_per_week_total: creatorBudgetWeek,
          acquisition_budget_per_week_total: acquisitionBudgetWeek,
        }

        // Optimistic (CPF min)
        const optimisticReq: ForecastRequest = {
          ...baseBandReq,
          cpf_paid: { min: cpfMin, mid: cpfMin, max: cpfMin },
          cpf_creator: { min: cpfMin, mid: cpfMin, max: cpfMin },
          cpf_acquisition: { min: cpfMin, mid: cpfMin, max: cpfMin },
        }
        const pessimisticReq: ForecastRequest = {
          ...baseBandReq,
          cpf_paid: { min: cpfMax, mid: cpfMax, max: cpfMax },
          cpf_creator: { min: cpfMax, mid: cpfMax, max: cpfMax },
          cpf_acquisition: { min: cpfMax, mid: cpfMax, max: cpfMax },
        }

        const [optRes, pessRes] = await Promise.all([
          api.runForecast(optimisticReq),
          api.runForecast(pessimisticReq),
        ])
        setBandHigh(optRes.monthly_data.map(m => m.total))
        setBandLow(pessRes.monthly_data.map(m => m.total))
      } else {
        setBandHigh(null)
        setBandLow(null)
      }
    } catch (err) {
      console.error('Failed to run forecast:', err)
    } finally {
      setLoading(false)
    }
  }

  const getAIRecommendations = async () => {
    setAiLoading(true)
    try {
      // Compute impressions from CPM if enabled
      const computedImpr = enablePaid && paidCPM > 0 ? Math.round((paidFunnelBudgetWeek / paidCPM) * 1000) : 0

      // Build full request with budget and projection context
      const request: ForecastRequest = {
        current_followers: currentFollowers,
        posts_per_week_total: postsPerWeek,
        platform_allocation: platformAllocation,
        content_mix_by_platform: contentMix,
        months,
        preset,
        // Include budget info for AI context
        paid_budget_per_week_total: enableBudget ? paidBudgetWeek : 0,
        creator_budget_per_week_total: enableBudget ? creatorBudgetWeek : 0,
        acquisition_budget_per_week_total: enableBudget ? acquisitionBudgetWeek : 0,
        cpf_paid: { min: cpfMin, mid: cpfMid, max: cpfMax },
        // Pass projections for AI context (added as extra fields)
        ...(projectedTotal ? { _projected_total: projectedTotal } : {}),
        ...(goalFollowers ? { _goal_followers: goalFollowers } : {}),
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
            preset: preset,  // Use the original user-selected preset
            ...(enablePaid ? {
              paid_impressions_per_week_total: computedImpr,
              paid_allocation: paidAllocation,
            } : {}),
            ...(enableBudget ? {
              paid_budget_per_week_total: paidBudgetWeek,
              creator_budget_per_week_total: creatorBudgetWeek,
              acquisition_budget_per_week_total: acquisitionBudgetWeek,
              cpf_paid: { min: cpfMin, mid: cpfMid, max: cpfMax },
              cpf_creator: { min: cpfMin, mid: cpfMid, max: cpfMax },
              cpf_acquisition: { min: cpfMin, mid: cpfMid, max: cpfMax },
            } : {})
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

  // Dynamic AI insight (single, contextual). Debounced refresh when >5% change.
  const [aiInsight, setAiInsight] = useState<string>('')
  const [aiLoadingCompact, setAiLoadingCompact] = useState(false)
  const [lastInsightKey, setLastInsightKey] = useState<string>('')
  // LLM Parameter Tuning modal state
  const [showTune, setShowTune] = useState(false)
  const [tuneLoading, setTuneLoading] = useState(false)
  const [tuneSuggestions, setTuneSuggestions] = useState<{key:string; current:number; suggested:number; reason:string; confidence:string; accept?:boolean}[]>([])
  useEffect(() => {
    const keyObj = {
      goal: goalFollowers,
      projected_total: projectedTotal,
      posts_per_week_total: postsPerWeek,
      platform_allocation: platformAllocation,
      months,
    }
    const key = JSON.stringify(keyObj)
    const prev = lastInsightKey ? JSON.parse(lastInsightKey) : null
    const pct = (a:number,b:number)=> b>0? Math.abs((a-b)/b)*100 : 0
    const changedMeaningfully = prev ? pct(projectedTotal, prev.projected_total) > 5 : true
    const timer = setTimeout(async () => {
      if (!changedMeaningfully || key === lastInsightKey) return
      setAiLoadingCompact(true)
      try {
        const cached = (window as any)._insightCache || {}
        if (cached[key]) { setAiInsight(cached[key]); setAiLoadingCompact(false); setLastInsightKey(key); return }
        const resp = await api.getAIInsight({
          goal: goalFollowers,
          projected_total: projectedTotal,
          posts_per_week_total: postsPerWeek,
          platform_allocation: platformAllocation,
          months,
          progress_to_goal: goalFollowers>0? (projectedTotal/goalFollowers)*100 : 0,
        })
        setAiInsight(resp.insight)
        ;(window as any)._insightCache = { ...(window as any)._insightCache, [key]: resp.insight }
        setLastInsightKey(key)
      } catch (e) {
        // ignore
      } finally {
        setAiLoadingCompact(false)
      }
    }, 2000)
    return () => clearTimeout(timer)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectedTotal, postsPerWeek, platformAllocation, months, goalFollowers])

  const toggleScenario = (index: number) => {
    setScenarios(prev => prev.map((s, i) =>
      i === index ? { ...s, visible: !s.visible } : s
    ))
  }

  const toggleSidebarSection = (key: string) => {
    const willExpand = sidebarCollapsed[key as keyof typeof sidebarCollapsed]
    setSidebarCollapsed(prev => ({ ...prev, [key]: !prev[key] }))

    // Auto-fetch AI insights when expanding the AI section
    if (key === 'aiInsights' && willExpand && !aiLoading && !aiInsights) {
      getAIRecommendations()
    }
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

  // Chart data - combine manual + visible scenarios + individual platforms
  // Forecast starts Jan 2026, runs 12 months through Dec 2026
  const FORECAST_MONTH_LABELS = ['Jan 2026', 'Feb 2026', 'Mar 2026', 'Apr 2026', 'May 2026', 'Jun 2026',
                                  'Jul 2026', 'Aug 2026', 'Sep 2026', 'Oct 2026', 'Nov 2026', 'Dec 2026']
  const chartData = forecastResults?.monthly_data.map((item, idx) => {
    const dataPoint: any = {
      month: FORECAST_MONTH_LABELS[idx] || `M${item.month}`,
      Total: Math.round(item.total),
      Instagram: Math.round(item.Instagram),
      TikTok: Math.round(item.TikTok),
      YouTube: Math.round(item.YouTube),
      Facebook: Math.round(item.Facebook)
    }

    if (bandHigh && bandHigh[idx] !== undefined) dataPoint.BandHigh = Math.round(bandHigh[idx])
    if (bandLow && bandLow[idx] !== undefined) dataPoint.BandLow = Math.round(bandLow[idx])
    if (dataPoint.BandHigh !== undefined && dataPoint.BandLow !== undefined) {
      dataPoint.BandDelta = dataPoint.BandHigh - dataPoint.BandLow
    }

    // Add visible scenario lines
    scenarios.forEach(scenario => {
      if (scenario.visible && scenario.forecast) {
        dataPoint[scenario.name] = Math.round(scenario.forecast.monthly_data[idx]?.total || 0)
      }
    })

    return dataPoint
  }) || []

  // Keep selected month in range when results change (default to latest)
  useEffect(() => {
    const list = forecastResults?.added_breakdown || []
    if (list.length > 0) {
      setSelectedBreakdownIndex(Math.max(0, Math.min(list.length - 1, selectedBreakdownIndex)))
    }
  }, [forecastResults?.added_breakdown])

  // Breakdown (selected month)
  const breakdownList = forecastResults?.added_breakdown || []
  const selectedBreakdown = breakdownList[selectedBreakdownIndex]
  const lastPaid = selectedBreakdown ? selectedBreakdown.paid_added : 0
  const lastOrg = selectedBreakdown ? selectedBreakdown.organic_added : 0
  const lastTotalAdded = selectedBreakdown ? selectedBreakdown.total_added : 0
  const paidPct = lastTotalAdded > 0 ? (lastPaid / lastTotalAdded) * 100 : 0
  const orgPct = lastTotalAdded > 0 ? (lastOrg / lastTotalAdded) * 100 : 0

  const riskLevel = postsPerWeek > 35 ? 'HIGH' : postsPerWeek > 28 ? 'MEDIUM' : 'LOW'
  const riskColor = riskLevel === 'HIGH' ? 'var(--bittersweet)' : riskLevel === 'MEDIUM' ? 'var(--texas-rose)' : 'var(--fountain-blue)'

  // Delta indicators: compare key metrics to previous values and show temporary delta pills
  const [delta, setDelta] = useState<{ projected?: number; cpf?: number; spend?: number } | null>(null)
  const [deltaKind, setDeltaKind] = useState<{ projected?: string; cpf?: string; spend?: string }>({})
  useEffect(() => {
    const win:any = window as any
    const prev = win._prevForecast || { projected: 0, cpf: 0, spend: 0 }
    const projected = projectedTotal
    const cpf = blendedCPF
    const spend = totalSpend
    const pct = (a:number,b:number)=> b>0? ((a-b)/b)*100 : 0
    const projDeltaPct = pct(projected, prev.projected)
    const cpfDeltaPct = pct(cpf, prev.cpf)
    const spendDeltaPct = pct(spend, prev.spend)
    const meaningful = (v:number)=> Math.abs(v) > 0.5
    const nextDelta:any = {}
    const nextKind:any = {}
    if (meaningful(projDeltaPct)) { nextDelta.projected = projected - prev.projected; nextKind.projected = projDeltaPct>0? 'positive':'negative' }
    if (meaningful(cpfDeltaPct)) { nextDelta.cpf = cpf - prev.cpf; nextKind.cpf = cpfDeltaPct<0? 'positive':'negative' }
    if (meaningful(spendDeltaPct)) { nextDelta.spend = spend - prev.spend; nextKind.spend = spendDeltaPct<0? 'positive':'negative' }
    if (Object.keys(nextDelta).length>0) {
      setDelta(nextDelta); setDeltaKind(nextKind)
      const t = setTimeout(()=> setDelta(null), 3500)
      return () => clearTimeout(t)
    }
    win._prevForecast = { projected, cpf, spend }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectedTotal, blendedCPF, totalSpend])

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
          {delta?.projected !== undefined && (
            <div className={`delta-pill ${deltaKind.projected}`}>{delta.projected>0?'+':''}{(delta.projected/1000).toFixed(0)}k</div>
          )}
          <div className="progress-badge" style={{
            background: progressPercent >= 95 ? 'var(--fountain-blue)' : progressPercent >= 80 ? 'var(--texas-rose)' : 'var(--bittersweet)'
          }}>
            {progressPercent.toFixed(0)}%
          </div>
        </div>
        <div className="kpi-separator"></div>
        <div className="kpi-section">
          <div className="kpi-label">EST. ROI</div>
          <div className="kpi-value">{estROI !== null ? `${estROI.toFixed(0)}%` : '—'}</div>
          {delta?.cpf !== undefined && (
            <div className={`delta-pill ${deltaKind.cpf}`}>{delta.cpf>0?'+':'-'}${Math.abs(delta.cpf).toFixed(2)}</div>
          )}
        </div>
        <div className="kpi-section">
          <div className="kpi-label">TOTAL SPEND</div>
          <div className="kpi-value">{(monthlySpend/1000).toFixed(1)}k / {annualDisplay}</div>
          {delta?.spend !== undefined && (
            <div className={`delta-pill ${deltaKind.spend}`}>{delta.spend>0?'+':'-'}${(Math.abs(delta.spend)/1000).toFixed(1)}k</div>
          )}
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="dashboard-grid">
        {/* Left Panel: Controls */}
        <div className="control-panel">
          <div className={`panel-section ${sidebarCollapsed.strategy ? 'is-collapsed' : ''}`}>
            <div className="section-header clickable" onClick={() => toggleSidebarSection('strategy')}>
              <div className="section-title-group">
                <span className={`collapse-icon ${sidebarCollapsed.strategy ? 'collapsed' : ''}`}>{sidebarCollapsed.strategy ? '+' : '−'}</span>
                Controls
              </div>
              {sidebarCollapsed.strategy ? (
                <div className="collapsed-summary">{postsPerWeek} posts/wk • {months}mo</div>
              ) : (
                <HelpTooltip text="Adjust posting frequency, timeline, and strategy approach to test different growth scenarios" />
              )}
            </div>
            <div className={`section-content ${sidebarCollapsed.strategy ? 'collapsed' : ''}`}>
              <div className="section-content-inner">
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
                  <label>
                    Strategy Preset
                    <HelpTooltip text="Conservative: Safe approach with lower growth (60% acquisition rate, no campaign boost). Balanced: Standard growth with moderate risk (100% acquisition, 15% campaign lift). Ambitious: Aggressive growth strategy (150% acquisition, 35% campaign lift, higher engagement sensitivity)." />
                  </label>
                  <select value={preset} onChange={e => setPreset(e.target.value)} className="preset-select">
                    <option>Conservative</option>
                    <option>Balanced</option>
                    <option>Ambitious</option>
                  </select>
                </div>
              </div>
            </div>
          </div>

          {/* Assumptions moved to Advanced at bottom */}
          {/* Repositioned: Paid Media and Budget panels after Content Mix */}
          <div className={`panel-section ${sidebarCollapsed.paidMedia ? 'is-collapsed' : ''}`}>
            <div className="section-header clickable" onClick={() => toggleSidebarSection('paidMedia')}>
              <div className="section-title-group">
                <span className={`collapse-icon ${sidebarCollapsed.paidMedia ? 'collapsed' : ''}`}>{sidebarCollapsed.paidMedia ? '+' : '−'}</span>
                Paid Media
              </div>
              {sidebarCollapsed.paidMedia ? (
                <div className="collapsed-summary">{enablePaid ? `$${paidFunnelBudgetWeek}/wk` : 'Off'}</div>
              ) : (
                <HelpTooltip text="Optional: Include paid impressions per week and how they are allocated by platform. Uses industry conversion defaults (imp → views → engagements → follows)." />
              )}
            </div>
            <div className={`section-content ${sidebarCollapsed.paidMedia ? 'collapsed' : ''}`}>
              <div className="section-content-inner">
                <div className="control-group" style={{display:'flex', alignItems:'center', justifyContent:'space-between'}}>
                  <label>Enable Paid Media</label>
                  <input type="checkbox" checked={enablePaid} onChange={e=>setEnablePaid(e.target.checked)} />
                </div>
                {enablePaid && (
                  <>
                    <div className="control-group">
                      <label>Paid Funnel Budget / Week (USD)</label>
                      <input type="number" min={0} step={100} value={paidFunnelBudgetWeek} onChange={e=>setPaidFunnelBudgetWeek(parseInt(e.target.value)||0)} className="follower-input" />
                    </div>
                    <div className="control-group">
                      <label>CPM (Cost Per Mille)</label>
                      <input type="number" min={1} step={0.5} value={paidCPM} onChange={e=>setPaidCPM(parseFloat(e.target.value)||0)} className="follower-input" />
                      <div className="ai-note">Cost per 1,000 ad impressions. ${paidFunnelBudgetWeek} ÷ ${paidCPM} CPM = {((paidFunnelBudgetWeek / paidCPM) * 1000 / 1000).toFixed(0)}K impressions/week</div>
                    </div>
                    <div className="control-group">
                      <label>Paid Allocation (must total 100%)</label>
                      {Object.keys(paidAllocation).map(platform => (
                        <div key={platform} className="platform-control">
                          <div className="platform-header">
                            <span className="platform-name">{platform}</span>
                            <span className="platform-percent">{paidAllocation[platform as keyof typeof paidAllocation]}%</span>
                          </div>
                          <input
                            type="range"
                            min="0"
                            max="100"
                            value={paidAllocation[platform as keyof typeof paidAllocation]}
                            onChange={e => {
                              const val = parseInt(e.target.value)
                              setPaidAllocation(prev => ({...prev, [platform]: val}))
                            }}
                            className="slider platform-slider"
                          />
                        </div>
                      ))}
                      <div className="ai-note">Tip: Defaults mirror your organic platform allocation. Impressions are derived from CPM × Budget.</div>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>

          <div className={`panel-section ${sidebarCollapsed.budget ? 'is-collapsed' : ''}`}>
            <div className="section-header clickable" onClick={() => toggleSidebarSection('budget')}>
              <div className="section-title-group">
                <span className={`collapse-icon ${sidebarCollapsed.budget ? 'collapsed' : ''}`}>{sidebarCollapsed.budget ? '+' : '−'}</span>
                Growth Strategy
              </div>
              {sidebarCollapsed.budget ? (
                <div className="collapsed-summary">{enableBudget ? `$${paidBudgetWeek + creatorBudgetWeek + acquisitionBudgetWeek}/wk` : 'Off'}</div>
              ) : (
                <HelpTooltip text="Budget-based predictive modeling using cost-per-follower (CPF) ranges. Defaults to $3–$5 across paid, creator, acquisition." />
              )}
            </div>
            <div className={`section-content ${sidebarCollapsed.budget ? 'collapsed' : ''}`}>
              <div className="section-content-inner">
                <div className="control-group" style={{display:'flex', alignItems:'center', justifyContent:'space-between'}}>
                  <label>Enable Budget Model</label>
                  <input type="checkbox" checked={enableBudget} onChange={e=>setEnableBudget(e.target.checked)} />
                </div>
                {enableBudget && (
                  <>
                    <div className="control-group">
                      <label>Paid Boosting Budget / Week (USD)</label>
                      <input type="number" min={0} step={100} value={paidBudgetWeek} onChange={e=>setPaidBudgetWeek(parseInt(e.target.value)||0)} className="follower-input" />
                    </div>
                    <div className="control-group">
                      <label>Creator Budget / Week (USD)</label>
                      <input type="number" min={0} step={100} value={creatorBudgetWeek} onChange={e=>setCreatorBudgetWeek(parseInt(e.target.value)||0)} className="follower-input" />
                    </div>
                    <div className="control-group">
                      <label>Acquisition Budget / Week (USD)</label>
                      <input type="number" min={0} step={100} value={acquisitionBudgetWeek} onChange={e=>setAcquisitionBudgetWeek(parseInt(e.target.value)||0)} className="follower-input" />
                    </div>
                    <div className="control-group">
                      <label>Cost per Follower (range)</label>
                      <div className="cpf-grid" style={{marginBottom:'6px', opacity:0.8, fontSize:'0.75rem', color:'var(--text-secondary)'}}>
                        <div style={{textAlign:'center'}}>Min</div>
                        <div style={{textAlign:'center'}}>Mid (used)</div>
                        <div style={{textAlign:'center'}}>Max</div>
                      </div>
                      <div className="cpf-grid">
                        <div className="input-prefix-group"><span className="prefix">$</span><input type="number" step={0.1} value={cpfMin} onChange={e=>setCpfMin(parseFloat(e.target.value)||0)} className="follower-input cpf-input" placeholder="Min" /></div>
                        <div className="input-prefix-group"><span className="prefix">$</span><input type="number" step={0.1} value={cpfMid} onChange={e=>setCpfMid(parseFloat(e.target.value)||0)} className="follower-input cpf-input" placeholder="Mid" /></div>
                        <div className="input-prefix-group"><span className="prefix">$</span><input type="number" step={0.1} value={cpfMax} onChange={e=>setCpfMax(parseFloat(e.target.value)||0)} className="follower-input cpf-input" placeholder="Max" /></div>
                      </div>
                      <div className="ai-note">Use ranges to frame outcomes rather than a single point prediction.</div>
                    </div>
                    <div className="control-group">
                      <label>Value per New Follower (USD)</label>
                      <div className="input-prefix-group">
                        <span className="prefix">$</span>
                        <input type="number" min={0} step={0.1} value={valuePerFollower} onChange={e=>setValuePerFollower(parseFloat(e.target.value)||0)} className="follower-input cpf-input" placeholder="per follower" />
                      </div>
                      <div className="ai-note">Used to estimate ROI at the top level.</div>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
          {/* Paid Media panel moved below Content Mix for a more natural workflow */}

          {/* Growth Strategy & Metrics panel moved below Content Mix */}

          <div className={`panel-section ${sidebarCollapsed.followers ? 'is-collapsed' : ''}`}>
            <div className="section-header clickable" onClick={() => toggleSidebarSection('followers')}>
              <div className="section-title-group">
                <span className={`collapse-icon ${sidebarCollapsed.followers ? 'collapsed' : ''}`}>{sidebarCollapsed.followers ? '+' : '−'}</span>
                Current Followers
              </div>
              {sidebarCollapsed.followers ? (
                <div className="collapsed-summary">{(totalFollowers/1000000).toFixed(1)}M</div>
              ) : (
                <HelpTooltip text="Enter the current follower count for each platform. These are your starting numbers for the forecast." />
              )}
            </div>
            <div className={`section-content ${sidebarCollapsed.followers ? 'collapsed' : ''}`}>
              <div className="section-content-inner">
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
            </div>
          </div>

          <div className={`panel-section ${sidebarCollapsed.platform ? 'is-collapsed' : ''}`}>
            <div className="section-header clickable" onClick={() => toggleSidebarSection('platform')}>
              <div className="section-title-group">
                <span className={`collapse-icon ${sidebarCollapsed.platform ? 'collapsed' : ''}`}>{sidebarCollapsed.platform ? '+' : '−'}</span>
                Platform Allocation
              </div>
              {sidebarCollapsed.platform ? (
                <div className="collapsed-summary">{Object.entries(platformAllocation).map(([p,v]) => `${p.slice(0,2)}:${v}%`).join(' ')}</div>
              ) : (
                <HelpTooltip text="Set what percentage of your total weekly posts go to each platform. Must total 100%." />
              )}
            </div>
            <div className={`section-content ${sidebarCollapsed.platform ? 'collapsed' : ''}`}>
              <div className="section-content-inner">
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
            </div>
          </div>

          <div className={`panel-section ${sidebarCollapsed.contentMix ? 'is-collapsed' : ''}`}>
            <div className="section-header clickable" onClick={() => toggleSidebarSection('contentMix')}>
              <div className="section-title-group">
                <span className={`collapse-icon ${sidebarCollapsed.contentMix ? 'collapsed' : ''}`}>{sidebarCollapsed.contentMix ? '+' : '−'}</span>
                Content Mix
              </div>
              {sidebarCollapsed.contentMix ? (
                <div className="collapsed-summary">4 platforms</div>
              ) : (
                <HelpTooltip text="Define the content type distribution for each platform. Click platform names to expand." />
              )}
            </div>
            <div className={`section-content ${sidebarCollapsed.contentMix ? 'collapsed' : ''}`}>
              <div className="section-content-inner">
                {Object.keys(contentMix).map(platform => (
                  <div key={platform} className="content-mix-section">
                    <button
                      className="content-mix-header"
                      onClick={(e) => { e.stopPropagation(); setExpandedContentMix(expandedContentMix === platform ? null : platform) }}
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
            </div>
          </div>

          <div className={`panel-section ai-section ${sidebarCollapsed.aiInsights ? 'is-collapsed' : ''}`}>
            <div className="section-header clickable" onClick={() => toggleSidebarSection('aiInsights')}>
              <div className="section-title-group">
                <span className={`collapse-icon ${sidebarCollapsed.aiInsights ? 'collapsed' : ''}`}>{sidebarCollapsed.aiInsights ? '+' : '−'}</span>
                AI Advisor
              </div>
              {sidebarCollapsed.aiInsights ? (
                <div className="collapsed-summary">{aiInsights ? 'Ready' : 'Click to analyze'}</div>
              ) : (
                <HelpTooltip text="AI analyzes your complete configuration to recommend strategies for doubling followers within 12 months on a $100K budget" />
              )}
            </div>
            <div className={`section-content ${sidebarCollapsed.aiInsights ? 'collapsed' : ''}`}>
              <div className="section-content-inner">
                {aiLoading ? (
                  <div className="ai-loading-container">
                    <div className="ai-spinner" />
                    <div className="ai-loading-text">Analyzing your strategy...</div>
                    <div className="ai-loading-text" style={{fontSize:'0.75rem', opacity:0.7}}>Reviewing budgets, allocations, and growth targets</div>
                  </div>
                ) : aiInsights ? (
                  <>
                    <div className="ai-results">
                      <div className="ai-analysis">{aiInsights.analysis}</div>
                      <div className="ai-insights-list">
                        {aiInsights.key_insights.map((insight, idx) => (
                          <div key={idx} className="insight-item">{insight}</div>
                        ))}
                      </div>
                    </div>
                    <div className="insight-card">
                      <div className="insight-label">Oversaturation Risk</div>
                      <div className="insight-value" style={{color: riskColor}}>
                        {riskLevel}
                      </div>
                    </div>
                    <button
                      onClick={getAIRecommendations}
                      className="ai-button"
                      style={{marginTop:'0.5rem'}}
                    >
                      Re-analyze Strategy
                    </button>
                  </>
                ) : (
                  <div className="ai-loading-container" style={{padding:'1.5rem'}}>
                    <div className="ai-loading-text">Click to analyze your configuration</div>
                    <button
                      onClick={getAIRecommendations}
                      className="ai-button"
                    >
                      Analyze Strategy
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Advanced — Assumptions & Tuning at bottom */}
          <div className={`panel-section ${sidebarCollapsed.advanced ? 'is-collapsed' : ''}`}>
            <div className="section-header clickable" onClick={() => toggleSidebarSection('advanced')}>
              <div className="section-title-group">
                <span className={`collapse-icon ${sidebarCollapsed.advanced ? 'collapsed' : ''}`}>{sidebarCollapsed.advanced ? '+' : '−'}</span>
                Advanced
              </div>
              {!sidebarCollapsed.advanced && (
                <HelpTooltip text="Inspect and tweak the model's underlying assumptions. Collapsed to keep focus on the planning flow." />
              )}
            </div>
            <div className={`section-content ${sidebarCollapsed.advanced ? 'collapsed' : ''}`}>
              <div className="section-content-inner">
                <Assumptions />
                <div style={{marginTop:'0.75rem', display:'flex', gap:'8px'}}>
                  <button className="ai-button" onClick={() => setShowTune(true)}>
                    AI Parameter Suggestions (beta)
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Panel: Visualizations */}
        <div className="viz-panel">
          {/* At-a-glance KPIs */}
          <div className="metrics-row" style={{gridTemplateColumns:'repeat(3, 1fr)'}}>
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
            
          </div>

          {/* Historical context first */}
          {historicalData && (
            <div className={`historical-section ${historicalCollapsed ? 'collapsed' : ''}`}>
              <div className="section-header" style={{marginBottom: historicalCollapsed ? 0 : '0.75rem', display:'flex', alignItems:'center', justifyContent:'space-between'}}>
                <div>
                  Historical Context (2025)
                  <HelpTooltip text="Past performance data showing engagement trends, sentiment analysis, and popular tags over time" />
                </div>
                <button className="chart-mode-btn" onClick={()=> setHistoricalCollapsed(v=>!v)}>
                  {historicalCollapsed ? '▸ Expand' : '▾ Minimize'}
                </button>
              </div>

              {!historicalCollapsed && (
              <>
              <div className="historical-tabs">
                <button
                  className={`historical-tab ${historicalTab === 'mentions' ? 'active' : ''}`}
                  onClick={() => setHistoricalTab('mentions')}
                >
                  Mentions
                </button>
                <button
                  className={`historical-tab ${historicalTab === 'sentiment' ? 'active' : ''}`}
                  onClick={() => setHistoricalTab('sentiment')}
                >
                  Sentiment
                </button>
                <button
                  className={`historical-tab ${historicalTab === 'tags' ? 'active' : ''}`}
                  onClick={() => setHistoricalTab('tags')}
                >
                  Tags
                </button>
                <button
                  className={`historical-tab ${historicalTab === 'growth' ? 'active' : ''}`}
                  onClick={() => setHistoricalTab('growth')}
                >
                  Growth
                </button>
              </div>

              <div className="historical-chart-container">
                {historicalTab === 'mentions' && (
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={historicalData.mentions}>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                      <XAxis dataKey="Time" stroke="var(--text-secondary)" />
                      <YAxis stroke="var(--text-secondary)" />
                      <Tooltip
                        contentStyle={{background: 'var(--bg-primary)', border: '1px solid var(--border)', borderRadius: '8px'}}
                      />
                      <Legend />
                      <Line type="monotone" dataKey="Mentions" stroke={SERIES_COLORS.mentions} strokeWidth={2.5} />
                    </LineChart>
                  </ResponsiveContainer>
                )}

                {historicalTab === 'sentiment' && (
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={historicalData.sentiment}>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                      <XAxis dataKey="Time" stroke="var(--text-secondary)" />
                      <YAxis stroke="var(--text-secondary)" />
                      <Tooltip
                        contentStyle={{background: 'var(--bg-primary)', border: '1px solid var(--border)', borderRadius: '8px'}}
                      />
                      <Legend />
                      <Line type="monotone" dataKey="Positive" stroke={SERIES_COLORS.sentimentPos} strokeWidth={2.5} />
                      <Line type="monotone" dataKey="Neutral" stroke={SERIES_COLORS.sentimentNeu} strokeWidth={2.5} />
                      <Line type="monotone" dataKey="Negative" stroke={SERIES_COLORS.sentimentNeg} strokeWidth={2.5} />
                    </LineChart>
                  </ResponsiveContainer>
                )}

                {historicalTab === 'tags' && (
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={historicalData.tags}>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                      <XAxis dataKey="Time" stroke="var(--text-secondary)" />
                      <YAxis stroke="var(--text-secondary)" />
                      <Tooltip
                        contentStyle={{background: 'var(--bg-primary)', border: '1px solid var(--border)', borderRadius: '8px'}}
                      />
                      <Legend />
                      <Line type="monotone" dataKey="Official Care Bears" stroke={SERIES_COLORS.tag1} strokeWidth={2.5} name="Official Care Bears" />
                      <Line type="monotone" dataKey="Stranger Things" stroke={SERIES_COLORS.tag2} strokeWidth={2.5} name="Stranger Things" />
                      <Line type="monotone" dataKey="Wicked" stroke={SERIES_COLORS.tag3} strokeWidth={2.5} name="Wicked" />
                    </LineChart>
                  </ResponsiveContainer>
                )}

                {historicalTab === 'growth' && followerHistory && (
                  <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={(function() {
                      // Transform data to split solid vs dashed based on interpolation flags
                      return followerHistory.map((row: any) => {
                        const point: any = { label: row.label }
                        const platforms = ['Total', 'Instagram', 'TikTok', 'YouTube', 'Facebook']
                        platforms.forEach(p => {
                          if (row[p] !== undefined) {
                            if (row[`${p}_interpolated`]) {
                              point[`${p}_dashed`] = row[p]
                            } else {
                              point[`${p}_solid`] = row[p]
                            }
                            // Also keep combined for connecting line
                            point[p] = row[p]
                          }
                        })
                        return point
                      })
                    })()} margin={{ top: 5, right: 50, left: 0, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                      <XAxis dataKey="label" stroke="var(--text-secondary)" tick={{fontSize: 10}} interval={0} angle={-45} textAnchor="end" height={50} />
                      <YAxis stroke="var(--text-secondary)" tick={{fontSize: 10}} tickFormatter={(value) => `${(value / 1000000).toFixed(1)}M`} width={45} />
                      <Tooltip
                        contentStyle={{background: 'var(--bg-primary)', border: '1px solid var(--border)', borderRadius: '8px'}}
                        formatter={(value: number, name: string) => {
                          // Only show _solid and _dashed entries, skip the combined values
                          if (!name.includes('_solid') && !name.includes('_dashed')) return null
                          const cleanName = name.replace('_solid', '').replace('_dashed', ' (est.)')
                          return [(value / 1000).toFixed(0) + 'K', cleanName]
                        }}
                      />
                      <Legend formatter={(value: string) => value.replace('_solid', '').replace('_dashed', '')} />
                      {/* Dashed lines for interpolated data (behind) */}
                      <Line type="monotone" dataKey="Total_dashed" stroke={SERIES_COLORS.total} strokeWidth={3} dot={false} strokeDasharray="6 4" connectNulls={false} legendType="none" />
                      <Line type="monotone" dataKey="Instagram_dashed" stroke={SERIES_COLORS.instagram} strokeWidth={2} dot={false} strokeDasharray="6 4" connectNulls={false} legendType="none" />
                      <Line type="monotone" dataKey="TikTok_dashed" stroke={SERIES_COLORS.tiktok} strokeWidth={2} dot={false} strokeDasharray="6 4" connectNulls={false} legendType="none" />
                      <Line type="monotone" dataKey="YouTube_dashed" stroke={SERIES_COLORS.youtube} strokeWidth={2} dot={false} strokeDasharray="6 4" connectNulls={false} legendType="none" />
                      <Line type="monotone" dataKey="Facebook_dashed" stroke={SERIES_COLORS.facebook} strokeWidth={2} dot={false} strokeDasharray="6 4" connectNulls={false} legendType="none" />
                      {/* Solid lines for real data (on top) */}
                      <Line type="monotone" dataKey="Total_solid" stroke={SERIES_COLORS.total} strokeWidth={3} dot={false} connectNulls={false} name="Total">
                        <LabelList dataKey="Total" content={({x, y, index}: any) => index === (followerHistory?.length || 0) - 1 ? <text x={x + 5} y={y - 8} fill={SERIES_COLORS.total} fontSize={9} fontWeight={600}>Total</text> : null} />
                      </Line>
                      <Line type="monotone" dataKey="Instagram_solid" stroke={SERIES_COLORS.instagram} strokeWidth={2} dot={false} connectNulls={false} name="Instagram">
                        <LabelList dataKey="Instagram" content={({x, y, index}: any) => index === (followerHistory?.length || 0) - 1 ? <text x={x + 5} y={y + 3} fill={SERIES_COLORS.instagram} fontSize={9} fontWeight={600}>IG</text> : null} />
                      </Line>
                      <Line type="monotone" dataKey="TikTok_solid" stroke={SERIES_COLORS.tiktok} strokeWidth={2} dot={false} connectNulls={false} name="TikTok">
                        <LabelList dataKey="TikTok" content={({x, y, index}: any) => index === (followerHistory?.length || 0) - 1 ? <text x={x + 5} y={y - 5} fill={SERIES_COLORS.tiktok} fontSize={9} fontWeight={600}>TT</text> : null} />
                      </Line>
                      <Line type="monotone" dataKey="YouTube_solid" stroke={SERIES_COLORS.youtube} strokeWidth={2} dot={false} connectNulls={false} name="YouTube">
                        <LabelList dataKey="YouTube" content={({x, y, index}: any) => index === (followerHistory?.length || 0) - 1 ? <text x={x + 5} y={y + 8} fill={SERIES_COLORS.youtube} fontSize={9} fontWeight={600}>YT</text> : null} />
                      </Line>
                      <Line type="monotone" dataKey="Facebook_solid" stroke={SERIES_COLORS.facebook} strokeWidth={2} dot={false} connectNulls={false} name="Facebook">
                        <LabelList dataKey="Facebook" content={({x, y, index}: any) => index === (followerHistory?.length || 0) - 1 ? <text x={x + 5} y={y + 12} fill={SERIES_COLORS.facebook} fontSize={9} fontWeight={600}>FB</text> : null} />
                      </Line>
                    </LineChart>
                  </ResponsiveContainer>
                )}
                {historicalTab === 'growth' && !followerHistory && (
                  <div style={{padding:'2rem', textAlign:'center', color:'var(--text-secondary)'}}>
                    No historical follower data available
                  </div>
                )}
              </div>
              </>
              )}
            </div>
          )}
          <div className="chart-container main-chart">
              <div className="chart-header" style={{flexWrap:'wrap', gap:'8px'}}>
                <h2 style={{marginRight:'auto'}}>Followers — {chartMode === 'historical' ? 'Historical (2025)' : chartMode === 'forecast' ? 'Forecast (2026)' : 'Historical (2025) & Forecast (2026)'}</h2>
                {loading && <span className="loading-indicator">Calculating...</span>}
                <div style={{display:'flex', gap:'4px', flexWrap:'wrap', alignItems:'center', flex:1, justifyContent:'flex-end'}}>
                  <button className={`chart-mode-btn ${chartMode==='historical'?'active':''}`} onClick={()=> setChartMode('historical')}>Hist</button>
                  <button className={`chart-mode-btn ${chartMode==='forecast'?'active':''}`} onClick={()=> setChartMode('forecast')}>Fcst</button>
                  <button className={`chart-mode-btn ${chartMode==='both'?'active':''}`} onClick={()=> setChartMode('both')}>Both</button>
                  <div style={{display:'flex', gap:'6px', marginLeft:'8px'}}>
                    {(['Total','Instagram','TikTok','YouTube','Facebook'] as const).map((p)=> (
                      <label key={p} style={{display:'flex', alignItems:'center', gap:'3px', color:'var(--text-secondary)', fontSize:'0.8rem', cursor:'pointer'}}>
                        <input type="checkbox" checked={showPlatforms[p]} onChange={e=> setShowPlatforms(prev=> ({...prev, [p]: e.target.checked}))} /> {p}
                      </label>
                    ))}
                  </div>
                  {/* AI Scenario toggles - only show when forecast/both is visible */}
                  {chartMode !== 'historical' && scenarios.length > 0 && (
                    <div style={{display:'flex', gap:'6px', marginLeft:'auto', paddingLeft:'12px', borderLeft:'1px solid var(--border)'}}>
                      {scenarios.map((scenario, idx) => (
                        <label key={idx} style={{display:'flex', alignItems:'center', gap:'3px', color: scenario.color, fontSize:'0.8rem', cursor:'pointer'}}>
                          <input
                            type="checkbox"
                            checked={scenario.visible}
                            onChange={() => toggleScenario(idx)}
                          />
                          {scenario.name}
                        </label>
                      ))}
                    </div>
                  )}
                </div>
              </div>

            <ResponsiveContainer width="100%" height={400}>
              <ComposedChart data={(function(){
                // Build historical data points with _hist suffix
                // Split into solid (real) and dashed (interpolated) values
                const hist = (followerHistory||[]).map((row:any, idx:number)=> {
                  const point: any = {
                    month: row.label || `H${idx+1}`,
                  }
                  // For each platform, put value in solid or dashed key based on interpolation flag
                  const platforms = ['Total', 'Instagram', 'TikTok', 'YouTube', 'Facebook']
                  platforms.forEach(p => {
                    if (row[p] !== undefined) {
                      if (row[`${p}_interpolated`]) {
                        point[`${p}_hist_dashed`] = row[p]
                      } else {
                        point[`${p}_hist`] = row[p]
                      }
                      // Also store the full value for connecting lines
                      point[`${p}_hist_all`] = row[p]
                    }
                  })
                  return point
                })

                // Build forecast data points
                const fc = (chartData||[]).map((row:any)=> ({
                  month: row.month,
                  Total: row.Total,
                  Instagram: row.Instagram,
                  TikTok: row.TikTok,
                  YouTube: row.YouTube,
                  Facebook: row.Facebook,
                  Total_forecast: row.Total,
                  Instagram_forecast: row.Instagram,
                  TikTok_forecast: row.TikTok,
                  YouTube_forecast: row.YouTube,
                  Facebook_forecast: row.Facebook,
                  BandHigh: row.BandHigh,
                  BandLow: row.BandLow,
                  BandDelta: row.BandDelta,
                }))

                if (chartMode==='forecast') return fc
                if (chartMode==='historical') return hist
                // 'both' mode: concatenate historical then forecast
                // Add forecast values to last historical point to create bridge
                if (hist.length > 0 && fc.length > 0) {
                  const lastHist = hist[hist.length - 1]
                  const firstFc = fc[0]
                  // Copy forecast keys to last historical point to connect the lines
                  lastHist.Total_forecast = lastHist.Total_hist_all || lastHist.Total_hist
                  lastHist.Instagram_forecast = lastHist.Instagram_hist_all || lastHist.Instagram_hist
                  lastHist.TikTok_forecast = lastHist.TikTok_hist_all || lastHist.TikTok_hist
                  lastHist.YouTube_forecast = lastHist.YouTube_hist_all || lastHist.YouTube_hist
                  lastHist.Facebook_forecast = lastHist.Facebook_hist_all || lastHist.Facebook_hist
                }
                return [...hist, ...fc]
              })()} margin={{ top: 5, right: 50, left: 0, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="month" stroke="var(--text-secondary)" tick={{fontSize: 10}} interval={0} angle={-45} textAnchor="end" height={50} />
                <YAxis stroke="var(--text-secondary)" tick={{fontSize: 10}} tickFormatter={(value) => `${(value / 1000000).toFixed(1)}M`} width={45} />
                <Tooltip
                  contentStyle={{background: 'var(--bg-primary)', border: '1px solid var(--border)', borderRadius: '8px'}}
                  formatter={(value: number, name: string) => {
                    // Clean up the dataKey name for display
                    let displayName = name
                      .replace('_hist_all', ' (est.)')
                      .replace('_hist', '')
                      .replace('_forecast', ' (forecast)')
                      .replace('Total', 'Total')
                    return [(value / 1000).toFixed(0) + 'K', displayName]
                  }}
                />
                <ReferenceLine
                  y={goalFollowers}
                  stroke="var(--fountain-blue)"
                  strokeDasharray="5 5"
                  label={{ value: 'Goal', position: 'right', fill: 'var(--fountain-blue)' }}
                />
                {chartMode==='forecast' && enableBudget && bandHigh && bandLow && (
                  <>
                    <Area type="monotone" dataKey="BandLow" stackId="band" stroke="none" fill="transparent" />
                    <Area type="monotone" dataKey="BandDelta" stackId="band" stroke="none" fill={SERIES_COLORS.bandFill} />
                    <Line type="monotone" dataKey="BandHigh" stroke={SERIES_COLORS.bandEdge} strokeWidth={1.5} dot={false} strokeDasharray="6 6" name="Optimistic (CPF min)" />
                    <Line type="monotone" dataKey="BandLow" stroke={SERIES_COLORS.bandEdge} strokeWidth={1.5} dot={false} strokeDasharray="6 6" name="Pessimistic (CPF max)" />
                  </>
                )}
                {chartMode==='forecast' && (
                  <>
                    {showPlatforms.Total && (<Line type="monotone" dataKey="Total" stroke={SERIES_COLORS.total} strokeWidth={4} dot={false} name="Total (Manual)">
                      <LabelList dataKey="Total" content={({x, y, index}: any) => index === (chartData?.length || 0) - 1 ? <text x={x + 5} y={y - 8} fill={SERIES_COLORS.total} fontSize={9} fontWeight={600}>Total</text> : null} />
                    </Line>)}
                    {showPlatforms.Instagram && (<Line type="monotone" dataKey="Instagram" stroke={SERIES_COLORS.instagram} strokeWidth={2.5} dot={false} strokeDasharray="4 2">
                      <LabelList dataKey="Instagram" content={({x, y, index}: any) => index === (chartData?.length || 0) - 1 ? <text x={x + 5} y={y + 3} fill={SERIES_COLORS.instagram} fontSize={9} fontWeight={600}>IG</text> : null} />
                    </Line>)}
                    {showPlatforms.TikTok && (<Line type="monotone" dataKey="TikTok" stroke={SERIES_COLORS.tiktok} strokeWidth={2.5} dot={false} strokeDasharray="3 3">
                      <LabelList dataKey="TikTok" content={({x, y, index}: any) => index === (chartData?.length || 0) - 1 ? <text x={x + 5} y={y - 5} fill={SERIES_COLORS.tiktok} fontSize={9} fontWeight={600}>TT</text> : null} />
                    </Line>)}
                    {showPlatforms.YouTube && (<Line type="monotone" dataKey="YouTube" stroke={SERIES_COLORS.youtube} strokeWidth={2.5} dot={false} strokeDasharray="6 3">
                      <LabelList dataKey="YouTube" content={({x, y, index}: any) => index === (chartData?.length || 0) - 1 ? <text x={x + 5} y={y + 8} fill={SERIES_COLORS.youtube} fontSize={9} fontWeight={600}>YT</text> : null} />
                    </Line>)}
                    {showPlatforms.Facebook && (<Line type="monotone" dataKey="Facebook" stroke={SERIES_COLORS.facebook} strokeWidth={2.5} dot={false} strokeDasharray="2 2">
                      <LabelList dataKey="Facebook" content={({x, y, index}: any) => index === (chartData?.length || 0) - 1 ? <text x={x + 5} y={y + 12} fill={SERIES_COLORS.facebook} fontSize={9} fontWeight={600}>FB</text> : null} />
                    </Line>)}
                  </>
                )}
                {chartMode!=='forecast' && (
                  <>
                    {/* Historical - dashed lines for interpolated data (rendered first, behind solid) */}
                    {/* Only show labels on historical lines when in 'historical' mode, not 'both' */}
                    {showPlatforms.Total && (<Line type="monotone" dataKey="Total_hist_all" stroke={SERIES_COLORS.total} strokeWidth={4} dot={false} strokeDasharray="4 4" strokeOpacity={0.5} name="Total (interpolated)" legendType="none">
                      {chartMode === 'historical' && <LabelList dataKey="Total_hist_all" content={({x, y, index}: any) => index === (followerHistory?.length || 0) - 1 ? <text x={x + 5} y={y - 8} fill={SERIES_COLORS.total} fontSize={9} fontWeight={600}>Total</text> : null} />}
                    </Line>)}
                    {showPlatforms.Instagram && (<Line type="monotone" dataKey="Instagram_hist_all" stroke={SERIES_COLORS.instagram} strokeWidth={2.5} dot={false} strokeDasharray="4 4" strokeOpacity={0.5} legendType="none">
                      {chartMode === 'historical' && <LabelList dataKey="Instagram_hist_all" content={({x, y, index}: any) => index === (followerHistory?.length || 0) - 1 ? <text x={x + 5} y={y + 3} fill={SERIES_COLORS.instagram} fontSize={9} fontWeight={600}>IG</text> : null} />}
                    </Line>)}
                    {showPlatforms.TikTok && (<Line type="monotone" dataKey="TikTok_hist_all" stroke={SERIES_COLORS.tiktok} strokeWidth={2.5} dot={false} strokeDasharray="4 4" strokeOpacity={0.5} legendType="none">
                      {chartMode === 'historical' && <LabelList dataKey="TikTok_hist_all" content={({x, y, index}: any) => index === (followerHistory?.length || 0) - 1 ? <text x={x + 5} y={y - 5} fill={SERIES_COLORS.tiktok} fontSize={9} fontWeight={600}>TT</text> : null} />}
                    </Line>)}
                    {showPlatforms.YouTube && (<Line type="monotone" dataKey="YouTube_hist_all" stroke={SERIES_COLORS.youtube} strokeWidth={2.5} dot={false} strokeDasharray="4 4" strokeOpacity={0.5} legendType="none">
                      {chartMode === 'historical' && <LabelList dataKey="YouTube_hist_all" content={({x, y, index}: any) => index === (followerHistory?.length || 0) - 1 ? <text x={x + 5} y={y + 8} fill={SERIES_COLORS.youtube} fontSize={9} fontWeight={600}>YT</text> : null} />}
                    </Line>)}
                    {showPlatforms.Facebook && (<Line type="monotone" dataKey="Facebook_hist_all" stroke={SERIES_COLORS.facebook} strokeWidth={2.5} dot={false} strokeDasharray="4 4" strokeOpacity={0.5} legendType="none">
                      {chartMode === 'historical' && <LabelList dataKey="Facebook_hist_all" content={({x, y, index}: any) => index === (followerHistory?.length || 0) - 1 ? <text x={x + 5} y={y + 12} fill={SERIES_COLORS.facebook} fontSize={9} fontWeight={600}>FB</text> : null} />}
                    </Line>)}
                    {/* Historical - solid lines for real data (rendered on top) */}
                    {showPlatforms.Total && (<Line type="monotone" dataKey="Total_hist" stroke={SERIES_COLORS.total} strokeWidth={4} dot={false} name="Total (hist)" connectNulls={false} />)}
                    {showPlatforms.Instagram && (<Line type="monotone" dataKey="Instagram_hist" stroke={SERIES_COLORS.instagram} strokeWidth={2.5} dot={false} name="Instagram" connectNulls={false} />)}
                    {showPlatforms.TikTok && (<Line type="monotone" dataKey="TikTok_hist" stroke={SERIES_COLORS.tiktok} strokeWidth={2.5} dot={false} name="TikTok" connectNulls={false} />)}
                    {showPlatforms.YouTube && (<Line type="monotone" dataKey="YouTube_hist" stroke={SERIES_COLORS.youtube} strokeWidth={2.5} dot={false} name="YouTube" connectNulls={false} />)}
                    {showPlatforms.Facebook && (<Line type="monotone" dataKey="Facebook_hist" stroke={SERIES_COLORS.facebook} strokeWidth={2.5} dot={false} name="Facebook" connectNulls={false} />)}
                  </>
                )}
                {chartMode==='both' && (
                  <>
                    {/* Forecast dashed continuation - labels shown at far right */}
                    {showPlatforms.Total && (<Line type="monotone" dataKey="Total_forecast" stroke={SERIES_COLORS.total} strokeWidth={4} dot={false} strokeDasharray="6 6" name="Total (forecast)">
                      <LabelList dataKey="Total_forecast" content={({x, y, index, payload}: any) => {
                        const combinedLen = (followerHistory?.length || 0) + (chartData?.length || 0)
                        return index === combinedLen - 1 ? <text x={x + 5} y={y - 8} fill={SERIES_COLORS.total} fontSize={9} fontWeight={600}>Total</text> : null
                      }} />
                    </Line>)}
                    {showPlatforms.Instagram && (<Line type="monotone" dataKey="Instagram_forecast" stroke={SERIES_COLORS.instagram} strokeWidth={2.5} dot={false} strokeDasharray="6 6">
                      <LabelList dataKey="Instagram_forecast" content={({x, y, index}: any) => {
                        const combinedLen = (followerHistory?.length || 0) + (chartData?.length || 0)
                        return index === combinedLen - 1 ? <text x={x + 5} y={y + 3} fill={SERIES_COLORS.instagram} fontSize={9} fontWeight={600}>IG</text> : null
                      }} />
                    </Line>)}
                    {showPlatforms.TikTok && (<Line type="monotone" dataKey="TikTok_forecast" stroke={SERIES_COLORS.tiktok} strokeWidth={2.5} dot={false} strokeDasharray="6 6">
                      <LabelList dataKey="TikTok_forecast" content={({x, y, index}: any) => {
                        const combinedLen = (followerHistory?.length || 0) + (chartData?.length || 0)
                        return index === combinedLen - 1 ? <text x={x + 5} y={y - 5} fill={SERIES_COLORS.tiktok} fontSize={9} fontWeight={600}>TT</text> : null
                      }} />
                    </Line>)}
                    {showPlatforms.YouTube && (<Line type="monotone" dataKey="YouTube_forecast" stroke={SERIES_COLORS.youtube} strokeWidth={2.5} dot={false} strokeDasharray="6 6">
                      <LabelList dataKey="YouTube_forecast" content={({x, y, index}: any) => {
                        const combinedLen = (followerHistory?.length || 0) + (chartData?.length || 0)
                        return index === combinedLen - 1 ? <text x={x + 5} y={y + 8} fill={SERIES_COLORS.youtube} fontSize={9} fontWeight={600}>YT</text> : null
                      }} />
                    </Line>)}
                    {showPlatforms.Facebook && (<Line type="monotone" dataKey="Facebook_forecast" stroke={SERIES_COLORS.facebook} strokeWidth={2.5} dot={false} strokeDasharray="6 6">
                      <LabelList dataKey="Facebook_forecast" content={({x, y, index}: any) => {
                        const combinedLen = (followerHistory?.length || 0) + (chartData?.length || 0)
                        return index === combinedLen - 1 ? <text x={x + 5} y={y + 12} fill={SERIES_COLORS.facebook} fontSize={9} fontWeight={600}>FB</text> : null
                      }} />
                    </Line>)}
                  </>
                )}
                {chartMode==='forecast' && scenarios.map((scenario, idx) =>
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
              </ComposedChart>
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

          {/* Acquisition Breakdown */}
          {forecastResults?.added_breakdown && (
            <div className="chart-container">
              <div className="chart-header">
                <h2 style={{margin:0}}>Acquisition Breakdown</h2>
              </div>
              <div style={{display:'flex', gap:'8px', overflowX:'auto', paddingBottom:'4px'}}>
                {forecastResults.added_breakdown.map((breakdown, idx) => {
                  const monthTotal = (breakdown.organic || 0) + (breakdown.paid || 0)
                  const monthPaidPct = monthTotal > 0 ? ((breakdown.paid || 0) / monthTotal) * 100 : 0
                  const monthOrgPct = 100 - monthPaidPct
                  return (
                    <div key={idx} style={{
                      flex: '1 1 0',
                      minWidth: '70px',
                      background: 'var(--bg-primary)',
                      borderRadius: '8px',
                      padding: '8px',
                      border: '1px solid var(--border)',
                      textAlign: 'center'
                    }}>
                      <div style={{fontSize:'0.7rem', fontWeight:700, color:'var(--text-secondary)', marginBottom:'4px'}}>M{idx+1}</div>
                      <div style={{fontSize:'0.9rem', fontWeight:800, color:'var(--fountain-blue)'}}>{(monthTotal/1000).toFixed(0)}K</div>
                      <div style={{height:'6px', background:'var(--bg-secondary)', borderRadius:'3px', overflow:'hidden', margin:'4px 0'}}>
                        <div style={{width:`${monthPaidPct}%`, height:'100%', background:'var(--primary)'}}></div>
                      </div>
                      <div style={{fontSize:'0.6rem', color:'var(--text-secondary)'}}>{monthPaidPct.toFixed(0)}% paid</div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}

          
          {/* Parameter Tuning Modal */}
          {showTune && (
            <div className="modal-backdrop" role="dialog" aria-modal="true">
              <div className="modal" style={{maxWidth:'760px'}}>
                <div className="modal-header">
                  <h2>AI Parameter Suggestions (beta)</h2>
                  <button className="modal-close" aria-label="Close" onClick={()=>setShowTune(false)}>×</button>
                </div>
                <div className="modal-body">
                  <p style={{marginTop:0, color:'var(--text-secondary)'}}>These are conservative, evidence-based tweaks to model assumptions. You control what to apply.</p>
                  <div style={{marginBottom:'0.75rem'}}>
                    <button
                      className="ai-button"
                      disabled={tuneLoading}
                      onClick={async ()=>{
                        setTuneLoading(true)
                        try {
                          const asmp = await api.getAssumptions()
                          const find = (label:string)=> (asmp.assumptions as any[]).find((x:any)=> x.label.includes(label))
                          const contentMult = find('Content multipliers')?.value || {}
                          const bands = find('Posting bands')?.value || {}
                          const ttAlloc = platformAllocation['TikTok'] || 0
                          const weightedSoft = Object.entries(bands||{}).reduce((acc:any,[p,v]:any)=> acc + (platformAllocation[p as keyof typeof platformAllocation]||0)*(v.soft||0)/100, 0)
                          const oversat_weeks = postsPerWeek > weightedSoft ? 6 : 0
                          const tt_strength = Math.min(1, Math.max(0, (ttAlloc-25)/15))
                          const resp = await api.tuneParameters({
                            current_params: { CONTENT_MULT: contentMult, RECOMMENDED_FREQ: bands },
                            historical_summary: { tt_strength, oversat_weeks },
                            gap_to_goal: goalFollowers>0? Math.max(0, 100 - (projectedTotal/goalFollowers)*100): 100,
                          })
                          setTuneSuggestions(resp.suggestions.map(s=> ({...s, accept:true})))
                        } catch(e) { /* ignore */ }
                        finally { setTuneLoading(false) }
                      }}
                    >{tuneLoading? 'Getting suggestions…' : 'Get Suggestions'}</button>
                  </div>
                  {tuneSuggestions.length>0 ? (
                    <div style={{overflowX:'auto'}}>
                      <table style={{width:'100%', borderCollapse:'collapse'}}>
                        <thead>
                          <tr style={{textAlign:'left', color:'var(--text-secondary)'}}>
                            <th style={{padding:'6px'}}>Apply</th>
                            <th style={{padding:'6px'}}>Parameter</th>
                            <th style={{padding:'6px'}}>Current</th>
                            <th style={{padding:'6px'}}>Suggested</th>
                            <th style={{padding:'6px'}}>Confidence</th>
                            <th style={{padding:'6px'}}>Reason</th>
                          </tr>
                        </thead>
                        <tbody>
                          {tuneSuggestions.map((s,i)=>(
                            <tr key={i} style={{borderTop:'1px solid var(--border)'}}>
                              <td style={{padding:'6px'}}><input type="checkbox" checked={s.accept!==false} onChange={e=>{
                                const v = e.target.checked; setTuneSuggestions(prev=> prev.map((x,idx)=> idx===i? {...x, accept:v}: x))
                              }} /></td>
                              <td style={{padding:'6px'}}><code>{s.key}</code></td>
                              <td style={{padding:'6px'}}>{s.current}</td>
                              <td style={{padding:'6px'}}>{s.suggested}</td>
                              <td style={{padding:'6px'}}>{s.confidence}</td>
                              <td style={{padding:'6px', color:'var(--text-secondary)'}}>{s.reason}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                      <div style={{display:'flex', gap:'8px', marginTop:'0.75rem'}}>
                        <button className="ai-button" onClick={()=> setShowTune(false)}>Dismiss</button>
                        <button className="ai-button" onClick={()=> alert('Preview only: model overrides not yet applied in forecast engine.')}>Apply suggestions</button>
                      </div>
                      <p className="ai-note">Note: Applying suggestions is a preview in this build. We can wire overrides into the forecast engine upon approval.</p>
                    </div>
                  ) : (
                    <p className="ai-note">Click “Get Suggestions” to retrieve conservative parameter tweaks based on current settings and benchmarks.</p>
                  )}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

function Assumptions() {
  const [items, setItems] = useState<{label:string, value:any, source:string}[]>([])
  useEffect(() => {
    api.getAssumptions().then(res => setItems(res.assumptions as any)).catch(()=>{})
  }, [])
  const renderItem = (a:any) => {
    const label = a.label as string
    const val = a.value
    if (label.includes('Content multipliers')) {
      const platforms = Object.keys(val||{})
      const cols = ['Short Video','Image','Carousel','Long Video','Story/Live']
      return (
        <div className="assump-item">
          <div className="assump-title">Content format multipliers</div>
          <table className="assump-table">
            <thead><tr><th>Platform</th>{cols.map(c=><th key={c}>{c}</th>)}</tr></thead>
            <tbody>
              {platforms.map(p=> (
                <tr key={p}><td>{p}</td>{cols.map(c=> <td key={c}>{(val[p]?.[c] ?? 1).toFixed(2)}×</td>)}</tr>
              ))}
            </tbody>
          </table>
          <div className="assump-source">Source: {a.source}</div>
        </div>
      )
    }
    if (label.includes('Posting bands')) {
      const rows = Object.entries(val||{}) as any[]
      return (
        <div className="assump-item">
          <div className="assump-title">Posting bands (per week)</div>
          <div className="assump-kv">
            {rows.map(([p,v])=> (
              <div key={p}><span className="assump-badge">{p}</span>min {v.min}, ideal ≤ {v.max}, soft {v.soft}, hard {v.hard}/wk</div>
            ))}
          </div>
          <div className="assump-source">Source: {a.source}</div>
        </div>
      )
    }
    if (label.includes('Frequency half-saturation')) {
      const rows = Object.entries(val||{}) as any[]
      return (
        <div className="assump-item">
          <div className="assump-title">Frequency half-saturation</div>
          <div className="assump-kv">
            {rows.map(([p,v])=> (
              <div key={p}><span className="assump-badge">{p}</span>{v}/wk</div>
            ))}
          </div>
          <div className="assump-source">Source: {a.source}</div>
        </div>
      )
    }
    if (label.includes('Monthly growth caps')) {
      const rows = Object.entries(val||{}) as any[]
      return (
        <div className="assump-item">
          <div className="assump-title">Monthly growth caps</div>
          <div className="assump-kv">
            {rows.map(([p,v])=> (
              <div key={p}><span className="assump-badge">{p}</span>{(v*100).toFixed(0)}%</div>
            ))}
          </div>
          <div className="assump-source">Source: {a.source}</div>
        </div>
      )
    }
    if (label.includes('CPF range')) {
      return (
        <div className="assump-item">
          <div className="assump-title">Cost per follower (range)</div>
          <div className="assump-kv">${val.min.toFixed(2)} – ${val.max.toFixed(2)} (using ${val.mid.toFixed(2)} midpoint)</div>
          <div className="assump-source">Source: {a.source}</div>
        </div>
      )
    }
    return (
      <div className="assump-item">
        <div className="assump-title">{label}</div>
        <div className="assump-kv">{typeof val === 'string' ? val : <code>{JSON.stringify(val)}</code>}</div>
        <div className="assump-source">Source: {a.source}</div>
      </div>
    )
  }
  return (
    <div className="assump-block">
      {items.map((a, idx) => (
        <div key={idx}>{renderItem(a)}</div>
      ))}
    </div>
  )
}
// Distinct, accessible series colors
const SERIES_COLORS = {
  total: '#1E293B',            // dark slate for the main total line (works on light bg)
  instagram: '#D946EF',        // fuchsia
  tiktok: '#06B6D4',           // cyan
  youtube: '#EF4444',          // red
  facebook: '#3B82F6',         // blue
  bandFill: 'rgba(99,102,241,0.22)', // indigo fill for confidence band
  bandEdge: '#A5B4FC',         // light indigo for band edges
  mentions: '#22D3EE',         // cyan for mentions
  sentimentPos: '#10B981',     // green
  sentimentNeu: '#9CA3AF',     // gray
  sentimentNeg: '#EF4444',     // red
  tag1: '#6366F1',             // indigo
  tag2: '#F97316',             // orange
  tag3: '#10B981',             // green
}
