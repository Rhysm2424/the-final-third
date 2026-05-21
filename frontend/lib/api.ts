/**
 * API client. All requests go through here.
 */

import type {
  HealthResponse,
  Insight,
  LeagueProjectionResponse,
  MatchDetail,
  MatchSummary,
  TrackRecordResponse,
} from './types';

const API_URL =
  typeof window === 'undefined'
    ? process.env.NEXT_PUBLIC_API_URL || 'http://backend:8000'
    : 'http://localhost:8000';
async function get<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(options?.headers ?? {}),
    },
    cache: 'no-store',
  });
  if (!res.ok) {
    throw new Error(`API ${path} returned ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => get<HealthResponse>('/health'),
  fixtures: (params?: { days_ahead?: number; days_back?: number }) => {
    const q = new URLSearchParams();
    if (params?.days_ahead) q.set('days_ahead', String(params.days_ahead));
    if (params?.days_back) q.set('days_back', String(params.days_back));
    const qs = q.toString();
    return get<MatchSummary[]>(`/fixtures${qs ? `?${qs}` : ''}`);
  },
  match: (id: number) => get<MatchDetail>(`/matches/${id}`),
  insights: (limit = 20) => get<Insight[]>(`/insights?limit=${limit}`),
  league: (code: string) => get<LeagueProjectionResponse>(`/league/${code}`),
  trackRecord: () => get<TrackRecordResponse>('/track-record'),
};
