from statistics import mean


class ResearchReviewService:
    """Deterministic contradiction, review, and quality-flag analysis."""

    high_fields = {"phone", "address", "license_information"}
    medium_fields = {"working_hours", "website", "email"}

    def contradiction_map(self, businesses: list[dict[str, object]]) -> list[dict[str, object]]:
        items: list[dict[str, object]] = []
        for business in businesses:
            for conflict in business.get("conflicts", []):
                field = self._value(conflict, "field")
                severity = self.conflict_severity(field)
                items.append(
                    {
                        "business_name": business.get("name"),
                        "field": field,
                        "severity": severity,
                        "values": [self._value(conflict, "value1"), self._value(conflict, "value2")],
                        "sources": [self._value(conflict, "source1"), self._value(conflict, "source2")],
                        "recommended_action": "Manual verification required before use."
                        if severity == "HIGH"
                        else "Review before relying on this field.",
                    }
                )
        return items

    def review_queue(self, businesses: list[dict[str, object]]) -> list[dict[str, object]]:
        contradictions = self.contradiction_map(businesses)
        high_conflict_names = {
            str(item["business_name"])
            for item in contradictions
            if item["severity"] == "HIGH"
        }
        queue: list[dict[str, object]] = []
        for business in businesses:
            reasons: list[str] = []
            evidence = list(business.get("evidence", []))
            category = str(business.get("category") or "").lower()
            reliability_average = self._source_reliability_average(evidence)
            if business.get("name") in high_conflict_names:
                reasons.append("High severity contradiction detected")
            if float(business.get("dna_score") or 0) < 65:
                reasons.append("DNA score below 65")
            if not business.get("phone") and not business.get("website"):
                reasons.append("Missing phone and website")
            if ("cardiologist" in category or "dentist" in category or "lawyer" in category or "legal" in category) and not any(
                item.get("field") == "license_information" for item in evidence
            ):
                reasons.append("License missing for regulated category")
            if reliability_average < 70:
                reasons.append("Source reliability average below 70")
            if reasons:
                queue.append(
                    {
                        "business_name": business.get("name"),
                        "reason": "; ".join(reasons),
                        "severity": "HIGH" if any("High severity" in reason or "License" in reason for reason in reasons) else "MEDIUM",
                        "suggested_action": "Assign to human reviewer for source-by-source verification.",
                        "related_evidence": [
                            {
                                "field": item.get("field"),
                                "source": item.get("source"),
                                "value": item.get("value"),
                            }
                            for item in evidence[:5]
                        ],
                    }
                )
        return queue

    def quality_flags(self, business: dict[str, object]) -> list[str]:
        flags: list[str] = []
        evidence = list(business.get("evidence", []))
        conflicts = list(business.get("conflicts", []))
        category = str(business.get("category") or "").lower()
        reliability_average = self._source_reliability_average(evidence)
        if float(business.get("dna_score") or 0) >= 85 and len(evidence) >= 8 and not conflicts:
            flags.append("HIGHLY_VERIFIED")
        if conflicts:
            flags.append("CONFLICT_DETECTED")
        if float(business.get("dna_score") or 0) < 65 or self._has_high_conflict(conflicts):
            flags.append("NEEDS_HUMAN_REVIEW")
        if reliability_average < 70:
            flags.append("WEAK_SOURCE_COVERAGE")
        if ("cardiologist" in category or "dentist" in category or "lawyer" in category or "legal" in category) and not any(
            item.get("field") == "license_information" for item in evidence
        ):
            flags.append("LICENSE_MISSING")
        if not business.get("phone") or not business.get("website"):
            flags.append("CONTACT_INCOMPLETE")
        return flags or ["STANDARD_REVIEW_COMPLETE"]

    def conflict_severity(self, field: str) -> str:
        if field in self.high_fields:
            return "HIGH"
        if field in self.medium_fields:
            return "MEDIUM"
        return "LOW"

    def _has_high_conflict(self, conflicts: list[object]) -> bool:
        return any(self.conflict_severity(self._value(conflict, "field")) == "HIGH" for conflict in conflicts)

    def _source_reliability_average(self, evidence: list[dict[str, object]]) -> float:
        scores = [float(item.get("reliability_score") or 0) for item in evidence]
        return mean(scores) if scores else 0

    def _value(self, obj: object, key: str) -> str:
        if isinstance(obj, dict):
            return str(obj.get(key) or "")
        return str(getattr(obj, key, ""))
