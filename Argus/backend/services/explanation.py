from collections import Counter

from backend.models.business import Business
from backend.models.conflict import Conflict
from backend.models.evidence import Evidence


class ExplanationService:
    """Builds deterministic trust explanations from evidence and conflicts."""

    def explain(
        self,
        business: Business,
        evidence: list[Evidence],
        conflicts: list[Conflict],
        dna_breakdown: dict[str, int],
    ) -> dict[str, object]:
        reliability = self.reliability(business.dna_score, len(conflicts))
        fields = Counter(item.field for item in evidence)
        source_count = len({item.source for item in evidence})

        reasons: list[str] = []
        warnings: list[str] = []

        if source_count:
            reasons.append(f"Evidence comes from {source_count} distinct source(s).")
        for field in ["phone", "address", "website", "email"]:
            if fields[field]:
                reasons.append(f"{field.title()} has {fields[field]} evidence receipt(s).")
        if dna_breakdown["completeness"] >= 70:
            reasons.append("Core business profile fields are substantially complete.")
        if not conflicts:
            reasons.append("No major conflicts were detected.")

        for conflict in conflicts:
            warnings.append(
                f"{conflict.field.title()} conflict between {conflict.source1} and {conflict.source2}."
            )
        if dna_breakdown["conflict_penalty"]:
            warnings.append(
                f"Conflict penalty reduced the score by {dna_breakdown['conflict_penalty']} point(s)."
            )

        name = business.name or "This business"
        summary = (
            f"{name} is classified as {reliability.lower()} reliability. "
            f"ARGUS found {len(evidence)} evidence receipt(s) across {source_count} source(s), "
            f"with a final Business DNA score of {round(business.dna_score)}."
        )
        summary += " Conflicting evidence was preserved for review." if conflicts else " No major conflicts were detected."

        return {
            "summary": summary,
            "reliability": reliability,
            "reasons": reasons,
            "warnings": warnings,
        }

    def reliability(self, dna_score: float, conflict_count: int) -> str:
        if conflict_count >= 2 or dna_score < 60:
            return "LOW"
        if conflict_count == 1 or dna_score < 80:
            return "MEDIUM"
        return "HIGH"
