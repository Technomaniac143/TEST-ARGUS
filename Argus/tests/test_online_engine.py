from types import SimpleNamespace

import pytest
from bs4 import BeautifulSoup

from backend.schemas.search import ParsedQuery, SearchResult
from backend.services.collector import CollectorService
from backend.services.search import SearchService
from backend.services.source_planner import SourcePlannerService
from backend.services.url_quality import UrlQualityService


def settings(mode: str) -> SimpleNamespace:
    return SimpleNamespace(
        argus_mode=mode,
        argus_offline_mode=False,
        argus_demo_mode=False,
        enable_live_search=False,
        argus_max_source_targets=5,
        argus_max_results_per_source=10,
        argus_max_source_queries=12,
        argus_max_results_per_query=10,
        argus_search_timeout_seconds=1,
        request_timeout_seconds=1,
    )


def test_mode_selection_prefers_argus_mode() -> None:
    service = SearchService()

    assert service._mode(settings("online")) == "online"
    assert service._mode(settings("offline")) == "offline"
    assert service._mode(settings("demo")) == "demo"
    assert service._mode(settings("auto")) == "auto"


def test_online_source_planner_generates_targeted_queries() -> None:
    targets = SourcePlannerService().plan(ParsedQuery(category="cardiologists", location="birmingham"), 12)
    queries = [target.query for target in targets]

    assert "cardiologists in birmingham" in queries
    assert "best cardiologists birmingham" in queries
    assert "cardiologists birmingham official website" in queries
    assert any("site:yelp.com" in query for query in queries)
    assert any("site:healthgrades.com" in query for query in queries)


def test_url_filtering_and_normalization() -> None:
    quality = UrlQualityService()

    assert quality.reject_reason("https://accounts.google.com/login")
    assert quality.reject_reason("https://example.com/file.pdf")
    assert quality.reject_reason("https://googleadservices.com/page")
    assert quality.normalize("https://www.Example.com/path/?utm=1") == "https://example.com/path"


def test_json_ld_extraction() -> None:
    html = """
    <script type="application/ld+json">
    {
      "@type": "Dentist",
      "name": "Austin Smile Group",
      "telephone": "512-555-0100",
      "email": "care@example.com",
      "url": "https://austinsmile.example",
      "openingHours": ["Mon-Fri 8am-5pm"],
      "sameAs": ["https://facebook.com/austinsmile"],
      "image": "https://cdn.example.com/austin.jpg",
      "address": {"streetAddress": "10 Main St", "addressLocality": "Austin", "addressRegion": "TX"},
      "aggregateRating": {"ratingValue": "4.8", "reviewCount": "124"}
    }
    </script>
    """
    data = CollectorService()._extract_json_ld(BeautifulSoup(html, "html.parser"))

    assert data["name"] == "Austin Smile Group"
    assert data["phone"] == "512-555-0100"
    assert data["address"] == "10 Main St, Austin, TX"
    assert data["rating"] == "4.8"
    assert data["review_count"] == "124"


def test_contact_page_url_generation_is_bounded() -> None:
    urls = CollectorService().contact_page_urls("https://example.com", max_pages=4)

    assert urls == [
        "https://example.com",
        "https://example.com/contact",
        "https://example.com/about",
        "https://example.com/services",
    ]


@pytest.mark.anyio
async def test_auto_mode_falls_back_to_offline(monkeypatch) -> None:
    monkeypatch.setattr("backend.services.search.get_settings", lambda: settings("auto"))
    service = SearchService()
    service.online_providers = []

    results, _ = await service.search(ParsedQuery(category="cardiologists", location="birmingham"))

    assert len(results) >= 20
    assert service.last_metadata["fallback_used"] is True
    assert service.last_metadata["active_mode"] == "auto_fallback"


@pytest.mark.anyio
async def test_online_mode_does_not_fabricate_when_search_empty(monkeypatch) -> None:
    monkeypatch.setattr("backend.services.search.get_settings", lambda: settings("online"))
    service = SearchService()
    service.providers = []
    service.online_providers = []

    results, searched = await service.search(ParsedQuery(category="cardiologists", location="birmingham"))

    assert results == []
    assert searched == 0


@pytest.mark.anyio
async def test_url_deduplication_preserves_one_normalized_url(monkeypatch) -> None:
    monkeypatch.setattr("backend.services.search.get_settings", lambda: settings("online"))
    service = SearchService()
    duplicate = SearchResult(title="A", url="https://www.example.com/path", source="Fake")
    same = SearchResult(title="B", url="https://example.com/path/", source="Fake")

    assert len(service._dedupe_and_filter([duplicate, same])) == 1
