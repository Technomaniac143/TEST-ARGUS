import pytest

from backend.agents.scout import ScoutAgent
from backend.data.demo_businesses import demo_search_results, get_demo_business
from backend.services.collector import CollectorService
from backend.services.conflicts import ConflictDetectionService
from backend.services.deduplication import DeduplicationService
from backend.services.dna import BusinessDnaService
from backend.services.search import DemoSearchProvider


def test_demo_dataset_selection_returns_eight_plus_businesses() -> None:
    parsed = ScoutAgent().parse_query("Roofing contractors in Dallas")

    results = demo_search_results(parsed)

    assert len(results) >= 8
    assert results[0][1].startswith("demo://roofing contractors/dallas/")


@pytest.mark.anyio
async def test_demo_search_provider_uses_clean_source_label() -> None:
    parsed = ScoutAgent().parse_query("Cardiologists in Birmingham")

    results = await DemoSearchProvider().search(parsed)

    assert results
    assert results[0].source == "ARGUS Demo Dataset"
    assert results[0].source != "Mock"


@pytest.mark.anyio
async def test_demo_collector_returns_source_diverse_evidence() -> None:
    parsed = ScoutAgent().parse_query("Cardiologists in Birmingham")
    result = (await DemoSearchProvider().search(parsed))[0]

    business = await CollectorService().collect_one(result, parsed)
    sources = {item.source for item in business.evidence}

    assert "Official Website" in sources
    assert "Google Business Profile" in sources
    assert "Government License Registry" in sources
    assert "Mock" not in sources


@pytest.mark.anyio
async def test_demo_duplicate_edge_case_is_removed() -> None:
    parsed = ScoutAgent().parse_query("Dentists in Austin")
    search_results = await DemoSearchProvider().search(parsed)
    records = [get_demo_business(result.url) for result in search_results]
    records = [record for record in records if record is not None]

    deduped, duplicates_removed = DeduplicationService().deduplicate(records)

    assert len(records) >= 9
    assert duplicates_removed >= 1
    assert len(deduped) >= 8


@pytest.mark.anyio
async def test_demo_conflict_edge_case_is_detected() -> None:
    parsed = ScoutAgent().parse_query("Plumbers in Houston")
    search_results = await DemoSearchProvider().search(parsed)
    records = [get_demo_business(result.url) for result in search_results]
    records = [record for record in records if record is not None]

    conflicts = [ConflictDetectionService().detect(record) for record in records]

    assert any(items for items in conflicts)


def test_source_diversity_scoring_uses_source_class_weights() -> None:
    service = BusinessDnaService()

    strong = service.source_diversity_score(
        {"Official Website", "Government License Registry", "Professional Directory"}
    )
    weak = service.source_diversity_score({"Facebook", "Yellow Pages"})

    assert strong > weak
    assert strong >= 80
