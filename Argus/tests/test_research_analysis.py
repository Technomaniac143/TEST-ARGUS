from types import SimpleNamespace

from backend.services.evidence_graph import EvidenceGraphService
from backend.services.review import ResearchReviewService


def evidence(field, value, source="Official Website", reliability_score=95):
    return {
        "field": field,
        "value": value,
        "source": source,
        "reliability_score": reliability_score,
    }


def conflict(field="phone"):
    return SimpleNamespace(
        field=field,
        value1="205-111-1111",
        value2="205-222-2222",
        source1="Official Website",
        source2="Yelp",
    )


def business(**overrides):
    base = {
        "name": "Birmingham Heart Associates",
        "category": "cardiologists",
        "phone": "205-111-1111",
        "website": "https://heart.example",
        "dna_score": 90,
        "evidence": [
            evidence("phone", "205-111-1111"),
            evidence("address", "100 Market St"),
            evidence("license_information", "AL-100"),
        ],
        "conflicts": [],
    }
    base.update(overrides)
    return base


def test_evidence_graph_structure() -> None:
    graph = EvidenceGraphService().build(
        SimpleNamespace(id=1, name="Example"),
        [
            SimpleNamespace(field="phone", value="205-111-1111", source="Official Website"),
        ],
        [],
    )

    assert any(node["type"] == "business" for node in graph["nodes"])
    assert {"from": "business:1", "to": "field:1:phone", "label": "HAS_FIELD"} in graph["edges"]
    assert any(edge["label"] == "SUPPORTED_BY" for edge in graph["edges"])


def test_conflict_graph_edge() -> None:
    graph = EvidenceGraphService().build(SimpleNamespace(id=1, name="Example"), [], [conflict()])

    assert any(node["type"] == "conflict" for node in graph["nodes"])
    assert any(edge["label"] == "CONFLICTS_WITH" for edge in graph["edges"])


def test_contradiction_severity_classification() -> None:
    service = ResearchReviewService()

    assert service.conflict_severity("phone") == "HIGH"
    assert service.conflict_severity("website") == "MEDIUM"
    assert service.conflict_severity("rating") == "LOW"


def test_review_queue_inclusion_rules() -> None:
    review = ResearchReviewService().review_queue(
        [
            business(conflicts=[conflict()]),
            business(name="Weak", dna_score=50, evidence=[evidence("phone", "1", reliability_score=60)]),
            business(name="Missing License", evidence=[evidence("phone", "1")]),
        ]
    )

    names = {item["business_name"] for item in review}
    assert "Birmingham Heart Associates" in names
    assert "Weak" in names
    assert "Missing License" in names


def test_analyst_quality_flags() -> None:
    service = ResearchReviewService()

    flags = service.quality_flags(business(conflicts=[conflict()], dna_score=60, website=None))

    assert "CONFLICT_DETECTED" in flags
    assert "NEEDS_HUMAN_REVIEW" in flags
    assert "CONTACT_INCOMPLETE" in flags


def test_export_payloads_include_new_fields() -> None:
    payload = business()
    payload["evidence_graph"] = {"nodes": [], "edges": []}
    payload["analyst_quality_flags"] = ["HIGHLY_VERIFIED"]
    report = {
        "contradiction_map": [],
        "review_queue": [],
    }

    assert "evidence_graph" in payload
    assert "analyst_quality_flags" in payload
    assert "contradiction_map" in report
    assert "review_queue" in report
