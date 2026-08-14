const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000';

export interface ProcessSummary {
  id: number;
  name: string;
  department: string | null;
  industry: string | null;
  status: string;
  total_score: number | null;
  band: string | null;
  rank: number | null;
  percentile: number | null;
  created_at: string;
}

export interface Factor {
  factor_key: string;
  feature_value: number;
  weight: number;
  contribution: number;
  direction: string;
}

export interface Score {
  id: number;
  rubric_version: string;
  total_score: number;
  band: string;
  recommendation: string;
  recommendation_text: string;
  computed_at: string;
  factors: Factor[];
}

export interface Feature {
  feature_key: string;
  ordinal_value: number;
  normalized_value: number;
  rationale: string | null;
  confidence: number | null;
}

export interface EvidenceItem {
  id: number;
  quote: string | null;
  verified: boolean;
  verification_method: string | null;
  source_chunk_id: number | null;
  chunk_text: string | null;
  source_title: string | null;
  source_publisher: string | null;
  source_url: string | null;
  source_year: number | null;
}

export interface Claim {
  id: number;
  claim_text: string;
  claim_type: string | null;
  supported: boolean;
  evidence_items: EvidenceItem[];
}

export interface Rank {
  rank: number;
  percentile: number;
  rubric_version: string;
  computed_at: string;
}

export interface ProcessDetail {
  id: number;
  name: string;
  raw_description: string;
  department: string | null;
  industry: string | null;
  status: string;
  created_at: string;
  features: Feature[];
  score: Score | null;
  claims: Claim[];
  rank: Rank | null;
}

export interface BandCount {
  band: string;
  count: number;
}

export interface PortfolioSummary {
  total: number;
  band_counts: BandCount[];
  top_processes: ProcessSummary[];
  bottom_processes: ProcessSummary[];
  avg_score: number | null;
  score_distribution: { range: string; count: number }[];
}

export interface JobOut {
  id: number;
  kind: string;
  target_process_id: number | null;
  status: string;
  stage: string | null;
  progress: number;
  error: string | null;
  created_at: string;
  finished_at: string | null;
}

export interface ProcessCreateInput {
  name: string;
  raw_description: string;
  department?: string;
  industry?: string;
}

export interface IngestResponse {
  job_id: number;
  process_id: number;
  message: string;
}

export interface AskResponse {
  question: string;
  intent: string;
  query_plan: Record<string, unknown>;
  results: unknown;
  prose_explanation: string | null;
  unmappable: boolean;
  unmappable_message?: string;
}

export interface RubricData {
  version: string;
  factors: Record<string, { direction: string; weight: number; description: string }>;
  bands: { automate_threshold: number; augment_threshold: number };
  override: Record<string, unknown>;
}

export interface ProcessListResponse {
  items: ProcessSummary[];
  total: number;
  offset: number;
  limit: number;
}

// ─── API Functions ──────────────────────────────────────────────────────────

async function fetchJSON<T>(url: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, init);
  if (!res.ok) {
    const body = await res.text().catch(() => '');
    throw new Error(`API ${res.status}: ${body}`);
  }
  return res.json();
}

export const api = {
  // Health
  health: () => fetchJSON<{ status: string; db: string }>('/health'),

  // Processes
  listProcesses: (params?: {
    band?: string;
    department?: string;
    search?: string;
    sort_by?: string;
    sort_dir?: string;
    offset?: number;
    limit?: number;
  }) => {
    const sp = new URLSearchParams();
    if (params) {
      Object.entries(params).forEach(([k, v]) => {
        if (v !== undefined && v !== null && v !== '') sp.set(k, String(v));
      });
    }
    return fetchJSON<ProcessListResponse>(`/api/processes?${sp}`);
  },

  getProcess: (id: number) => fetchJSON<ProcessDetail>(`/api/processes/${id}`),

  ingestProcess: (data: ProcessCreateInput) =>
    fetchJSON<IngestResponse>('/api/processes', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    }),

  // Jobs
  getJob: (id: number) => fetchJSON<JobOut>(`/api/jobs/${id}`),

  // Portfolio
  portfolioSummary: () => fetchJSON<PortfolioSummary>('/api/portfolio/summary'),

  // Rubric
  getRubric: (version: string = 'v1') => fetchJSON<RubricData>(`/api/rubric/${version}`),

  // Ask
  ask: (question: string) =>
    fetchJSON<AskResponse>('/api/ask', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question }),
    }),

  // Compare
  compare: (ids: number[]) =>
    fetchJSON<unknown>('/api/compare', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ process_ids: ids }),
    }),
};
