import asyncio

import pytest

from backend.adapters import default_adapters
from backend.adapters.avvo_adapter import AvvoAdapter
from backend.adapters.base_adapter import SourceAdapter
from backend.adapters.bbb_adapter import BbbAdapter
from backend.adapters.justdial_adapter import JustdialAdapter
from backend.adapters.practo_adapter import PractoAdapter
from backend.schemas.search import ParsedQuery, SearchResult, SourceTarget
from backend.services.search import SearchService


def test_every_adapter_exposes_contract() -> None:
    adapters = default_adapters()

    assert len(adapters) >= 15
    for adapter in adapters:
        assert hasattr(adapter, "discover")
        assert hasattr(adapter, "collect")
        assert hasattr(adapter, "health")
        assert adapter.adapter_name
        assert adapter.source_type


def test_pagination_query_generation() -> None:
    adapter = JustdialAdapter()
    parsed = ParsedQuery(category="plumbers", location="Coimbatore")
    target = SourceTarget(source_type="directory", label="Justdial", query="site:justdial.com plumbers Coimbatore")

    assert "page 2" in adapter.query_for(parsed, target, page=2)
    assert "site:justdial.com" in adapter.query_for(parsed, target, page=1)


def test_adapter_health_tracks_failures_timeouts_and_blocked() -> None:
    adapter = SourceAdapter("Test Adapter", "directory", "example.com")

    adapter._record("success", 0)
    adapter._record("failure", 0)
    adapter._record("timeout", 0)
    adapter._record("blocked", 0)

    health = adapter.health()
    assert health["success_count"] == 1
    assert health["failure_count"] == 1
    assert health["timeout_count"] == 1
    assert health["blocked_count"] == 1
    assert health["health_score"] < 100


def test_blocked_page_detection() -> None:
    adapter = SourceAdapter("Test Adapter", "directory", "example.com")

    assert adapter._blocked("<html>Access denied. Verify you are human.</html>")


def test_practo_source_specific_extraction() -> None:
    fields = asyncio.run(PractoAdapter().collect(
        """
        <html><body>
        Doctor: Dr. Priya Raman
        Speciality: Cardiologist
        Experience: 18 years
        Clinic: Chennai Heart Centre
        Timings: Mon-Fri 9am-5pm
        </body></html>
        """,
        "https://practo.com/chennai/doctor",
    ))

    assert fields["doctor"] == "Dr. Priya Raman"
    assert fields["speciality"] == "Cardiologist"
    assert fields["clinic"] == "Chennai Heart Centre"


def test_justdial_source_specific_extraction() -> None:
    fields = asyncio.run(JustdialAdapter().collect(
        "<html><body>Phone: 044-5555-0101\nAddress: Anna Salai, Chennai\nRating: 4.6</body></html>",
        "https://justdial.com/chennai/plumber",
    ))

    assert fields["phone"] == "044-5555-0101"
    assert fields["address"] == "Anna Salai, Chennai"
    assert fields["rating"] == "4.6"


def test_avvo_and_bbb_source_specific_extraction() -> None:
    avvo = asyncio.run(AvvoAdapter().collect(
        "<html><body>Practice areas: Family Law\nLicense status: Active</body></html>",
        "https://avvo.com/attorney",
    ))
    bbb = asyncio.run(BbbAdapter().collect(
        "<html><body>Accreditation: BBB Accredited Business\nRating: A+</body></html>",
        "https://bbb.org/profile",
    ))

    assert avvo["practice_areas"] == "Family Law"
    assert avvo["license_status"] == "Active"
    assert bbb["accreditation"] == "BBB Accredited Business"


def test_search_service_selects_source_specific_adapters() -> None:
    service = SearchService()
    target = SourceTarget(source_type="healthcare_directory", label="Practo", query="site:practo.com cardiologists Chennai")

    adapters = service._adapters_for_target(target)

    assert any(adapter.adapter_name == "Practo" for adapter in adapters)


def test_search_result_deduplication_keeps_adapter_metadata() -> None:
    service = SearchService()
    results = service._dedupe_and_filter(
        [
            SearchResult(
                title="A",
                url="https://example.com/?utm_source=x",
                source="Official Website",
                source_type="official_website",
                adapter_name="Official Website",
                confidence=88,
                adapter_health=100,
                metadata={"page": 1},
            ),
            SearchResult(
                title="A duplicate",
                url="https://example.com/",
                source="Official Website",
                source_type="official_website",
                adapter_name="Official Website",
                confidence=88,
                adapter_health=100,
                metadata={"page": 2},
            ),
        ]
    )

    assert len(results) == 1
    assert results[0].adapter_name == "Official Website"
