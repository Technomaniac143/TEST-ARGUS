import asyncio

from fastapi.testclient import TestClient

from backend.api import research as research_api
from backend.database.session import SessionLocal, init_db
from backend.main import app
from backend.models.research_session import ResearchSession
from backend.schemas.research import TimelineEvent
from backend.services.research_jobs import research_job_service
from backend.services.timeline import timeline_hub


def test_start_returns_before_completion(monkeypatch) -> None:
    init_db()
    queued = {}

    def fake_queue(session_id: int) -> None:
        queued["session_id"] = session_id

    monkeypatch.setattr(research_api.research_service, "queue", fake_queue)
    monkeypatch.setattr(research_api.research_service, "is_cache_hit", lambda session_id: False)

    response = TestClient(app).post("/api/research/start", json={"query": "Background cardiologists in Chennai"})

    payload = response.json()
    assert response.status_code == 200
    assert payload["status"] == "queued"
    assert payload["job_id"]
    assert queued["session_id"] == int(payload["session_id"])


def test_get_research_works_while_running_and_report_not_ready(monkeypatch) -> None:
    init_db()
    monkeypatch.setattr(research_api.research_service, "queue", lambda session_id: None)
    monkeypatch.setattr(research_api.research_service, "is_cache_hit", lambda session_id: False)
    client = TestClient(app)

    started = client.post("/api/research/start", json={"query": "Background plumbers in Coimbatore"}).json()
    detail = client.get(f"/api/research/{started['session_id']}").json()

    assert detail["status"] == "queued"
    assert detail["report_ready"] is False
    assert detail["job"]["status"] == "queued"
    assert detail["job"]["current_stage"] == "planning"


def test_job_transition_running_to_completed() -> None:
    init_db()
    db = SessionLocal()
    try:
        session = ResearchSession(query="Dentists in Austin", status="queued")
        db.add(session)
        db.commit()
        db.refresh(session)
        job = research_job_service.get_or_create(db, session.id)

        research_job_service.queue(db, job)
        research_job_service.start(db, job)
        research_job_service.stage(db, job, "completed")

        assert job.status == "complete"
        assert job.stage_progress == 100
    finally:
        db.close()


def test_failed_job_persists_error() -> None:
    init_db()
    db = SessionLocal()
    try:
        session = ResearchSession(query="Failure Case", status="queued")
        db.add(session)
        db.commit()
        db.refresh(session)
        job = research_job_service.get_or_create(db, session.id)

        research_job_service.fail(db, job, "network exploded")

        assert job.status == "failed"
        assert "network exploded" in job.error_message
    finally:
        db.close()


def test_report_ready_true_after_completion() -> None:
    init_db()
    db = SessionLocal()
    try:
        session = ResearchSession(query="Completed Background Case", status="complete")
        db.add(session)
        db.commit()
        db.refresh(session)
        job = research_job_service.get_or_create(db, session.id)
        research_job_service.stage(db, job, "completed")
        session_id = session.id
    finally:
        db.close()

    detail = TestClient(app).get(f"/api/research/{session_id}").json()

    assert detail["report_ready"] is True
    assert detail["job"]["current_stage"] == "completed"


def test_sse_live_history_contains_queued_and_completion_events() -> None:
    async def scenario() -> list[str]:
        session_id = 90001
        await timeline_hub.publish(TimelineEvent(session_id=session_id, event="job_queued", message="queued", status="queued"))
        await timeline_hub.publish(TimelineEvent(session_id=session_id, event="job_completed", message="done", status="complete"))
        events = []
        async for chunk in timeline_hub.stream(session_id):
            events.append(chunk)
        return events

    chunks = asyncio.run(scenario())

    assert any("job_queued" in chunk for chunk in chunks)
    assert any("job_completed" in chunk for chunk in chunks)
