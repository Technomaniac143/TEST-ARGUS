from statistics import mean


class MarketClusteringService:
    """Rule-based market clustering and position analysis."""

    def attach(self, businesses: list[dict[str, object]], review_queue: list[dict[str, object]]) -> list[dict[str, object]]:
        review_names = {str(item.get("business_name")) for item in review_queue}
        for business in businesses:
            business["market_cluster"] = self.cluster_name(business, review_names)
        self._positions(businesses, review_names)
        return self.clusters(businesses)

    def cluster_name(self, business: dict[str, object], review_names: set[str]) -> str:
        flags = set(business.get("analyst_quality_flags", []))
        dna = float(business.get("dna_score") or 0)
        certs = self._field_count(business, "certifications")
        reviews = int(self._first(business, "review_count") or 0)
        if business.get("name") in review_names or "NEEDS_HUMAN_REVIEW" in flags:
            return "Review Required"
        if dna >= 88 and certs and reviews >= 100:
            return "Premium Providers"
        if dna >= 75 and certs:
            return "Independent Specialists"
        if dna < 65 or "WEAK_SOURCE_COVERAGE" in flags:
            return "Weak Coverage"
        return "Small Clinics"

    def clusters(self, businesses: list[dict[str, object]]) -> list[dict[str, object]]:
        names = ["Premium Providers", "Independent Specialists", "Small Clinics", "Weak Coverage", "Review Required"]
        result = []
        for name in names:
            members = [item for item in businesses if item.get("market_cluster") == name]
            result.append(
                {
                    "cluster_name": name,
                    "members": [item.get("name") for item in members],
                    "cluster_metrics": {
                        "count": len(members),
                        "average_dna": round(mean([float(item.get("dna_score") or 0) for item in members]), 1) if members else 0,
                    },
                }
            )
        return result

    def outliers(self, businesses: list[dict[str, object]], review_queue: list[dict[str, object]]) -> dict[str, list[dict[str, str]]]:
        review_names = {str(item.get("business_name")) for item in review_queue}
        output: dict[str, list[dict[str, str]]] = {}
        for business in businesses:
            reasons = []
            flags = set(business.get("analyst_quality_flags", []))
            if "WEAK_SOURCE_COVERAGE" in flags:
                reasons.append(("weak source coverage", "MEDIUM", "Add stronger official or registry evidence."))
            if len(business.get("conflicts", [])) >= 2:
                reasons.append(("high conflicts", "HIGH", "Resolve contradictory values manually."))
            if self._field_count(business, "certifications") == 0:
                reasons.append(("missing certifications", "MEDIUM", "Verify certification or registry status."))
            if int(self._first(business, "review_count") or 0) < 20:
                reasons.append(("few reviews", "LOW", "Treat popularity signals as limited."))
            if float(business.get("dna_score") or 0) < 65:
                reasons.append(("low DNA", "HIGH", "Review before use."))
            if business.get("name") in review_names:
                reasons.append(("human review required", "HIGH", "Assign to reviewer."))
            output[str(business.get("name"))] = [
                {"outlier_reason": reason, "severity": severity, "recommended_action": action}
                for reason, severity, action in reasons
            ]
        return output

    def market_overview(self, businesses: list[dict[str, object]], clusters: list[dict[str, object]], review_queue: list[dict[str, object]], common_services: list[str], common_specialties: list[str]) -> dict[str, object]:
        source_scores = [float(e.get("reliability_score") or 0) for b in businesses for e in b.get("evidence", [])]
        top_cluster = max(clusters, key=lambda item: item["cluster_metrics"]["count"], default={"cluster_name": "None"})
        return {
            "total_businesses": len(businesses),
            "premium_providers": self._cluster_count(clusters, "Premium Providers"),
            "independent_specialists": self._cluster_count(clusters, "Independent Specialists"),
            "review_required": len(review_queue),
            "high_confidence_businesses": sum(1 for b in businesses if b.get("confidence_label") == "HIGH"),
            "weak_businesses": sum(1 for b in businesses if b.get("market_cluster") == "Weak Coverage"),
            "average_dna": round(mean([float(b.get("dna_score") or 0) for b in businesses]), 1) if businesses else 0,
            "average_source_reliability": round(mean(source_scores), 1) if source_scores else 0,
            "top_cluster": top_cluster.get("cluster_name"),
            "most_common_specialties": common_specialties,
            "most_common_services": common_services,
        }

    def _positions(self, businesses: list[dict[str, object]], review_names: set[str]) -> None:
        raw = []
        for business in businesses:
            score = (
                float(business.get("dna_score") or 0) * 0.55
                + self._avg_reliability(business) * 0.2
                + int(business.get("dna_breakdown", {}).get("evidence_strength", 0)) * 0.15
                - len(business.get("conflicts", [])) * 5
                - (10 if business.get("name") in review_names else 0)
            )
            raw.append((business, max(0, min(100, round(score)))))
        ranked = sorted(raw, key=lambda item: item[1], reverse=True)
        total = max(len(ranked), 1)
        for index, (business, score) in enumerate(ranked, start=1):
            percentile = round(((total - index + 1) / total) * 100)
            business["percentile_score"] = score
            business["market_position"] = self._position(percentile, score)

    def _position(self, percentile: int, score: int) -> str:
        if percentile >= 95 or score >= 92:
            return "TOP_5_PERCENT"
        if percentile >= 90 or score >= 86:
            return "TOP_10_PERCENT"
        if score >= 75:
            return "ABOVE_AVERAGE"
        if score >= 60:
            return "AVERAGE"
        return "WEAK"

    def _first(self, business: dict[str, object], field: str) -> str:
        for item in business.get("evidence", []):
            if item.get("field") == field:
                return str(item.get("value") or "")
        return "0"

    def _field_count(self, business: dict[str, object], field: str) -> int:
        return sum(1 for item in business.get("evidence", []) if item.get("field") == field)

    def _avg_reliability(self, business: dict[str, object]) -> float:
        scores = [float(item.get("reliability_score") or 0) for item in business.get("evidence", [])]
        return mean(scores) if scores else 0

    def _cluster_count(self, clusters: list[dict[str, object]], name: str) -> int:
        for cluster in clusters:
            if cluster.get("cluster_name") == name:
                return int(cluster.get("cluster_metrics", {}).get("count", 0))
        return 0
