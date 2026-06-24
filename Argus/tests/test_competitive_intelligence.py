from backend.services.competitive_intelligence import CompetitiveIntelligenceService


def business(**overrides):
    base = {
        "name": "Apollo Heart Center",
        "category": "cardiologists",
        "phone": "044-555-0100",
        "website": "https://apollo-heart.example",
        "email": "care@example.com",
        "dna_score": 92,
        "dna_breakdown": {"source_diversity": 90},
        "analyst_quality_flags": ["HIGHLY_VERIFIED"],
        "market_cluster": "Premium Providers",
        "conflicts": [],
        "evidence": [
            {"field": "phone", "value": "044-555-0100", "source": "Official Website", "reliability_score": 95},
            {"field": "address", "value": "Chennai", "source": "Justdial", "reliability_score": 75},
            {"field": "license_information", "value": "TNMC-100", "source": "Government License Registry", "reliability_score": 95},
            {"field": "certifications", "value": "Tamil Nadu Medical Council", "source": "Practo", "reliability_score": 90},
            {"field": "rating", "value": "4.8", "source": "Google Business Profile", "reliability_score": 88},
            {"field": "review_count", "value": "150", "source": "Google Business Profile", "reliability_score": 88},
        ],
    }
    base.update(overrides)
    return base


def test_strength_generation() -> None:
    strengths = CompetitiveIntelligenceService().strengths(business())

    assert "High Business DNA score" in strengths
    assert "Strong source diversity" in strengths
    assert "Certifications present" in strengths


def test_weakness_generation() -> None:
    weaknesses = CompetitiveIntelligenceService().weaknesses(
        business(website=None, phone=None, dna_score=50, conflicts=[{"field": "phone"}])
    )

    assert "Missing website" in weaknesses
    assert "Missing phone" in weaknesses
    assert "Low Business DNA score" in weaknesses
    assert "Conflicts present" in weaknesses


def test_opportunity_gap_generation() -> None:
    gaps = CompetitiveIntelligenceService().opportunity_gaps(business(website=None))

    assert "Missing social profiles" in gaps
    assert "Missing working hours" in gaps
    assert "Missing images" in gaps
    assert "No official website" in gaps


def test_risk_factor_generation() -> None:
    risks = CompetitiveIntelligenceService().risk_factors(
        business(conflicts=[{"field": "phone"}], website=None),
        in_review_queue=True,
    )

    assert "High severity conflict" in risks
    assert "Human review queue item" in risks
    assert "Contact information incomplete" in risks


def test_market_comparison() -> None:
    comparison = CompetitiveIntelligenceService().market_comparison(
        [
            business(name="Strong", dna_score=95, conflicts=[]),
            business(name="Weak", dna_score=40, conflicts=[{"field": "phone"}, {"field": "address"}]),
        ]
    )

    assert comparison["strongest_business"] == "Strong"
    assert comparison["weakest_business"] == "Weak"
    assert comparison["most_conflicted"] == "Weak"


def test_export_fields_present() -> None:
    service = CompetitiveIntelligenceService()
    item = business()
    service.attach([item], [])

    assert "competitive_intelligence" in item
    assert "strengths" in item["competitive_intelligence"]
    assert "weaknesses" in item["competitive_intelligence"]
    assert "opportunity_gaps" in item["competitive_intelligence"]
    assert "risk_factors" in item["competitive_intelligence"]
    assert "differentiation_summary" in item["competitive_intelligence"]
