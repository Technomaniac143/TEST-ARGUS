from sqlalchemy.orm import Session

from backend.models.business import Business
from backend.models.conflict import Conflict
from backend.models.evidence import Evidence
from backend.schemas.extraction import ExtractedBusiness
from backend.services.conflicts import ConflictCandidate


class VerificationService:
    """Persists field-level evidence and detected conflicts."""

    def store_evidence(self, db: Session, business: Business, extracted: ExtractedBusiness) -> None:
        for item in extracted.evidence:
            db.add(
                Evidence(
                    business_id=business.id,
                    field=item.field,
                    value=item.value,
                    source=item.source,
                    url=item.url,
                    normalized_url=item.normalized_url,
                    source_type=item.source_type,
                    extraction_method=item.extraction_method,
                    reliability_score=item.reliability_score,
                    crawl_status=item.crawl_status,
                )
            )

    def store_conflicts(
        self,
        db: Session,
        business: Business,
        conflicts: list[ConflictCandidate],
    ) -> None:
        for item in conflicts:
            db.add(
                Conflict(
                    business_id=business.id,
                    field=item.field,
                    value1=item.value1,
                    value2=item.value2,
                    source1=item.source1,
                    source2=item.source2,
                )
            )

    def confidence(self, extracted: ExtractedBusiness, conflict_count: int) -> float:
        fields_with_evidence = {item.field for item in extracted.evidence}
        sources = {item.source for item in extracted.evidence}
        base = min(70, len(fields_with_evidence) * 10) + min(30, len(sources) * 10)
        return max(0, min(100, base - conflict_count * 8))
