import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
import re
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

from backend.config import get_settings
from backend.schemas.search import ParsedQuery, SearchResult, SourceTarget


@dataclass
class AdapterHealth:
    success_count: int = 0
    failure_count: int = 0
    timeout_count: int = 0
    blocked_count: int = 0
    total_response_time: float = 0.0
    last_success: str | None = None
    last_failure: str | None = None

    @property
    def average_response_time(self) -> float:
        attempts = self.success_count + self.failure_count + self.timeout_count + self.blocked_count
        return round(self.total_response_time / max(attempts, 1), 3)

    @property
    def health_score(self) -> int:
        attempts = self.success_count + self.failure_count + self.timeout_count + self.blocked_count
        if attempts == 0:
            return 100
        penalty = self.failure_count * 15 + self.timeout_count * 20 + self.blocked_count * 25
        return max(0, min(100, 100 - penalty))

    def as_dict(self) -> dict[str, object]:
        return {
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "timeout_count": self.timeout_count,
            "average_response_time": self.average_response_time,
            "blocked_count": self.blocked_count,
            "last_success": self.last_success,
            "last_failure": self.last_failure,
            "health_score": self.health_score,
        }


@dataclass
class SourceAdapter:
    adapter_name: str
    source_type: str
    domain: str | None = None
    labels: list[str] = field(default_factory=list)
    blocked_markers: tuple[str, ...] = ("captcha", "unusual traffic", "access denied", "verify you are human")

    def __post_init__(self) -> None:
        self._health = AdapterHealth()

    async def discover(self, parsed_query: ParsedQuery, target: SourceTarget, page: int = 1) -> list[SearchResult]:
        settings = get_settings()
        query = self.query_for(parsed_query, target, page)
        url = f"https://duckduckgo.com/html/?q={quote_plus(query)}"
        started = time.perf_counter()
        try:
            async with httpx.AsyncClient(
                timeout=settings.argus_search_timeout_seconds,
                headers={"User-Agent": "Mozilla/5.0 ARGUS adapter research bot"},
            ) as client:
                response = await client.get(url, follow_redirects=True)
                response.raise_for_status()
        except httpx.TimeoutException:
            self._record("timeout", started)
            return []
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            self._record("blocked" if status in {403, 429} else "failure", started)
            return []
        except httpx.HTTPError:
            self._record("failure", started)
            return []

        if self._blocked(response.text):
            self._record("blocked", started)
            return []

        soup = BeautifulSoup(response.text, "html.parser")
        results: list[SearchResult] = []
        for node in soup.select(".result__a, a"):
            href = str(node.get("href") or "")
            title = node.get_text(" ", strip=True)
            if not href.startswith(("http://", "https://")) or not title:
                continue
            if self.domain and self.domain not in href.lower():
                continue
            results.append(
                SearchResult(
                    title=title,
                    url=href,
                    snippet=self.snippet_for(parsed_query, target),
                    source=self.adapter_name,
                    source_type=self.source_type,
                    adapter_name=self.adapter_name,
                    confidence=self.confidence_for_url(href),
                    adapter_health=self.health().get("health_score", 100),
                    metadata={"page": page, "query": query, "domain": self.domain},
                )
            )
        self._record("success", started)
        return results

    async def collect(self, html: str, url: str) -> dict[str, object]:
        soup = BeautifulSoup(html, "html.parser")
        text = soup.get_text("\n", strip=True)
        fields = self.extract_fields(text, soup)
        return {key: value for key, value in fields.items() if value}

    def health(self) -> dict[str, object]:
        return self._health.as_dict()

    def query_for(self, parsed_query: ParsedQuery, target: SourceTarget, page: int = 1) -> str:
        base = target.query
        if self.domain and f"site:{self.domain}" not in base:
            base = f"site:{self.domain} {parsed_query.category} {parsed_query.location}"
        return f"{base} page {page}" if page > 1 else base

    def extract_fields(self, text: str, soup: BeautifulSoup) -> dict[str, object]:
        fields: dict[str, object] = {}
        aliases = {
            "doctor": "doctor",
            "speciality": "speciality",
            "specialities": "specialities",
            "experience": "experience",
            "clinic": "clinic",
            "timings": "timings",
            "phone": "phone",
            "address": "address",
            "rating": "rating",
            "practice areas": "practice_areas",
            "license status": "license_status",
            "company": "company_name",
            "website": "website",
            "industry": "industry",
            "accreditation": "accreditation",
            "certifications": "certifications",
        }
        for label in self.labels:
            value = self._labeled_value(text, label)
            if value:
                fields[aliases.get(label, label.replace(" ", "_"))] = value
        notes = [label for label in self.labels if label.lower() in text.lower()]
        if notes:
            fields["source_specific_notes"] = "; ".join(notes)
        return fields

    def snippet_for(self, parsed_query: ParsedQuery, target: SourceTarget) -> str:
        return f"{self.adapter_name} discovery result for {parsed_query.category} in {parsed_query.location}."

    def confidence_for_url(self, url: str) -> int:
        if self.domain and self.domain in url.lower():
            return 88
        return 65

    def _blocked(self, html: str) -> bool:
        lowered = html.lower()
        return any(marker in lowered for marker in self.blocked_markers)

    def _labeled_value(self, text: str, label: str) -> str | None:
        pattern = re.compile(rf"{re.escape(label)}\s*[:\-]\s*([^\n|]+)", re.I)
        match = pattern.search(text)
        return match.group(1).strip(" .") if match else None

    def _record(self, status: str, started: float) -> None:
        self._health.total_response_time += time.perf_counter() - started
        now = datetime.now(timezone.utc).isoformat()
        if status == "success":
            self._health.success_count += 1
            self._health.last_success = now
        elif status == "timeout":
            self._health.timeout_count += 1
            self._health.last_failure = now
        elif status == "blocked":
            self._health.blocked_count += 1
            self._health.last_failure = now
        else:
            self._health.failure_count += 1
            self._health.last_failure = now
