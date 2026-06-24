from backend.services.analyst import DeterministicAnalystService


def business(**overrides):
    base = {
        "name": "Apollo Heart Center",
        "category": "cardiologists",
        "location": "Chennai",
        "dna_score": 91,
        "confidence": 96,
        "confidence_label": "HIGH",
        "dna_breakdown": {"completeness": 88},
        "market_position": "TOP_10_PERCENT",
        "market_cluster": "Premium Providers",
        "percentile_score": 92,
        "centrality_score": 8,
        "evidence": [
            {"field": "phone", "value": "044-5555-0101", "source": "Official Website", "reliability_score": 95},
            {"field": "address", "value": "Anna Salai, Chennai", "source": "Google Business Profile", "reliability_score": 88},
            {"field": "license_information", "value": "TN-MED-100", "source": "Government License Registry", "reliability_score": 95},
        ],
        "conflicts": [],
        "analyst_quality_flags": ["HIGHLY_VERIFIED"],
        "competitive_intelligence": {
            "strengths": ["High Business DNA score", "Strong source diversity"],
            "weaknesses": [],
            "opportunity_gaps": ["Missing images"],
            "risk_factors": [],
            "differentiation_summary": "Apollo Heart Center stands out with high evidence quality.",
        },
    }
    base.update(overrides)
    return base


def context():
    return {
        "review_queue": [],
        "contradiction_map": [],
        "clusters": [{"cluster_name": "Premium Providers", "cluster_metrics": {"count": 1}}],
        "market_comparison": {"strongest_cluster": "Premium Providers", "weakest_cluster": "Weak Coverage"},
        "ecosystem_summary": {
            "shared_services": ["cardiology"],
            "most_connected_business": "Apollo Heart Center",
            "most_unique_business": "Apollo Heart Center",
        },
        "centrality_metrics": [{"business_name": "Apollo Heart Center", "centrality_score": 8}],
        "source_health": {"crawl_failures": 0},
        "source_reliability_average": 91,
    }


def test_analyst_outputs_and_swot() -> None:
    items = [business()]

    output = DeterministicAnalystService().attach(items, context())

    assert items[0]["swot"]["strengths"]
    assert items[0]["analyst_output"]["confidence"]
    assert items[0]["overall_intelligence_score"] >= 80
    assert output["analyst_output"]["confidence_commentary"]


def test_scorecard_and_benchmarks() -> None:
    items = [business(), business(name="Risk Clinic", dna_score=50, conflicts=[{"field": "phone"}])]

    output = DeterministicAnalystService().attach(items, context())

    assert output["scorecard"]["overall_intelligence_score"] > 0
    assert output["benchmarks"]["best_overall_business"]
    assert output["benchmarks"]["highest_risk_business"] == "Risk Clinic"


def test_recommendations_and_narratives() -> None:
    items = [business(), business(name="Review Clinic", analyst_quality_flags=["NEEDS_HUMAN_REVIEW"], dna_score=55)]
    ctx = context()
    ctx["review_queue"] = [{"business_name": "Review Clinic"}]

    output = DeterministicAnalystService().attach(items, ctx)

    assert output["recommendations"]["businesses_requiring_manual_review"] == ["Review Clinic"]
    assert "market_structure" in output["market_narratives"]
    assert "risk_landscape" in output["market_narratives"]


def test_export_fields_are_attached_to_business() -> None:
    item = business()

    DeterministicAnalystService().attach([item], context())

    assert "overall_intelligence_score" in item
    assert "swot" in item
    assert "executive_recommendation" in item
