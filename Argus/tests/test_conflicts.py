from backend.schemas.extraction import ExtractedBusiness, FieldEvidence
from backend.services.conflicts import ConflictDetectionService


def test_conflict_detection_preserves_different_phone_values() -> None:
    business = ExtractedBusiness(
        name="Southern Pulse Cardiology",
        evidence=[
            FieldEvidence(field="phone", value="205-555-0267", source="Website"),
            FieldEvidence(field="phone", value="205-555-0299", source="Directory"),
        ],
    )

    conflicts = ConflictDetectionService().detect(business)

    assert len(conflicts) == 1
    assert conflicts[0].field == "phone"
    assert conflicts[0].value1 == "205-555-0267"
    assert conflicts[0].value2 == "205-555-0299"
