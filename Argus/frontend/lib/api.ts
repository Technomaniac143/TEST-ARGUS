export const API_BASE_URL = process.env.NEXT_PUBLIC_ARGUS_API_URL || "";

export type ArgusMode = "auto" | "online" | "offline" | "demo";

export type TimelineEvent = {
  event: string;
  message: string;
  status: string;
  elapsed_seconds?: number;
  stage?: string | null;
  progress?: number;
  payload?: Record<string, unknown>;
};

export type Business = {
  id: number | string;
  name?: string | null;
  category?: string | null;
  location?: string | null;
  phone?: string | null;
  address?: string | null;
  website?: string | null;
  confidence?: number;
  dna_score?: number;
  dnaScore?: number;
  risk?: string;
  risk_level?: string;
  reliability?: string;
  confidence_label?: string;
  recommendation?: string;
  executive_recommendation?: string;
  overall_intelligence_score?: number;
  dna_breakdown?: Record<string, number>;
  analyst_quality_flags?: string[];
  quality_flags?: string[];
  flags?: string[];
  evidence_graph?: Record<string, unknown>;
  similar_businesses?: Array<Record<string, unknown>>;
  market_cluster?: string;
  market_position?: string;
  percentile_score?: number;
  centrality_score?: number;
  top_relationship?: string;
  shared_services_count?: number;
  competitive_intelligence?: Record<string, unknown>;
  analyst_output?: Record<string, unknown>;
  swot?: Record<string, unknown>;
  outliers?: Array<Record<string, unknown>>;
  evidence?: Array<Record<string, unknown>>;
  conflicts?: Array<Record<string, unknown>>;
};

export type ResearchReport = {
  executive_summary?: string;
  active_mode?: string;
  support_level?: string;
  cache_hit?: boolean;
  cache_age_seconds?: number | null;
  cached_at?: string | null;
  cache_key?: string | null;
  unsupported_message?: string | null;
  suggested_queries?: string[];
  businesses_found?: number;
  businesses_verified?: number;
  duplicates_removed?: number;
  sources_searched?: number;
  research_duration?: number;
  top_recommendations?: string[];
  top_recommended_businesses?: Array<Record<string, unknown>>;
  ranked_businesses?: Array<Record<string, unknown>>;
  executive_report?: Record<string, unknown>;
  scorecard?: Record<string, number>;
  recommendations?: Record<string, string[]>;
  market_narratives?: Record<string, string>;
  benchmarks?: Record<string, unknown>;
  [key: string]: unknown;
};

export type ResearchSession = {
  session_id?: string;
  id: number;
  query: string;
  category?: string | null;
  location?: string | null;
  status: string;
  stage?: string;
  progress?: number;
  mode?: ArgusMode | string;
  active_mode?: string;
  metrics?: {
    businesses?: number;
    verified?: number;
    sources?: number;
    failed_urls?: number;
    duration_seconds?: number;
  };
  error_summary?: string[];
  duration?: number;
  sources_searched?: number;
  businesses_found?: number;
  duplicates_removed?: number;
  timeline_events?: TimelineEvent[];
  job?: {
    id?: number;
    status?: string;
    current_stage?: string;
    stage_progress?: number;
    total_urls?: number;
    processed_urls?: number;
    verified_businesses?: number;
    failed_urls?: number;
    enrichment_status?: string;
    partial_businesses?: string[];
  };
  report_ready?: boolean;
  cache_hit?: boolean;
  cache_age_seconds?: number | null;
  cached_at?: string | null;
  cache_key?: string | null;
  report?: ResearchReport;
  businesses: Business[];
};

export type StartResearchResponse = {
  session_id: string;
  job_id?: string | null;
  status: string;
};

export class ApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

export async function startResearch(query: string, mode: ArgusMode = "auto"): Promise<StartResearchResponse> {
  const response = await fetch(`${API_BASE_URL}/api/research/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, mode }),
  });
  if (!response.ok) throw new ApiError("Unable to start ARGUS research", response.status);
  return response.json();
}

export async function getResearch(sessionId: string): Promise<ResearchSession> {
  const response = await fetch(`${API_BASE_URL}/api/research/${sessionId}`);
  if (!response.ok) throw new ApiError("Unable to load ARGUS research session", response.status);
  return response.json();
}

export async function getBasicResearch(sessionId: string): Promise<ResearchSession> {
  const response = await fetch(`${API_BASE_URL}/api/research/${sessionId}/basic`);
  if (!response.ok) throw new ApiError("Unable to load ARGUS research session", response.status);
  return response.json();
}

export function streamResearchEvents(
  sessionId: string,
  onEvent: (event: TimelineEvent) => void,
  onError?: () => void,
): EventSource {
  const source = new EventSource(`${API_BASE_URL}/api/research/${sessionId}/events`);
  const handler = (event: MessageEvent) => onEvent(JSON.parse(event.data) as TimelineEvent);
  [
    "job_queued",
    "job_started",
    "stage_changed",
    "business_candidate_found",
    "url_processed",
    "business_verified",
    "business_enriched",
    "conflict_found",
    "report_ready",
    "job_completed",
    "job_failed",
    "research_complete",
    "research_failed",
  ].forEach((eventName) => source.addEventListener(eventName, handler));
  source.onerror = () => {
    onError?.();
  };
  return source;
}

export async function cancelResearch(sessionId: string): Promise<Record<string, unknown>> {
  const response = await fetch(`${API_BASE_URL}/api/research/${sessionId}/cancel`, { method: "POST" });
  if (!response.ok) throw new ApiError("Unable to cancel research", response.status);
  return response.json();
}

export async function getRecentJobs(): Promise<Array<Record<string, unknown>>> {
  const response = await fetch(`${API_BASE_URL}/api/research/jobs/recent`);
  if (!response.ok) throw new ApiError("Unable to load recent jobs", response.status);
  return response.json();
}
