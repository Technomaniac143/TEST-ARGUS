from backend.models.business import Business
from backend.models.conflict import Conflict
from backend.models.evidence import Evidence


RECOMMENDATION_RANK = {
    "STRONGLY_RECOMMENDED": 0,
    "RECOMMENDED": 1,
    "REVIEW_REQUIRED": 2,
    "NOT_RECOMMENDED": 3,
}


class JudgeRecommendationService:
    """Deterministic recommendation engine for ranked business intelligence output."""

    critical_fields = ["phone", "address", "website"]

    def recommend(
        self,
        business: Business,
        evidence: list[Evidence],
        conflicts: list[Conflict],
        reliability: str,
    ) -> dict[str, str]:
        missing = [field for field in self.critical_fields if not getattr(business, field)]
        evidence_count = len(evidence)
        dna_score = business.dna_score

        if dna_score >= 90 and not conflicts and evidence_count >= 12 and not missing and reliability == "HIGH":
            recommendation = "STRONGLY_RECOMMENDED"
            reason = "High DNA score, strong evidence coverage, no conflicts, and complete critical fields."
        elif dna_score >= 75 and len(conflicts) <= 1 and evidence_count >= 6 and len(missing) <= 1:
            recommendation = "RECOMMENDED"
            reason = "Solid DNA score and usable evidence coverage with limited review risk."
        elif dna_score >= 55 and evidence_count >= 3:
            recommendation = "REVIEW_REQUIRED"
            reason = "Record has enough signal to inspect, but conflicts or missing critical fields require review."
        else:
            recommendation = "NOT_RECOMMENDED"
            reason = "Weak evidence coverage or low DNA score makes this record unreliable."

        return {
            "recommendation": recommendation,
            "reason": reason,
            "risk_level": self._risk_level(dna_score, len(conflicts), missing),
            "confidence_label": self._confidence_label(business.confidence),
        }

    def sort_key(self, payload: dict[str, object]) -> tuple[int, float, int, int]:
        return (
            RECOMMENDATION_RANK.get(str(payload["recommendation"]), 99),
            -float(payload["dna_score"]),
            len(payload["conflicts"]),
            -int(payload["dna_breakdown"].get("evidence_strength", 0)),
        )

    def _risk_level(self, dna_score: float, conflict_count: int, missing: list[str]) -> str:
        if conflict_count >= 2 or dna_score < 55 or len(missing) >= 2:
            return "HIGH"
        if conflict_count == 1 or dna_score < 75 or missing:
            return "MEDIUM"
        return "LOW"

    def _confidence_label(self, confidence: float) -> str:
        if confidence >= 85:
            return "HIGH"
        if confidence >= 65:
            return "MEDIUM"
        return "LOW"
