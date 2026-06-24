from statistics import mean


class DeterministicAnalystService:
    """Executive intelligence without LLMs: rule-based SWOT, scorecards, narratives."""

    def attach(
        self,
        businesses: list[dict[str, object]],
        report_context: dict[str, object],
    ) -> dict[str, object]:
        review_names = {str(item.get("business_name")) for item in report_context.get("review_queue", [])}
        for business in businesses:
            swot = self.swot(business, business.get("name") in review_names)
            business["swot"] = swot
            business["analyst_output"] = self.business_commentary(business, swot)
            business["overall_intelligence_score"] = self.business_score(business, swot)
            business["executive_recommendation"] = self.business_recommendation(business, swot)
        benchmarks = self.benchmarks(businesses, report_context)
        scorecard = self.scorecard(businesses, report_context)
        narratives = self.market_narratives(businesses, report_context, benchmarks)
        recommendations = self.recommendations(businesses, report_context)
        return {
            "benchmarks": benchmarks,
            "scorecard": scorecard,
            "market_narratives": narratives,
            "recommendations": recommendations,
            "analyst_output": {
                "data_quality_commentary": self.data_quality_commentary(scorecard),
                "confidence_commentary": self.confidence_commentary(scorecard),
                "market_commentary": narratives["market_structure"],
                "review_commentary": narratives["risk_landscape"],
                "cluster_commentary": narratives["cluster_landscape"],
                "competitive_commentary": narratives["competitive_landscape"],
            },
        }

    def swot(self, business: dict[str, object], in_review_queue: bool = False) -> dict[str, list[str]]:
        competitive = business.get("competitive_intelligence", {})
        strengths = list(competitive.get("strengths", []))
        weaknesses = list(competitive.get("weaknesses", []))
        opportunities = list(competitive.get("opportunity_gaps", []))
        threats = list(competitive.get("risk_factors", []))
        if float(business.get("dna_score") or 0) >= 85:
            strengths.append("High trust profile")
        if business.get("market_position") in {"TOP_5_PERCENT", "TOP_10_PERCENT"}:
            strengths.append("Strong market position")
        if business.get("market_cluster") == "Premium Providers":
            strengths.append("Premium provider cluster membership")
        if business.get("conflicts"):
            threats.append("Contradictory evidence requires resolution")
        if "NEEDS_HUMAN_REVIEW" in business.get("analyst_quality_flags", []) or in_review_queue:
            threats.append("Manual review required before use")
        if not opportunities:
            opportunities.append("Maintain evidence freshness and source monitoring")
        return {
            "strengths": self._unique(strengths) or ["Baseline evidence present"],
            "weaknesses": self._unique(weaknesses) or ["No major weakness detected"],
            "opportunities": self._unique(opportunities),
            "threats": self._unique(threats) or ["No major threat detected"],
        }

    def business_commentary(self, business: dict[str, object], swot: dict[str, list[str]]) -> dict[str, str]:
        name = business.get("name") or "This business"
        return {
            "strengths": f"{name} shows {swot['strengths'][0].lower()} with a DNA score of {round(float(business.get('dna_score') or 0))}.",
            "weaknesses": f"Primary weakness: {swot['weaknesses'][0].lower()}.",
            "opportunities": f"Opportunity: {swot['opportunities'][0].lower()}.",
            "threats": f"Threat profile: {swot['threats'][0].lower()}.",
            "confidence": f"Confidence is {business.get('confidence_label', 'MEDIUM')} with {len(business.get('evidence', []))} evidence receipt(s).",
            "competitive": str(business.get("competitive_intelligence", {}).get("differentiation_summary", "")),
        }

    def business_score(self, business: dict[str, object], swot: dict[str, list[str]]) -> int:
        base = float(business.get("dna_score") or 0) * 0.45
        evidence = min(100, len(business.get("evidence", [])) * 8) * 0.2
        market = float(business.get("percentile_score") or 50) * 0.15
        centrality = min(100, float(business.get("centrality_score") or 0) * 8) * 0.1
        penalties = (len(business.get("conflicts", [])) * 7 + max(0, len(swot["threats"]) - 1) * 3)
        return round(max(0, min(100, base + evidence + market + centrality + 15 - penalties)))

    def business_recommendation(self, business: dict[str, object], swot: dict[str, list[str]]) -> str:
        score = int(business.get("overall_intelligence_score") or self.business_score(business, swot))
        if score >= 82 and not business.get("conflicts"):
            return "Safe for executive outreach"
        if score >= 68:
            return "Promising with verification follow-up"
        if "Manual review required before use" in swot["threats"]:
            return "Manual review required"
        return "Additional verification required"

    def benchmarks(self, businesses: list[dict[str, object]], context: dict[str, object]) -> dict[str, object]:
        if not businesses:
            return {}
        centrality = context.get("centrality_metrics", [])
        return {
            "best_overall_business": max(businesses, key=lambda b: b.get("overall_intelligence_score", 0)).get("name"),
            "highest_trust_business": max(businesses, key=lambda b: float(b.get("dna_score") or 0)).get("name"),
            "highest_risk_business": max(businesses, key=lambda b: len(b.get("conflicts", [])) + len(b.get("swot", {}).get("threats", []))).get("name"),
            "most_differentiated": max(businesses, key=lambda b: len(b.get("swot", {}).get("strengths", []))).get("name"),
            "strongest_cluster": context.get("market_comparison", {}).get("strongest_cluster"),
            "weakest_cluster": context.get("market_comparison", {}).get("weakest_cluster"),
            "most_connected": (centrality[0].get("business_name") if centrality else None),
            "most_isolated": (centrality[-1].get("business_name") if centrality else None),
            "highest_confidence": max(businesses, key=lambda b: float(b.get("confidence") or 0)).get("name"),
            "highest_opportunity": max(businesses, key=lambda b: len(b.get("swot", {}).get("opportunities", []))).get("name"),
        }

    def scorecard(self, businesses: list[dict[str, object]], context: dict[str, object]) -> dict[str, int]:
        if not businesses:
            return {key: 0 for key in ["trust_score", "coverage_score", "risk_score", "evidence_score", "market_strength_score", "review_burden_score", "overall_intelligence_score"]}
        avg_dna = mean(float(b.get("dna_score") or 0) for b in businesses)
        evidence_score = min(100, round(mean(len(b.get("evidence", [])) for b in businesses) * 8))
        coverage = round(mean(int(b.get("dna_breakdown", {}).get("completeness", 0)) for b in businesses))
        conflicts = sum(len(b.get("conflicts", [])) for b in businesses)
        review_items = len(context.get("review_queue", []))
        market_strength = round(mean(float(b.get("percentile_score") or 50) for b in businesses))
        risk_score = max(0, 100 - conflicts * 10 - review_items * 6)
        review_burden = max(0, 100 - review_items * 10)
        overall = round(mean([avg_dna, evidence_score, coverage, risk_score, market_strength, review_burden]))
        return {
            "trust_score": round(avg_dna),
            "coverage_score": coverage,
            "risk_score": risk_score,
            "evidence_score": evidence_score,
            "market_strength_score": market_strength,
            "review_burden_score": review_burden,
            "overall_intelligence_score": overall,
        }

    def market_narratives(self, businesses: list[dict[str, object]], context: dict[str, object], benchmarks: dict[str, object]) -> dict[str, str]:
        ecosystem = context.get("ecosystem_summary", {})
        source_health = context.get("source_health", {})
        return {
            "market_structure": f"The market resolves into {len(context.get('clusters', []))} cluster(s), led by {benchmarks.get('strongest_cluster') or 'unassigned providers'}.",
            "competitive_landscape": f"{benchmarks.get('best_overall_business') or 'The top business'} leads the executive benchmark, while {benchmarks.get('highest_opportunity') or 'several businesses'} show opportunity upside.",
            "risk_landscape": f"{len(context.get('review_queue', []))} business(es) require review and {len(context.get('contradiction_map', []))} contradiction(s) remain visible.",
            "source_landscape": f"Source reliability averages {context.get('source_reliability_average', 0)}/100 with {source_health.get('crawl_failures', 0)} crawl failure(s).",
            "relationship_landscape": f"{ecosystem.get('most_connected_business') or 'No single business'} is most connected; {ecosystem.get('most_unique_business') or 'no unique outlier'} appears most isolated.",
            "cluster_landscape": f"Dominant services include {', '.join(ecosystem.get('shared_services', [])[:3]) or 'limited shared service signals'}.",
        }

    def recommendations(self, businesses: list[dict[str, object]], context: dict[str, object]) -> dict[str, list[str]]:
        return {
            "immediate_actions": [
                "Use top-ranked, high-trust businesses for the first outreach wave.",
                "Resolve high-severity contradictions before operational use.",
            ],
            "businesses_requiring_manual_review": [str(item.get("business_name")) for item in context.get("review_queue", [])],
            "businesses_safe_for_outreach": [str(b.get("name")) for b in businesses if b.get("executive_recommendation") == "Safe for executive outreach"],
            "businesses_requiring_additional_verification": [str(b.get("name")) for b in businesses if b.get("executive_recommendation") in {"Manual review required", "Additional verification required"}],
            "weak_areas_in_current_market": self._weak_areas(businesses),
            "high_opportunity_businesses": [str(b.get("name")) for b in sorted(businesses, key=lambda item: len(item.get("swot", {}).get("opportunities", [])), reverse=True)[:3]],
        }

    def data_quality_commentary(self, scorecard: dict[str, int]) -> str:
        return f"Data quality is represented by {scorecard['coverage_score']}/100 coverage and {scorecard['evidence_score']}/100 evidence strength."

    def confidence_commentary(self, scorecard: dict[str, int]) -> str:
        return f"Overall trust is {scorecard['trust_score']}/100 with an intelligence score of {scorecard['overall_intelligence_score']}/100."

    def _weak_areas(self, businesses: list[dict[str, object]]) -> list[str]:
        counter: dict[str, int] = {}
        for business in businesses:
            for weakness in business.get("swot", {}).get("weaknesses", []):
                counter[weakness] = counter.get(weakness, 0) + 1
        return [item for item, _count in sorted(counter.items(), key=lambda pair: pair[1], reverse=True)[:5]]

    def _unique(self, values: list[str]) -> list[str]:
        return list(dict.fromkeys(value for value in values if value))
