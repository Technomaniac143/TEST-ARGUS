from backend.schemas.extraction import ExtractedBusiness, FieldEvidence
from backend.services.deduplication import DeduplicationService


def test_deduplicate_by_phone_and_preserve_evidence() -> None:
    records = [
        ExtractedBusiness(
            name="ABC Heart Clinic",
            phone="205-111-1111",
            evidence=[FieldEvidence(field="phone", value="205-111-1111", source="Website")],
        ),
        ExtractedBusiness(
            name="ABC Heart Specialists",
            phone="(205) 111-1111",
            evidence=[FieldEvidence(field="name", value="ABC Heart Specialists", source="Directory")],
        ),
    ]

    deduped, duplicates_removed = DeduplicationService().deduplicate(records)

    assert len(deduped) == 1
    assert duplicates_removed == 1
    assert len(deduped[0].evidence) == 2
