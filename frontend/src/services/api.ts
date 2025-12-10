// API Service
const isDev = import.meta.env.DEV;
const DEFAULT_PROD_API = 'https://cbgrowthdash-production.up.railway.app';
const API_BASE: string = (import.meta.env.VITE_API_BASE as string | undefined)
  || (isDev ? 'http://localhost:8000' : DEFAULT_PROD_API);

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${API_BASE}${path}`;
  const res = await fetch(url, init);
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
  return res.json() as Promise<T>;
}

export interface ForecastRequest {
  current_followers: Record<string, number>;
  posts_per_week_total: number;
  platform_allocation: Record<string, number>;
  content_mix_by_platform: Record<string, Record<string, number>>;
  months: number;
  preset: string;
  // Optional paid media fields
  paid_impressions_per_week_total?: number;
  paid_allocation?: Record<string, number>;
  paid_funnel?: Record<string, { vtr: number; er: number; fcr: number }>;
  // Optional budget + CPF fields
  paid_budget_per_week_total?: number;
  creator_budget_per_week_total?: number;
  acquisition_budget_per_week_total?: number;
  cpf_paid?: { min: number; mid: number; max: number };
  cpf_creator?: { min: number; mid: number; max: number };
  cpf_acquisition?: { min: number; mid: number; max: number };
}

export interface MonthlyForecast {
  month: number;
  Instagram: number;
  TikTok: number;
  YouTube: number;
  Facebook: number;
  total: number;
  added: number;
}

export interface ForecastResponse {
  monthly_data: MonthlyForecast[];
  goal: number;
  projected_total: number;
  progress_to_goal: number;
  added_breakdown?: { month: number; organic_added: number; paid_added: number; total_added: number }[];
}

export interface HistoricalDataResponse {
  mentions: any[];
  sentiment: any[];
  tags: any[];
  engagement_index: number[];
}

export interface AIScenario {
  name: string;
  posts_per_week: number;
  platform_allocation: Record<string, number>;
  reasoning: string;
  risk_level: 'LOW' | 'MEDIUM' | 'HIGH';
  expected_outcome: string;
}

export interface AIInsightsResponse {
  analysis: string;
  scenarios: AIScenario[];
  key_insights: string[];
}

export interface InsightResponse { insight: string }
export interface AssumptionsPayload { assumptions: any[] }
export interface ParamSuggestion { key: string; current: number; suggested: number; reason: string; confidence: string }
export interface ParamTuneResponse { suggestions: ParamSuggestion[] }
export interface FollowersHistoryPayload { labels: string[]; data: Array<any> }
export interface PlatformMetricsResponse {
  months: string[];
  posts: Record<string, (number | null)[]>;
  engagement: Record<string, (number | null)[]>;
  views?: Record<string, (number | null)[]>;
}

// GWI Research types
export interface AudiencePreset {
  id: string;
  name: string;
  description: string;
  segment_focus: 'parents' | 'gifters' | 'collectors' | 'emerging' | 'balanced';
  platform_allocation: Record<string, number>;
  posts_per_week: number;
  rationale: string;
  data_source: string;
  risk_level: 'low' | 'medium' | 'high';
  expected_goal_range: [number, number];
  content_recommendations: string[];
}

export interface PresetsResponse {
  presets: AudiencePreset[];
  default: string;
}

export interface ResearchOverview {
  meta: {
    source: string;
    total_respondents: number;
    segments: string[];
    confidence_level: number;
    margin_of_error: number;
  };
  key_insights: Record<string, any>;
  segments_summary: Record<string, { sample_size: number; description: string }>;
}

export interface SegmentData {
  segment: string;
  data: any;
  insights: {
    segment: string;
    sample_size: number;
    description: string;
    top_platforms: Array<{ platform: string; index: number; insight: string }>;
    top_drivers?: Array<{ driver: string; pct: number }>;
    top_motivations?: Array<{ motivation: string; pct: number }>;
  };
}

export interface PlatformInsight {
  platform: string;
  segments: Record<string, { total_usage: number; purchaser_usage: number; index: number }>;
  avg_index: number;
  insight: string;
}

export interface AllocationRecommendation {
  recommended_allocation: Record<string, number>;
  rationale: string;
  confidence: number;
  segment_weights: Record<string, number>;
}

export interface ContextualInsight {
  type: 'positive' | 'warning' | 'info' | 'highlight';
  text: string;
  detail: string;
}

export interface ContextualInsightsResponse {
  context: string;
  insights: ContextualInsight[];
}

// AI Strategy Critique types
export interface CritiqueRequest {
  current_followers: Record<string, number>;
  posts_per_week: number;
  platform_allocation: Record<string, number>;
  content_mix: Record<string, Record<string, number>>;
  months: number;
  preset: string;
  audience_mix: Record<string, number>;
  projected_total: number;
  goal: number;
  paid_budget_week?: number;
  creator_budget_week?: number;
  acquisition_budget_week?: number;
  cpf_range?: { min: number; mid: number; max: number };
  previous_suggestions?: Optimization[] | null;
}

export interface CategoryAssessment {
  category: string;
  rating: 'OPTIMAL' | 'ACCEPTABLE' | 'NEEDS_ADJUSTMENT' | 'ON_TRACK' | 'ACHIEVABLE' | 'STRETCH' | 'UNLIKELY';
  current_value: string;
  assessment: string;
  suggestion: string | null;
  suggested_value: string | null;
}

export interface Optimization {
  priority: number;
  action: string;
  impact: string;
  effort: 'LOW' | 'MEDIUM' | 'HIGH';
}

export interface CritiqueResponse {
  overall_assessment: {
    rating: 'STRONG' | 'GOOD' | 'NEEDS_WORK' | 'AT_RISK';
    summary: string;
  };
  category_assessments: CategoryAssessment[];
  top_optimizations: Optimization[];
  gwi_alignment_notes: string[];
  recommended_changes?: {
    posts_per_week?: number;
    platform_allocation?: Record<string, number>;
    content_mix_by_platform?: Record<string, Record<string, number>>;
  };
  estimated_impact?: number; // percent delta vs current projection
  convergence_note?: string;
}

// User Preset types
export interface UserPresetConfig {
  currentFollowers: Record<string, number>;
  postsPerWeek: number;
  platformAllocation: Record<string, number>;
  contentMix: Record<string, Record<string, number>>;
  preset: string;
  months: number;
  enablePaid: boolean;
  paidFunnelBudgetWeek: number;
  paidCPM: number;
  paidAllocation: Record<string, number>;
  enableBudget: boolean;
  paidBudgetWeek: number;
  creatorBudgetWeek: number;
  acquisitionBudgetWeek: number;
  cpfMin: number;
  cpfMid: number;
  cpfMax: number;
  valuePerFollower: number;
  audienceMix: Record<string, number>;
  selectedPresetId: string;
}

export interface UserPresetCreate {
  name: string;
  description?: string;
  config: UserPresetConfig;
}

export interface UserPresetResponse {
  id: number;
  name: string;
  description: string | null;
  created_at: string;
  updated_at: string | null;
  config: UserPresetConfig;
}

export const api = {
  getHistoricalData: () => request<HistoricalDataResponse>('/api/historical'),
  runForecast: (data: ForecastRequest) => request<ForecastResponse>('/api/forecast', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  }),
  getAIInsights: (data: ForecastRequest) => request<AIInsightsResponse>('/api/ai-insights', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  }),
  getAIInsight: (data: any) => request<InsightResponse>('/api/ai/insight', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  }),
  getAssumptions: () => request<AssumptionsPayload>('/api/assumptions-plain'),
  getFollowersHistory: (sheetPath?: string) => request<FollowersHistoryPayload>(`/api/followers-history${sheetPath?`?sheet_path=${encodeURIComponent(sheetPath)}`:''}`),
  tuneParameters: (data: any) => request<ParamTuneResponse>('/api/ai/tune-parameters', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  }),
  health: () => request<{ status: string; version: string }>('/health'),
  getPlatformMetrics: () => request<PlatformMetricsResponse>('/api/platform-metrics'),
  // Research API endpoints
  getResearchOverview: () => request<ResearchOverview>('/api/research/overview'),
  getPresets: () => request<PresetsResponse>('/api/research/presets'),
  getPreset: (presetId: string) => request<AudiencePreset>(`/api/research/presets/${presetId}`),
  getSegment: (segmentName: string) => request<SegmentData>(`/api/research/segments/${segmentName}`),
  getPlatformInsight: (platformName: string) => request<PlatformInsight>(`/api/research/platforms/${platformName}`),
  getRecommendedAllocation: (audienceMix: { parents: number; gifters: number; collectors: number }) =>
    request<AllocationRecommendation>('/api/research/allocation/recommend', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(audienceMix),
    }),
  getContextualInsights: (context: string, platform?: string, value?: number) =>
    request<ContextualInsightsResponse>(
      `/api/research/insights/contextual/${context}${platform ? `?platform=${platform}` : ''}${value ? `&value=${value}` : ''}`
    ),
  // User Presets API endpoints
  getUserPresets: () => request<UserPresetResponse[]>('/api/user-presets/'),
  getUserPreset: (id: number) => request<UserPresetResponse>(`/api/user-presets/${id}`),
  createUserPreset: (data: UserPresetCreate) => request<UserPresetResponse>('/api/user-presets/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  }),
  updateUserPreset: (id: number, data: UserPresetCreate) => request<UserPresetResponse>(`/api/user-presets/${id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  }),
  deleteUserPreset: (id: number) => request<{ message: string }>(`/api/user-presets/${id}`, {
    method: 'DELETE',
  }),
  checkDbHealth: () => request<{ status: string; message: string }>('/api/user-presets/health/db'),
  // AI Strategy Critique
  getStrategyCritique: (data: CritiqueRequest) => request<CritiqueResponse>('/api/ai/critique', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  }),
};
