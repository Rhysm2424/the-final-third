/**
 * Frontend types — kept in lockstep with backend Pydantic schemas
 * at backend/app/api/schemas.py.
 *
 * If you change one, change the other.
 */

export interface Team {
  id: number;
  short_name: string;
  full_name: string;
  tla: string | null;
  crest_url: string | null;
  primary_color: string | null;
  secondary_color: string | null;
  is_premier_league: boolean;
}

export interface Competition {
  id: number;
  code: string;
  name: string;
  tier: string;
}

export interface MatchSummary {
  id: number;
  kickoff: string;
  matchday: number | null;
  status: string;
  home_team: Team;
  away_team: Team;
  competition: Competition;
  home_score: number | null;
  away_score: number | null;
  prob_home: number | null;
  prob_draw: number | null;
  prob_away: number | null;
}

export interface ScorelineProb {
  home: number;
  away: number;
  prob: number;
}

export interface Driver {
  label: string;
  detail: string;
  impact_pp: number;
  direction: 'home' | 'away' | 'neutral';
}

export interface Prediction {
  id: number;
  model_name: string;
  prob_home: number;
  prob_draw: number;
  prob_away: number;
  home_xg: number;
  away_xg: number;
  prob_btts: number | null;
  prob_over_2_5: number | null;
  scoreline_distribution: ScorelineProb[] | null;
  drivers: Driver[] | null;
  narrative: string | null;
  created_at: string;
}

export interface MatchDetail {
  id: number;
  kickoff: string;
  matchday: number | null;
  venue: string | null;
  status: string;
  home_team: Team;
  away_team: Team;
  competition: Competition;
  home_score: number | null;
  away_score: number | null;
  home_xg: number | null;
  away_xg: number | null;
  odds_home: number | null;
  odds_draw: number | null;
  odds_away: number | null;
  prediction: Prediction | null;
}

export interface Insight {
  id: number;
  kind: string;
  subject: string;
  headline: string;
  detail: string;
  data: Record<string, unknown>;
  notability: number;
  is_weighted: boolean;
  created_at: string;
}

export interface LeagueProjectionRow {
  team: Team;
  expected_position: number;
  expected_points: number;
  title_probability: number;
  top_four_probability: number;
  relegation_probability: number;
}

export interface LeagueProjectionResponse {
  competition: Competition;
  as_of: string;
  rows: LeagueProjectionRow[];
}

export interface CalibrationBin {
  bin_lower: number;
  bin_upper: number;
  predicted: number;
  actual: number;
  count: number;
}

export interface TrackRecordSummary {
  n_predictions: number;
  brier_score: number;
  log_loss: number;
  top_pick_accuracy: number;
  market_brier: number | null;
  market_log_loss: number | null;
  simulated_pnl_units: number | null;
  simulated_roi_pct: number | null;
  calibration_bins: CalibrationBin[];
  model_name: string;
  season_range: string;
}

export interface PastPredictionRow {
  match_id: number;
  date: string;
  home_team: string;
  away_team: string;
  home_score: number | null;
  away_score: number | null;
  pick: 'home' | 'draw' | 'away';
  pick_label: string;
  pick_probability: number;
  result: 'hit' | 'miss' | 'pending';
}

export interface TrackRecordResponse {
  summary: TrackRecordSummary;
  recent: PastPredictionRow[];
}

export interface HealthResponse {
  status: string;
  demo_mode: boolean;
  version: string;
}
