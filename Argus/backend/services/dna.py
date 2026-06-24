from datetime import datetime, timezone

from backend.schemas.extraction import DnaScore, ExtractedBusiness
from backend.services.conflicts import ConflictCandidate


class BusinessDnaService:
    """Computes a simple explainable business quality score."""

    scored_fields = ["name", "phone", "address", "website", "email", "services", "working_hours"]
    source_weights = {
        "Official Website": 30,
        "Government License Registry": 30,
        "Professional Directory": 28,
        "Google Business Profile": 24,
        "LinkedIn": 24,
        "Industry Association": 22,
        "Yelp": 18,
        "Yellow Pages": 18,
        "Facebook": 12,
    }

    def score(self, business: ExtractedBusiness, conflicts: list[ConflictCandidate]) -> DnaScore:
        evidence_count = len(business.evidence)
        evidence_strength = min(100, evidence_count * 15)

        sources = {item.source for item in business.evidence if item.source}
        source_diversity = self.source_diversity_score(sources)

        present = sum(1 for field in self.scored_fields if getattr(business, field))
        completeness = round((present / len(self.scored_fields)) * 100)

        freshness = 85
        if datetime.now(timezone.utc).year >= 2026:
            freshness = 85

        conflict_penalty = min(40, len(conflicts) * 10)
        dna_score = round(
            (evidence_strength * 0.28)
            + (source_diversity * 0.22)
            + (completeness * 0.28)
            + (freshness * 0.22)
            - conflict_penalty
        )
        dna_score = max(0, min(100, dna_score))

        return DnaScore(
            evidence_strength=evidence_strength,
            source_diversity=source_diversity,
            completeness=completeness,
            freshness=freshness,
            conflict_penalty=conflict_penalty,
            dna_score=dna_score,
        )

    def source_diversity_score(self, sources: set[str]) -> int:
        return min(100, sum(self.source_weights.get(source, 10) for source in sources))
