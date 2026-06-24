import pytest

from backend.agents.scout import ScoutAgent
from backend.offline_corpus.corpus import corpus_index, search_offline
from backend.schemas.search import ParsedQuery
from backend.services.search import SearchService
from backend.services.source_planner import SourcePlannerService


def test_tamil_nadu_corpus_index_has_required_coverage() -> None:
    index = corpus_index(ParsedQuery(category="cardiologists", location="chennai"))

    assert index["support_level"] == "FULL_CORPUS_MATCH"
    assert index["tamil_nadu_supported_query_count"] >= 30
    assert "Chennai" in index["tamil_nadu_supported_cities"]
    assert "Restaurants" in index["tamil_nadu_supported_categories"]


def test_tamil_nadu_offline_search_volume() -> None:
    results = search_offline(ParsedQuery(category="plumbers", location="coimbatore"), limit=200)

    assert len(results) >= 15
    assert any(result.source == "Justdial" for result in results)
    assert any(result.source == "Sulekha" for result in results)


def test_india_specific_source_planner_output() -> None:
    targets = SourcePlannerService().plan(ParsedQuery(category="cardiologists", location="chennai"), 20)
    queries = [target.query for target in targets]

    assert any("site:justdial.com" in query for query in queries)
    assert any("site:sulekha.com" in query for query in queries)
    assert any("site:practo.com" in query for query in queries)
    assert any("site:lybrate.com" in query for query in queries)


def test_global_source_planner_accepts_non_us_location() -> None:
    targets = SourcePlannerService().plan(ParsedQuery(category="dentists", location="singapore"), 12)

    assert any("dentists in singapore" == target.query for target in targets)
    assert any("official website" in target.query for target in targets)


@pytest.mark.anyio
async def test_auto_fallback_for_chennai(monkeypatch) -> None:
    monkeypatch.setattr(
        "backend.services.search.get_settings",
        lambda: type(
            "Settings",
            (),
            {
                "argus_mode": "auto",
                "argus_offline_mode": True,
                "argus_demo_mode": False,
                "argus_max_source_queries": 0,
                "argus_max_results_per_query": 10,
            },
        )(),
    )
    service = SearchService()
    service.providers = []

    results, _ = await service.search(ParsedQuery(category="cardiologists", location="chennai"))

    assert len(results) >= 15
    assert service.last_metadata["fallback_used"] is True
    assert service.last_metadata["active_mode"] == "auto_fallback"


def test_unsupported_global_query_does_not_fabricate_offline_records() -> None:
    parsed = ScoutAgent().parse_query("Restaurants in Tokyo")

    assert parsed.category == "restaurants"
    assert parsed.location == "tokyo"
    assert search_offline(parsed, limit=200) == []
