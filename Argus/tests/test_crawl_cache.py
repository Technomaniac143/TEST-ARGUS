from datetime import timedelta
from uuid import uuid4

import pytest

from backend.database.session import SessionLocal, init_db
from backend.models.crawl_cache import CrawlCache
from backend.schemas.extraction import ExtractedBusiness
from backend.schemas.search import ParsedQuery, SearchResult
from backend.services.collector import CollectorService
from backend.services.crawl_cache import CrawlCacheService
from backend.services.report import ResearchReportService
from backend.services.url_quality import UrlQualityService


def unique_url(path: str = "") -> str:
    return f"https://example.com/{uuid4().hex}{path}?utm_source=test#frag"


def test_url_normalization_removes_tracking_and_fragments() -> None:
    normalized = UrlQualityService().normalize("HTTPS://www.Example.com/Path/?utm_source=x&keep=1#section")

    assert normalized == "https://example.com/Path?keep=1"


def test_crawl_cache_miss_and_hit() -> None:
    init_db()
    service = CrawlCacheService()
    url = unique_url()
    result = SearchResult(title="Example", url=url, source="Official Website", source_type="official_website")
    db = SessionLocal()
    try:
        assert service.get_valid_success(db, url) is None
        business = ExtractedBusiness(name="Example", source_name="Official Website", source_url=url)
        service.store_success(db, result, business, "Example text", "<html>Example</html>", 200)

        cached = service.get_valid_success(db, url)

        assert cached is not None
        assert cached.status == "success"
        assert cached.attempt_count == 1
    finally:
        db.close()


def test_failed_crawl_persistence_and_ttl_expiry() -> None:
    init_db()
    service = CrawlCacheService()
    url = unique_url("/failed")
    result = SearchResult(title="Bad", url=url, source="DuckDuckGo", source_type="general_search")
    db = SessionLocal()
    try:
        service.store_failure(db, result, "timeout", http_status=504)
        assert service.is_valid_failure(db, url) is True

        cache = db.query(CrawlCache).filter(CrawlCache.normalized_url == service.normalized_url(url)).one()
        cache.ttl_expires_at = service._now() - timedelta(seconds=1)
        db.commit()

        assert service.is_valid_failure(db, url) is False
    finally:
        db.close()


@pytest.mark.anyio
async def test_evidence_includes_extraction_method_and_crawl_status() -> None:
    result = SearchResult(
        title="Offline",
        url="offline://official_websites/cardiologists_birmingham_0_official_websites.html",
        source="Official Website",
        source_type="official_website",
    )

    business = await CollectorService().collect_one(result, ParsedQuery(category="cardiologists", location="birmingham"))

    assert business.evidence
    assert all(item.extraction_method == "corpus_html" for item in business.evidence)
    assert all(item.crawl_status == "success" for item in business.evidence)
    assert all(item.normalized_url for item in business.evidence)


def test_source_health_metrics_from_timeline() -> None:
    class Session:
        query = "Cardiologists in Birmingham"
        businesses_found = 1
        duplicates_removed = 0
        sources_searched = 1
        duration = 1.0
        timeline_summary = (
            '[{"event":"url_discovered","message":"URL discovered: https://a.example"},'
            '{"event":"crawl_cache_hit","message":"Crawl cache hit: https://a.example"},'
            '{"event":"crawl_cache_miss","message":"Crawl cache miss: https://b.example"},'
            '{"event":"crawl_succeeded","message":"Crawl succeeded: https://a.example"},'
            '{"event":"crawl_failed","message":"Crawl failed: https://b.example"}]'
        )

    businesses = [
        {
            "confidence_label": "HIGH",
            "recommendation": "RECOMMENDED",
            "conflicts": [],
            "website": "https://a.example",
            "phone": "2055550100",
            "evidence": [
                {"field": "phone", "source": "Official Website", "reliability_score": 95},
            ],
            "name": "Example",
        }
    ]

    report = ResearchReportService().build(Session(), businesses)

    assert report["source_health"]["urls_discovered"] == 1
    assert report["source_health"]["crawl_cache_hits"] == 1
    assert report["source_health"]["crawl_failures"] == 1
