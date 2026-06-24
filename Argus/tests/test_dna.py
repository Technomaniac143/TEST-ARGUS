from backend.schemas.extraction import ExtractedBusiness, FieldEvidence
from backend.services.dna import BusinessDnaService


def test_dna_score_returns_expected_shape() -> None:
    business = ExtractedBusiness(
        name="Birmingham Heart Specialists",
        phone="205-555-0184",
        address="2010 Brookwood Medical Center Dr",
        website="https://example.com",
        email="care@example.com",
        services="cardiology",
        working_hours="Mon-Fri 8am-5pm",
        evidence=[
            FieldEvidence(field="phone", value="205-555-0184", source="Website"),
            FieldEvidence(field="address", value="2010 Brookwood Medical Center Dr", source="Google"),
            FieldEvidence(field="website", value="https://example.com", source="LinkedIn"),
        ],
    )

    score = BusinessDnaService().score(business, conflicts=[])

    assert score.evidence_strength > 0
    assert score.source_diversity > 0
    assert score.completeness == 100
    assert 0 <= score.dna_score <= 100
