from backend.services.clustering import MarketClusteringService
from backend.services.knowledge_graph import BusinessKnowledgeGraphService
from backend.services.similarity import BusinessSimilarityService


def business(name="Apollo Heart Center", dna=90, flags=None):
    return {
        "id": name,
        "name": name,
        "category": "cardiologists",
        "location": "chennai",
        "dna_score": dna,
        "dna_breakdown": {"evidence_strength": 90},
        "confidence_label": "HIGH",
        "analyst_quality_flags": flags or ["HIGHLY_VERIFIED"],
        "conflicts": [],
        "evidence": [
            {"field": "services", "value": "cardiac consultation, echocardiography", "source": "Official Website", "reliability_score": 95},
            {"field": "specialties", "value": "heart rhythm", "source": "Practo", "reliability_score": 90},
            {"field": "certifications", "value": "Tamil Nadu Medical Council", "source": "Government License Registry", "reliability_score": 95},
            {"field": "review_count", "value": "150", "source": "Google Business Profile", "reliability_score": 88},
            {"field": "rating", "value": "4.8", "source": "Google Business Profile", "reliability_score": 88},
        ],
    }


def test_knowledge_graph_nodes_and_edges() -> None:
    graph = BusinessKnowledgeGraphService().build([business()], [])

    assert any(node["type"] == "business" for node in graph["nodes"])
    assert any(node["type"] == "service" for node in graph["nodes"])
    assert any(edge["label"] == "BUSINESS_HAS_SERVICE" for edge in graph["edges"])
    assert any(edge["label"] == "BUSINESS_IN_CITY" for edge in graph["edges"])


def test_similarity_scoring_and_top_matches() -> None:
    businesses = [business(), business("Fortis Cardiology", 88), business("Unrelated", 60, ["WEAK_SOURCE_COVERAGE"])]

    BusinessSimilarityService().attach(businesses)

    assert businesses[0]["similar_businesses"][0]["business_name"] == "Fortis Cardiology"
    assert businesses[0]["similar_businesses"][0]["score"] > 70


def test_clustering_market_position_outliers_and_overview() -> None:
    businesses = [
        business(),
        business("Review Clinic", 55, ["NEEDS_HUMAN_REVIEW", "WEAK_SOURCE_COVERAGE"]),
    ]
    review_queue = [{"business_name": "Review Clinic", "reason": "Low DNA"}]
    service = MarketClusteringService()

    clusters = service.attach(businesses, review_queue)
    outliers = service.outliers(businesses, review_queue)
    overview = service.market_overview(businesses, clusters, review_queue, ["cardiac consultation"], ["heart rhythm"])

    assert businesses[0]["market_position"] in {"TOP_5_PERCENT", "TOP_10_PERCENT", "ABOVE_AVERAGE"}
    assert businesses[1]["market_cluster"] == "Review Required"
    assert outliers["Review Clinic"]
    assert overview["total_businesses"] == 2
    assert "Premium Providers" in {cluster["cluster_name"] for cluster in clusters}


def test_export_payloads_include_market_fields() -> None:
    payload = business()
    payload["similar_businesses"] = [{"business_name": "Fortis Cardiology", "score": 92}]
    payload["market_cluster"] = "Premium Providers"
    payload["market_position"] = "TOP_10_PERCENT"
    report = {
        "knowledge_graph": {"nodes": [], "edges": []},
        "clusters": [],
        "market_positions": [],
        "outliers": {},
        "market_overview": {},
    }

    assert "similar_businesses" in payload
    assert "market_cluster" in payload
    assert "market_position" in payload
    assert "knowledge_graph" in report
