import pytest

from backend.agents.scout import ScoutAgent
from backend.offline_corpus.corpus import ensure_offline_corpus, search_offline
from backend.schemas.search import ParsedQuery
from backend.services.collector import CollectorService
from backend.services.search import SearchService


def test_offline_corpus_returns_competition_volume() -> None:
    parsed = ScoutAgent().parse_query("Cardiologists in Birmingham")

    results = search_offline(parsed, limit=200)

    assert len(results) >= 20
    assert {result.source for result in results} >= {
        "Official Website",
        "Google Business Profile",
        "Government License Registry",
    }
    assert all(result.url.startswith("offline://") for result in results)


@pytest.mark.anyio
async def test_offline_collector_extracts_from_local_page() -> None:
    ensure_offline_corpus()
    parsed = ParsedQuery(category="roofing contractors", location="dallas")
    result = search_offline(parsed, source_type="official_website", limit=1)[0]

    business = await CollectorService().collect_one(result, parsed)

    assert business.name
    assert business.phone
    assert business.address
    assert business.website
    assert any(item.field == "license_information" for item in business.evidence)


@pytest.mark.anyio
async def test_offline_search_service_uses_corpus(monkeypatch) -> None:
    monkeypatch.setattr(
        "backend.services.search.get_settings",
        lambda: type(
            "Settings",
            (),
            {
                "argus_offline_mode": True,
                "argus_demo_mode": True,
                "enable_live_search": False,
                "argus_max_source_targets": 5,
                "argus_max_results_per_source": 10,
            },
        )(),
    )

    service = SearchService()
    results, searched = await service.search(ParsedQuery(category="dentists", location="austin"))

    assert searched >= 1
    assert len(results) >= 20
    assert all(result.url.startswith("offline://") for result in results)
