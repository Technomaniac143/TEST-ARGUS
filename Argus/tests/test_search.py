import pytest

from backend.agents.scout import ScoutAgent
from backend.services.search import SearchService


@pytest.mark.anyio
async def test_search_service_returns_mock_fallback_results() -> None:
    parsed = ScoutAgent().parse_query("Cardiologists in Birmingham")
    service = SearchService()
    service.providers = []

    results, searched = await service.search(parsed)

    assert searched == 1
    assert len(results) >= 3
    assert all(result.source == "Mock" for result in results)
