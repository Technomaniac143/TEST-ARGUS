from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class EvidenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    field: str
    value: str
    source: str
    url: str | None = None
    normalized_url: str | None = None
    source_type: str = "unknown"
    extraction_method: str = "regex"
    reliability_score: int = 50
    reliability_label: str = "LOW"
    crawl_status: str = "success"
    agreement_count: int = 1
    agreement_total: int = 1
    agreement: str = "1/1"
    created_at: datetime


class ConflictRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    field: str
    value1: str
    value2: str
    source1: str
    source2: str
    created_at: datetime


class BusinessRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str | None = None
    category: str | None = None
    location: str | None = None
    phone: str | None = None
    address: str | None = None
    website: str | None = None
    email: str | None = None
    confidence: float
    dna_score: float
    dna_breakdown: dict[str, int] = Field(default_factory=dict)
    risk: str
    reliability: str = "LOW"
    recommendation: str = "REVIEW_REQUIRED"
    recommendation_reason: str = ""
    risk_level: str = "MEDIUM"
    confidence_label: str = "MEDIUM"
    rank: int | None = None
    analyst_quality_flags: list[str] = Field(default_factory=list)
    evidence_graph: dict[str, list[dict[str, str]]] = Field(default_factory=dict)
    similar_businesses: list[dict[str, object]] = Field(default_factory=list)
    market_cluster: str = "Unassigned"
    percentile_score: int = 0
    market_position: str = "AVERAGE"
    centrality_score: int = 0
    top_relationship: str = ""
    shared_services_count: int = 0
    outliers: list[dict[str, str]] = Field(default_factory=list)
    competitive_intelligence: dict[str, object] = Field(default_factory=dict)
    analyst_output: dict[str, object] = Field(default_factory=dict)
    swot: dict[str, list[str]] = Field(default_factory=dict)
    overall_intelligence_score: int = 0
    executive_recommendation: str = ""
    explanation: dict[str, object] = Field(default_factory=dict)
    created_at: datetime
    evidence: list[EvidenceRead] = Field(default_factory=list)
    conflicts: list[ConflictRead] = Field(default_factory=list)
