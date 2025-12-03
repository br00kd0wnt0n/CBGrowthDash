// API Service
const API_BASE = import.meta.env.VITE_API_BASE || 'https://cbgrowthdash-production.up.railway.app';

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
  health: () => request<{ status: string; version: string }>('/health'),
};
