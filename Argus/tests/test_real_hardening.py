import asyncio
from types import SimpleNamespace
from uuid import uuid4

import pytest
from sqlalchemy import delete

from backend.agents.scout import ScoutAgent
from backend.database.session import SessionLocal, init_db
from backend.models.research_cache import ResearchCache
from backend.schemas.extraction import ExtractedBusiness
from backend.schemas.search import ParsedQuery, SearchResult, SourceTarget
from backend.services.collector import CollectorService
from backend.services.research import research_service
from backend.services.search import SearchService
from backend.services.source_planner import SourcePlannerService
from backend.utils.text import extract_links, extract_rating, extract_review_count, first_match
from backend.utils.text import EMAIL_RE, HOURS_RE, IMAGE_URL_RE, PHONE_RE, SOCIAL_LINK_RE


def test_source_planner_outputs_required_source_types() -> None:
    parsed = ScoutAgent().parse_query("Cardiologists in Birmingham")

    targets = SourcePlannerService().plan(parsed, max_targets=8)
    source_types = {target.source_type for target in targets}

    assert "general_search" in source_types
    assert "directory" in source_types
    assert "review_platform" in source_types
    assert "professional_directory" in source_types
    assert "government_license_registry" in source_types
    assert "social_profile" in source_types


@pytest.mark.anyio
async def test_fanout_url_deduplicates_results(monkeypatch) -> None:
    class FakeProvider:
        async def search(self, parsed_query, limit=5, query_text=None, source_type="general_search"):
            return [
                SearchResult(
                    title=f"{query_text} result",
                    url="https://same.example/profile",
                    snippet="same",
                    source="Fake",
                    source_type=source_type,
                )
            ]

    service = SearchService()
    service.providers = [FakeProvider()]
    service.planner.plan = lambda parsed, max_targets=5: [
        SourceTarget(source_type="directory", query="one", label="One"),
        SourceTarget(source_type="review_platform", query="two", label="Two"),
    ]
    monkeypatch.setattr(
        "backend.services.search.get_settings",
        lambda: SimpleNamespace(
            argus_demo_mode=False,
            argus_max_source_targets=2,
            argus_max_results_per_source=10,
        ),
    )

    results, searched = await service.search(ParsedQuery(category="dentists", location="austin"))

    assert searched == 2
    assert len(results) == 1
    assert results[0].url == "https://same.example/profile"


@pytest.mark.anyio
async def test_collector_uses_bounded_concurrency(monkeypatch) -> None:
    service = CollectorService()
    active = 0
    max_active = 0

    async def fake_collect_one(result, parsed_query):
        nonlocal active, max_active
        active += 1
        max_active = max(max_active, active)
        await asyncio.sleep(0.01)
        active -= 1
        return ExtractedBusiness(name=result.title)

    monkeypatch.setattr("backend.services.collector.get_settings", lambda: SimpleNamespace(argus_max_concurrency=2))
    service.collect_one = fake_collect_one
    results = [SearchResult(title=str(index), url=f"https://example.com/{index}", source="Fake") for index in range(6)]

    collected = await service.collect(results, ParsedQuery(category="x", location="y"))

    assert len(collected) == 6
    assert max_active <= 2


@pytest.mark.anyio
async def test_collection_failure_continues_pipeline(monkeypatch) -> None:
    service = CollectorService()
    failures = []

    async def fake_collect_one(result, parsed_query):
        if "bad" in result.url:
            raise RuntimeError("boom")
        return ExtractedBusiness(name="Good")

    async def on_failure(result):
        failures.append(result.url)

    monkeypatch.setattr("backend.services.collector.get_settings", lambda: SimpleNamespace(argus_max_concurrency=2))
    service.collect_one = fake_collect_one
    results = [
        SearchResult(title="bad", url="https://bad.example", source="Fake"),
        SearchResult(title="good", url="https://good.example", source="Fake"),
    ]

    collected = await service.collect(results, ParsedQuery(category="x", location="y"), on_failure=on_failure)

    assert len(collected) == 1
    assert failures == ["https://bad.example"]


def test_extraction_helpers_find_required_fields() -> None:
    text = (
        "Call (205) 555-0199 or email care@example.com. "
        "Mon-Fri 8am-5pm. Rating 4.7 stars from 1,245 reviews. "
        "https://facebook.com/example https://cdn.example.com/photo.jpg"
    )

    assert first_match(PHONE_RE, text) == "(205) 555-0199"
    assert first_match(EMAIL_RE, text) == "care@example.com"
    assert first_match(HOURS_RE, text)
    assert extract_rating(text) == "4.7"
    assert extract_review_count(text) == "1245"
    assert "facebook.com/example" in extract_links(SOCIAL_LINK_RE, text)
    assert "photo.jpg" in extract_links(IMAGE_URL_RE, text)


@pytest.mark.anyio
async def test_durable_cache_hit_and_miss() -> None:
    init_db()
    query = "Cardiologists in Chennai"
    db = SessionLocal()
    try:
        parsed = research_service.scout.parse_query(query)
        cache_key = research_service._cache_key(parsed.category, parsed.location, True, True, "offline")
        db.execute(delete(ResearchCache).where(ResearchCache.cache_key == cache_key))
        db.commit()

        first = research_service.start(db, query, "offline")
        assert not research_service.is_cache_hit(first.id)
        await research_service.run(first.id)
        db.close()
        db = SessionLocal()

        second = research_service.start(db, query, "offline")

        assert second.id == first.id
        assert research_service.is_cache_hit(second.id)
        assert research_service.cache_metadata(second.id)["cache_hit"] is True
    finally:
        db.close()


@pytest.mark.anyio
async def test_zero_business_completed_session_is_not_cache_hit() -> None:
    init_db()
    query = f"Cache Poison {uuid4().hex[:8]} in Chennai"
    db = SessionLocal()
    try:
        first = research_service.start(db, query, "offline")
        first.category = research_service.scout.parse_query(query).category
        first.location = research_service.scout.parse_query(query).location
        first.status = "complete"
        first.businesses_found = 0
        research_service._store_cache(db, first)
        db.commit()
        first_id = first.id

        second = research_service.start(db, query, "offline")

        assert second.id != first_id
        assert not research_service.is_cache_hit(second.id)
    finally:
        db.close()


@pytest.mark.anyio
async def test_real_mode_without_providers_does_not_fabricate(monkeypatch) -> None:
    service = SearchService()
    service.providers = []
    monkeypatch.setattr(
        "backend.services.search.get_settings",
        lambda: SimpleNamespace(
            argus_demo_mode=False,
            argus_max_source_targets=2,
            argus_max_results_per_source=10,
        ),
    )

    results, searched = await service.search(ParsedQuery(category="dentists", location="austin"))

    assert results == []
    assert searched == 0
