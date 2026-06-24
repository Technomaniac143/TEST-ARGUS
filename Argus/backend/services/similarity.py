from rapidfuzz import fuzz


class BusinessSimilarityService:
    """Deterministic pairwise business similarity scoring."""

    def attach(self, businesses: list[dict[str, object]]) -> None:
        for business in businesses:
            scored = []
            for other in businesses:
                if business.get("id") == other.get("id"):
                    continue
                score = self.score(business, other)
                scored.append({"business_name": other.get("name"), "score": score})
            business["similar_businesses"] = sorted(scored, key=lambda item: item["score"], reverse=True)[:5]

    def score(self, left: dict[str, object], right: dict[str, object]) -> int:
        services = self._jaccard(self._values(left, "services"), self._values(right, "services")) * 30
        specialties = self._jaccard(self._values(left, "specialties"), self._values(right, "specialties")) * 25
        certs = self._jaccard(self._values(left, "certifications"), self._values(right, "certifications")) * 20
        flags = self._jaccard(set(left.get("analyst_quality_flags", [])), set(right.get("analyst_quality_flags", []))) * 10
        reliability = max(0, 100 - abs(self._avg_reliability(left) - self._avg_reliability(right))) / 100 * 10
        rating = fuzz.ratio(self._first(left, "rating"), self._first(right, "rating")) / 100 * 5
        return round(services + specialties + certs + flags + reliability + rating)

    def _values(self, business: dict[str, object], field: str) -> set[str]:
        values: set[str] = set()
        for item in business.get("evidence", []):
            if item.get("field") == field:
                values.update(part.strip().lower() for part in str(item.get("value") or "").split(",") if part.strip())
        return values

    def _first(self, business: dict[str, object], field: str) -> str:
        for item in business.get("evidence", []):
            if item.get("field") == field:
                return str(item.get("value") or "")
        return ""

    def _avg_reliability(self, business: dict[str, object]) -> float:
        scores = [float(item.get("reliability_score") or 0) for item in business.get("evidence", [])]
        return sum(scores) / len(scores) if scores else 0

    def _jaccard(self, left: set[str], right: set[str]) -> float:
        if not left and not right:
            return 0
        return len(left & right) / max(len(left | right), 1)
