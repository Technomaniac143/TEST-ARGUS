import asyncio
from types import SimpleNamespace

from fastapi.testclient import TestClient

from backend.api import research as research_api
from backend.database.session import SessionLocal, engine, init_db
from backend.main import app
from backend.services.research import research_service


def test_start_then_get_uses_returned_session_id(monkeypatch) -> None:
    init_db()
    monkeypatch.setattr(research_api.research_service, "queue", lambda session_id: None)
    monkeypatch.setattr(research_api.research_service, "is_cache_hit", lambda session_id: False)

    client = TestClient(app)
    started = client.post(
        "/api/research/start",
        json={"query": "Production contract cardiologists in Chennai", "mode": "offline"},
    )

    assert started.status_code == 200
    session_id = started.json()["session_id"]
    detail = client.get(f"/api/research/{session_id}")

    assert detail.status_code == 200
    assert str(detail.json()["id"]) == session_id


def test_research_404_includes_cors_for_vercel_origin() -> None:
    init_db()
    client = TestClient(app)

    response = client.get(
        "/api/research/999999999",
        headers={"Origin": "https://argus-frontend-seven.vercel.app"},
    )

    assert response.status_code == 404
    assert response.headers["access-control-allow-origin"] == "https://argus-frontend-seven.vercel.app"


def test_completed_offline_research_get_releases_pool_connections() -> None:
    init_db()
    with SessionLocal() as db:
        session = research_service.start(db, "Plumbers in Coimbatore", "offline")
        session_id = session.id

    if not research_service.is_cache_hit(session_id):
        asyncio.run(research_service.run(session_id))

    client = TestClient(app)
    for _ in range(20):
        response = client.get(f"/api/research/{session_id}")
        assert response.status_code == 200

    payload = response.json()
    assert payload["businesses"]
    assert payload["businesses"][0]["name"]
    assert payload["businesses"][0]["dna_score"] > 0

    checkedout = getattr(engine.pool, "checkedout", None)
    if checkedout is not None:
        assert checkedout() == 0


def test_basic_research_endpoint_is_stable_for_repeated_polling() -> None:
    init_db()
    with SessionLocal() as db:
        session = research_service.start(db, "Cardiologists in Chennai", "offline")
        session_id = session.id

    if not research_service.is_cache_hit(session_id):
        asyncio.run(research_service.run(session_id))

    client = TestClient(app)
    for _ in range(100):
        response = client.get(f"/api/research/{session_id}/basic")
        assert response.status_code == 200
        payload = response.json()
        assert payload["session_id"] == str(session_id)
        assert payload["businesses"]
        assert payload["businesses"][0]["name"]
        assert payload["businesses"][0]["dna_score"] > 0
        assert len(payload["businesses"]) <= 10
        assert len(payload["timeline_events"]) <= 20

    checkedout = getattr(engine.pool, "checkedout", None)
    if checkedout is not None:
        assert checkedout() == 0


def test_existing_get_returns_compact_safe_payload() -> None:
    init_db()
    with SessionLocal() as db:
        session = research_service.start(db, "Cardiologists in Chennai", "offline")
        session_id = session.id

    if not research_service.is_cache_hit(session_id):
        asyncio.run(research_service.run(session_id))

    payload = TestClient(app).get(f"/api/research/{session_id}").json()

    assert payload["session_id"] == str(session_id)
    assert payload["businesses"]
    assert payload["businesses"][0]["dna_score"] > 0
    assert "relationship_graph" not in payload.get("report", {})


def test_production_safe_start_completes_without_background_worker(monkeypatch) -> None:
    init_db()
    queued = {"called": False}

    monkeypatch.setattr(research_api, "get_settings", lambda: SimpleNamespace(argus_production_safe_mode=True))
    monkeypatch.setattr(research_api.research_service, "queue", lambda session_id: queued.update(called=True))

    client = TestClient(app)
    started = client.post(
        "/api/research/start",
        json={"query": "Cardiologists in Chennai", "mode": "offline"},
    )

    assert started.status_code == 200
    assert started.json()["status"] == "complete"
    assert queued["called"] is False

    basic = client.get(f"/api/research/{started.json()['session_id']}/basic")
    assert basic.status_code == 200
    payload = basic.json()
    assert payload["status"] == "complete"
    assert payload["businesses"]
    assert payload["businesses"][0]["dna_score"] > 0
