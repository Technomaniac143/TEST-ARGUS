from pydantic import BaseModel, Field


class ParsedQuery(BaseModel):
    category: str
    location: str


class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str = ""
    source: str
    source_type: str = "general_search"
    adapter_name: str | None = None
    confidence: int | None = None
    adapter_health: int | None = None
    metadata: dict[str, object] = Field(default_factory=dict)


class SourceTarget(BaseModel):
    source_type: str
    query: str
    label: str


class ResearchStartRequest(BaseModel):
    query: str
    mode: str | None = None


class ResearchStartResponse(BaseModel):
    session_id: str
    job_id: str | None = None
    status: str
