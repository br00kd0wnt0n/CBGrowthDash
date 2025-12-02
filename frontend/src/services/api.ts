// API Service
const API_BASE = import.meta.env.VITE_API_BASE || '';

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

export const api = {
  getHistoricalData: () => request<HistoricalDataResponse>('/api/historical'),
  runForecast: (data: ForecastRequest) => request<ForecastResponse>('/api/forecast', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  }),
  health: () => request<{ status: string; version: string }>('/health'),
};
