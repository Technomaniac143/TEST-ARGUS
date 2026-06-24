import asyncio

from sqlalchemy import select

from backend.database.session import SessionLocal, init_db
from backend.models.research_job import ResearchJob
from backend.models.research_session import ResearchSession
from backend.models.timeline_event import PersistedTimelineEvent
from backend.schemas.research import TimelineEvent
from backend.services.recovery import recovery_service
from backend.services.relationship_graph import RelationshipGraphService
from backend.services.research_jobs import research_job_service
from backend.services.timeline import timeline_hub


def test_timeline_event_persistence_and_replay() -> None:
    init_db()
    session_id = 777001

    asyncio.run(
        timeline_hub.publish(
            TimelineEvent(
                session_id=session_id,
                event="stage_changed",
                message="Stage changed: discovering",
                stage="discovering",
                progress=20,
            )
        )
    )
    timeline_hub._history.pop(session_id, None)

    replay = timeline_hub.history(session_id)

    assert replay[0].event == "stage_changed"
    assert replay[0].stage == "discovering"
    assert replay[0].progress == 20


def test_startup_recovery_resumes_queued_job(monkeypatch) -> None:
    init_db()
    queued = []
    db = SessionLocal()
    try:
        session = ResearchSession(query="Recovery Cardiologists in Chennai", status="queued")
        db.add(session)
        db.commit()
        db.refresh(session)
        job = ResearchJob(session_id=session.id, status="queued", current_stage="collecting", stage_progress=35)
        db.add(job)
        db.commit()
        session_id = session.id
    finally:
        db.close()

    from backend.services.research import research_service

    monkeypatch.setattr(research_service, "queue", lambda sid: queued.append(sid))

    result = asyncio.run(recovery_service.recover())

    assert result["recovered"] >= 1
    assert session_id in queued
    db = SessionLocal()
    try:
        events = db.execute(
            select(PersistedTimelineEvent).where(PersistedTimelineEvent.session_id == session_id)
        ).scalars().all()
        assert any(item.event_type == "job_recovered" for item in events)
        assert any(item.event_type == "job_resumed" for item in events)
    finally:
        db.close()


def test_relationship_graph_edges_and_network_metrics() -> None:
    businesses = [
        business("Alpha Heart", "Premium Providers", ["cardiology", "imaging"], ["echo"], ["Board Certified"]),
        business("Beta Heart", "Premium Providers", ["cardiology"], ["echo"], ["Board Certified"]),
        business("Solo Clinic", "Weak Coverage", ["rehab"], ["vascular"], []),
    ]
    businesses[0]["similar_businesses"] = [{"business_name": "Beta Heart", "score": 91}]
    businesses[1]["similar_businesses"] = [{"business_name": "Alpha Heart", "score": 91}]
    clusters = [{"cluster_name": "Premium Providers", "cluster_metrics": {"count": 2}}, {"cluster_name": "Weak Coverage", "cluster_metrics": {"count": 1}}]

    graph = RelationshipGraphService().build(businesses, clusters)

    edge_types = {edge["type"] for edge in graph["edges"]}
    assert "SHARES_SERVICE" in edge_types
    assert "SHARES_SPECIALTY" in edge_types
    assert "SHARES_CERTIFICATION" in edge_types
    assert "IN_SAME_CLUSTER" in edge_types
    assert "SIMILAR_TO" in edge_types
    assert graph["ecosystem_summary"]["most_connected_business"]
    assert graph["centrality_metrics"][0]["centrality_score"] >= graph["centrality_metrics"][-1]["centrality_score"]
    assert graph["similar_pairs"][0]["score"] == 91


def test_ecosystem_summary_and_export_fields_are_available() -> None:
    businesses = [
        business("Alpha", "Small Clinics", ["plumbing"], ["emergency"], ["Licensed"]),
        business("Beta", "Small Clinics", ["plumbing"], ["repair"], ["Licensed"]),
    ]
    graph = RelationshipGraphService().build(businesses, [{"cluster_name": "Small Clinics", "cluster_metrics": {"count": 2}}])

    assert "plumbing" in graph["ecosystem_summary"]["shared_services"]
    assert businesses[0]["centrality_score"] >= 1
    assert "top_relationship" in businesses[0]
    assert "shared_services_count" in businesses[0]


def business(name: str, cluster: str, services: list[str], specialties: list[str], certifications: list[str]) -> dict[str, object]:
    evidence = []
    for field, values in {"services": services, "specialties": specialties, "certifications": certifications}.items():
        if values:
            evidence.append({"field": field, "value": ", ".join(values), "source": "Official Website", "reliability_score": 95})
    return {
        "id": name,
        "name": name,
        "location": "Chennai",
        "category": "cardiologists",
        "market_cluster": cluster,
        "analyst_quality_flags": ["HIGHLY_VERIFIED"],
        "evidence": evidence,
        "outliers": [],
        "similar_businesses": [],
    }
