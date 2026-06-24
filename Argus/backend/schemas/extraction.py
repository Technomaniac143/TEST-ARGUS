from pydantic import BaseModel, Field

from backend.schemas.search import SearchResult


class FieldEvidence(BaseModel):
    field: str
    value: str
    source: str
    url: str | None = None
    normalized_url: str | None = None
    source_type: str = "unknown"
    extraction_method: str = "regex"
    reliability_score: int = 50
    crawl_status: str = "success"


class ExtractedBusiness(BaseModel):
    name: str | None = None
    category: str | None = None
    location: str | None = None
    phone: str | None = None
    address: str | None = None
    website: str | None = None
    email: str | None = None
    services: str | None = None
    working_hours: str | None = None
    source_url: str | None = None
    source_name: str = "Unknown"
    evidence: list[FieldEvidence] = Field(default_factory=list)
    raw_search_result: SearchResult | None = None


class DnaScore(BaseModel):
    evidence_strength: int
    source_diversity: int
    completeness: int
    freshness: int
    conflict_penalty: int
    dna_score: int
