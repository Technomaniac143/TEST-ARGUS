from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.schemas.business import BusinessRead


class ResearchReportRead(BaseModel):
    query: str
    businesses_found: int
    businesses_verified: int
    verified_businesses: int
    duplicates_removed: int
    sources_searched: int
    research_duration: float
    conflicts_found: int
    high_confidence_count: int
    weak_records_count: int
    records_with_website_percentage: int
    records_with_phone_percentage: int
    records_with_working_hours_percentage: int
    records_with_license_percentage: int
    source_reliability_average: int
    cache_hit: bool = False
    cached_at: str | None = None
    cache_age_seconds: float | None = None
    cache_key: str | None = None
    offline_mode: bool = False
    active_mode: str = "Auto"
    fallback_used: bool = False
    fallback_reason: str | None = None
    online_results_count: int = 0
    filtered_urls_count: int = 0
    source_health: dict[str, object] = Field(default_factory=dict)
    adapter_health: dict[str, object] = Field(default_factory=dict)
    job: dict[str, object] = Field(default_factory=dict)
    recent_jobs: list[dict[str, object]] = Field(default_factory=list)
    contradiction_map: list[dict[str, object]] = Field(default_factory=list)
    review_queue: list[dict[str, object]] = Field(default_factory=list)
    knowledge_graph: dict[str, list[dict[str, str]]] = Field(default_factory=dict)
    clusters: list[dict[str, object]] = Field(default_factory=list)
    market_positions: list[dict[str, object]] = Field(default_factory=list)
    outliers: dict[str, list[dict[str, str]]] = Field(default_factory=dict)
    market_overview: dict[str, object] = Field(default_factory=dict)
    market_comparison: dict[str, object] = Field(default_factory=dict)
    relationship_graph: dict[str, object] = Field(default_factory=dict)
    ecosystem_summary: dict[str, object] = Field(default_factory=dict)
    centrality_metrics: list[dict[str, object]] = Field(default_factory=list)
    similar_pairs: list[dict[str, object]] = Field(default_factory=list)
    analyst_output: dict[str, object] = Field(default_factory=dict)
    swot: dict[str, object] = Field(default_factory=dict)
    scorecard: dict[str, int] = Field(default_factory=dict)
    recommendations: dict[str, list[str]] = Field(default_factory=dict)
    market_narratives: dict[str, str] = Field(default_factory=dict)
    benchmarks: dict[str, object] = Field(default_factory=dict)
    support_level: str = "LIVE_MODE"
    unsupported_message: str | None = None
    suggested_queries: list[str] = Field(default_factory=list)
    offline_corpus_coverage: dict[str, object] = Field(default_factory=dict)
    live_source_plan: list[str] = Field(default_factory=list)
    export_ready: bool = True
    discovered_records_raw: int
    processed_records: int
    final_unique_businesses: int
    requirement_coverage: dict[str, str] = Field(default_factory=dict)
    challenge_requirement_coverage: dict[str, str] = Field(default_factory=dict)
    executive_report: dict[str, object] = Field(default_factory=dict)
    demo_command_center: list[str] = Field(default_factory=list)
    top_recommendations: list[str] = Field(default_factory=list)
    data_quality_summary: str
    executive_summary: str


class TimelineReplayEvent(BaseModel):
    event: str
    message: str
    status: str
    elapsed_seconds: float = 0


class ResearchSessionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    query: str
    category: str | None = None
    location: str | None = None
    status: str
    duration: float
    sources_searched: int
    businesses_found: int
    duplicates_removed: int
    timeline_summary: str = "[]"
    timeline_events: list[TimelineReplayEvent] = Field(default_factory=list)
    report: ResearchReportRead | None = None
    cache_hit: bool = False
    cached_at: str | None = None
    cache_age_seconds: float | None = None
    cache_key: str | None = None
    job: dict[str, object] = Field(default_factory=dict)
    report_ready: bool = False
    created_at: datetime
    businesses: list[BusinessRead] = Field(default_factory=list)


class TimelineEvent(BaseModel):
    session_id: int
    event: str
    message: str
    status: str = "running"
    elapsed_seconds: float = 0
    payload: dict[str, object] = Field(default_factory=dict)
    stage: str | None = None
    progress: float = 0
