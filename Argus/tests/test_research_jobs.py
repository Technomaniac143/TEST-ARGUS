from datetime import datetime

from backend.models.research_job import ResearchJob
from backend.services.research_jobs import ResearchJobService


class DummyDb:
    def __init__(self) -> None:
        self.commits = 0
        self.refreshes = 0

    def commit(self) -> None:
        self.commits += 1

    def refresh(self, _item) -> None:
        self.refreshes += 1


def job() -> ResearchJob:
    return ResearchJob(session_id=1, status="pending", current_stage="planning")


def test_stage_transitions_update_progress() -> None:
    service = ResearchJobService()
    db = DummyDb()
    item = job()

    service.stage(db, item, "collecting")
    collecting_progress = item.stage_progress
    service.stage(db, item, "completed")

    assert collecting_progress > 0
    assert item.stage_progress == 100
    assert item.status == "complete"
    assert item.completed_at is not None


def test_resume_logic_returns_latest_safe_stage() -> None:
    service = ResearchJobService()
    item = job()
    item.status = "running"
    item.current_stage = "verifying"

    assert service.resumable_stage(item) == "collecting"

    item.current_stage = "enriching"
    assert service.resumable_stage(item) == "enriching"


def test_partial_storage_tracks_urls_businesses_and_failures() -> None:
    service = ResearchJobService()
    db = DummyDb()
    item = job()

    service.set_urls(db, item, ["https://a.example", "https://a.example", "https://b.example"])
    service.discovered(db, item, [type("Business", (), {"name": "Alpha"})(), type("Business", (), {"name": "Beta"})()])
    service.failed_url(db, item, "https://bad.example")

    payload = service.payload(item)
    assert item.total_urls == 3
    assert payload["candidate_urls"] == ["https://a.example", "https://b.example"]
    assert payload["partial_businesses"] == ["Alpha", "Beta"]
    assert payload["failed_urls"] == 1


def test_deep_enrichment_status_is_persisted() -> None:
    service = ResearchJobService()
    db = DummyDb()
    item = job()

    service.enrichment(db, item, "completed_from_existing_corpus")

    assert service.payload(item)["enrichment_status"] == "completed_from_existing_corpus"


def test_job_completion_payload_survives_recovery() -> None:
    service = ResearchJobService()
    db = DummyDb()
    item = job()
    item.created_at = datetime(2026, 1, 1)

    service.start(db, item)
    service.verified(db, item, 8)
    service.stage(db, item, "completed")
    recovered = service.payload(item)

    assert recovered["status"] == "complete"
    assert recovered["verified_businesses"] == 8
    assert recovered["current_stage"] == "completed"
