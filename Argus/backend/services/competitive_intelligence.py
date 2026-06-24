from statistics import mean


class CompetitiveIntelligenceService:
    """Rule-based competitive intelligence for each business and session."""

    regulated_terms = {"cardiologist", "dentist", "lawyer", "legal", "hospital", "physiotherapist"}

    def attach(self, businesses: list[dict[str, object]], review_queue: list[dict[str, object]]) -> dict[str, object]:
        review_names = {str(item.get("business_name")) for item in review_queue}
        for business in businesses:
            intelligence = self.business_intelligence(business, business.get("name") in review_names)
            business["competitive_intelligence"] = intelligence
        return self.market_comparison(businesses)

    def business_intelligence(self, business: dict[str, object], in_review_queue: bool = False) -> dict[str, object]:
        strengths = self.strengths(business)
        weaknesses = self.weaknesses(business)
        opportunity_gaps = self.opportunity_gaps(business)
        risk_factors = self.risk_factors(business, in_review_queue)
        evidence_gaps = self.evidence_gaps(business)
        return {
            "strengths": strengths,
            "weaknesses": weaknesses,
            "opportunity_gaps": opportunity_gaps,
            "risk_factors": risk_factors,
            "evidence_gaps": evidence_gaps,
            "differentiation_summary": self.differentiation_summary(business, strengths, weaknesses, risk_factors),
        }

    def strengths(self, business: dict[str, object]) -> list[str]:
        output: list[str] = []
        if float(business.get("dna_score") or 0) >= 85:
            output.append("High Business DNA score")
        if int(business.get("dna_breakdown", {}).get("source_diversity", 0)) >= 80:
            output.append("Strong source diversity")
        for field in ["phone", "address", "license_information"]:
            if self._has_field(business, field):
                output.append(f"Verified {field.replace('_', ' ')}")
        if float(self._first(business, "rating") or 0) >= 4.5:
            output.append("High public rating")
        if int(self._first(business, "review_count") or 0) >= 100:
            output.append("High review volume")
        if self._has_field(business, "certifications"):
            output.append("Certifications present")
        if not business.get("conflicts"):
            output.append("Few or no conflicts")
        return output or ["Basic evidence coverage present"]

    def weaknesses(self, business: dict[str, object]) -> list[str]:
        output: list[str] = []
        if not business.get("website"):
            output.append("Missing website")
        if not business.get("phone"):
            output.append("Missing phone")
        if not business.get("email"):
            output.append("Missing email")
        if "WEAK_SOURCE_COVERAGE" in business.get("analyst_quality_flags", []):
            output.append("Weak source coverage")
        if float(business.get("dna_score") or 0) < 65:
            output.append("Low Business DNA score")
        if int(self._first(business, "review_count") or 0) < 20:
            output.append("Low review count")
        if self._regulated(business) and not self._has_field(business, "license_information"):
            output.append("License missing for regulated category")
        if business.get("conflicts"):
            output.append("Conflicts present")
        return output

    def opportunity_gaps(self, business: dict[str, object]) -> list[str]:
        gaps: list[str] = []
        if not self._has_field(business, "social_profiles"):
            gaps.append("Missing social profiles")
        if not self._has_field(business, "working_hours"):
            gaps.append("Missing working hours")
        if not self._has_field(business, "certifications"):
            gaps.append("Missing certifications")
        if not self._has_field(business, "images_urls"):
            gaps.append("Missing images")
        if not business.get("website"):
            gaps.append("No official website")
        if len({item.get("source") for item in business.get("evidence", [])}) < 3:
            gaps.append("Weak directory presence")
        return gaps

    def risk_factors(self, business: dict[str, object], in_review_queue: bool = False) -> list[str]:
        risks: list[str] = []
        if any(self._value(conflict, "field") in {"phone", "address", "license_information"} for conflict in business.get("conflicts", [])):
            risks.append("High severity conflict")
        if in_review_queue or "NEEDS_HUMAN_REVIEW" in business.get("analyst_quality_flags", []):
            risks.append("Human review queue item")
        if self._average_reliability(business) < 70:
            risks.append("Source reliability below 70")
        if self._regulated(business) and not self._has_field(business, "license_information"):
            risks.append("Missing license in regulated category")
        if not business.get("phone") or not business.get("website"):
            risks.append("Contact information incomplete")
        return risks

    def evidence_gaps(self, business: dict[str, object]) -> list[str]:
        expected = ["phone", "address", "website", "email", "working_hours", "license_information", "certifications"]
        return [field for field in expected if not self._has_field(business, field) and not business.get(field)]

    def market_comparison(self, businesses: list[dict[str, object]]) -> dict[str, object]:
        if not businesses:
            return {}
        return {
            "strongest_business": max(businesses, key=lambda item: float(item.get("dna_score") or 0)).get("name"),
            "weakest_business": min(businesses, key=lambda item: float(item.get("dna_score") or 0)).get("name"),
            "highest_rated": max(businesses, key=lambda item: float(self._first(item, "rating") or 0)).get("name"),
            "most_verified": max(businesses, key=lambda item: len(item.get("evidence", []))).get("name"),
            "most_conflicted": max(businesses, key=lambda item: len(item.get("conflicts", []))).get("name"),
            "best_source_coverage": max(businesses, key=self._average_reliability).get("name"),
            "strongest_cluster": self._cluster_extreme(businesses, strongest=True),
            "weakest_cluster": self._cluster_extreme(businesses, strongest=False),
        }

    def differentiation_summary(self, business: dict[str, object], strengths: list[str], weaknesses: list[str], risks: list[str]) -> str:
        name = business.get("name") or "This business"
        if risks:
            return f"{name} has useful market signals but needs review because {risks[0].lower()}."
        if strengths and not weaknesses:
            return f"{name} stands out with {strengths[0].lower()} and clean evidence coverage."
        if strengths:
            return f"{name} is competitive due to {strengths[0].lower()}, with improvement opportunities around {', '.join(weaknesses[:2]).lower() or 'coverage depth'}."
        return f"{name} has limited differentiation and should be compared carefully against stronger verified competitors."

    def _cluster_extreme(self, businesses: list[dict[str, object]], strongest: bool) -> str | None:
        clusters: dict[str, list[float]] = {}
        for business in businesses:
            clusters.setdefault(str(business.get("market_cluster") or "Unassigned"), []).append(float(business.get("dna_score") or 0))
        scored = [(cluster, mean(scores)) for cluster, scores in clusters.items()]
        return (max if strongest else min)(scored, key=lambda item: item[1])[0] if scored else None

    def _first(self, business: dict[str, object], field: str) -> str:
        for item in business.get("evidence", []):
            if item.get("field") == field:
                return str(item.get("value") or "")
        return ""

    def _has_field(self, business: dict[str, object], field: str) -> bool:
        return any(item.get("field") == field and item.get("value") for item in business.get("evidence", []))

    def _average_reliability(self, business: dict[str, object]) -> float:
        scores = [float(item.get("reliability_score") or 0) for item in business.get("evidence", [])]
        return mean(scores) if scores else 0

    def _regulated(self, business: dict[str, object]) -> bool:
        category = str(business.get("category") or "").lower()
        return any(term in category for term in self.regulated_terms)

    def _value(self, obj: object, key: str) -> str:
        if isinstance(obj, dict):
            return str(obj.get(key) or "")
        return str(getattr(obj, key, ""))
