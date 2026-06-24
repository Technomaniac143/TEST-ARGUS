import json
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.models.research_job import ResearchJob


STAGES = [
    "planning",
    "discovering",
    "collecting",
    "verifying",
    "deduplicating",
    "enriching",
    "ranking",
    "reporting",
    "completed",
]


class ResearchJobService:
    """Persists progressive deep-research job state for recovery and replay."""

    def get_or_create(self, db: Session, session_id: int) -> ResearchJob:
        job = db.execute(select(ResearchJob).where(ResearchJob.session_id == session_id)).scalars().first()
        if job:
            return job
        job = ResearchJob(session_id=session_id, status="pending", current_stage="planning", stage_progress=0)
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    def start(self, db: Session, job: ResearchJob) -> ResearchJob:
        if not job.started_at:
            job.started_at = self._now()
        job.status = "running"
        self.stage(db, job, "planning")
        return job

    def queue(self, db: Session, job: ResearchJob) -> ResearchJob:
        job.status = "queued"
        job.current_stage = "planning"
        job.stage_progress = 0
        job.updated_at = self._now()
        db.commit()
        db.refresh(job)
        return job

    def stage(self, db: Session, job: ResearchJob, stage: str, progress: int | None = None) -> ResearchJob:
        job.current_stage = stage
        job.status = "complete" if stage == "completed" else "running"
        job.stage_progress = progress if progress is not None else self.stage_progress(stage)
        job.updated_at = self._now()
        if stage == "completed":
            job.completed_at = self._now()
        db.commit()
        db.refresh(job)
        return job

    def fail(self, db: Session, job: ResearchJob, message: str) -> ResearchJob:
        job.status = "failed"
        job.error_message = message[:1000]
        job.updated_at = self._now()
        db.commit()
        db.refresh(job)
        return job

    def cancel(self, db: Session, job: ResearchJob) -> ResearchJob:
        job.status = "cancelled"
        job.updated_at = self._now()
        db.commit()
        db.refresh(job)
        return job

    def stage_progress(self, stage: str) -> int:
        if stage not in STAGES:
            return 0
        return round((STAGES.index(stage) / (len(STAGES) - 1)) * 100)

    def set_urls(self, db: Session, job: ResearchJob, urls: list[str]) -> None:
        job.total_urls = len(urls)
        job.candidate_urls_json = json.dumps(list(dict.fromkeys(urls)))
        job.updated_at = self._now()
        db.commit()

    def processed(self, db: Session, job: ResearchJob, count: int) -> None:
        job.processed_urls = count
        job.updated_at = self._now()
        db.commit()

    def discovered(self, db: Session, job: ResearchJob, businesses: list[object]) -> None:
        names = [str(getattr(item, "name", "") or "business") for item in businesses]
        job.discovered_businesses = len(names)
        job.partial_businesses_json = json.dumps(names)
        job.updated_at = self._now()
        db.commit()

    def verified(self, db: Session, job: ResearchJob, count: int) -> None:
        job.verified_businesses = count
        job.updated_at = self._now()
        db.commit()

    def failed_url(self, db: Session, job: ResearchJob, url: str) -> None:
        failed = self._loads(job.failed_urls_json)
        if url not in failed:
            failed.append(url)
        job.failed_urls_json = json.dumps(failed)
        job.failed_urls = len(failed)
        job.updated_at = self._now()
        db.commit()

    def enrichment(self, db: Session, job: ResearchJob, status: str) -> None:
        job.enrichment_status = status
        job.updated_at = self._now()
        db.commit()

    def resumable_stage(self, job: ResearchJob) -> str:
        if job.status == "complete":
            return "completed"
        if job.current_stage in {"planning", "discovering"}:
            return "discovering"
        if job.current_stage in {"collecting", "verifying", "deduplicating"}:
            return "collecting"
        if job.current_stage == "enriching":
            return "enriching"
        return job.current_stage or "planning"

    def payload(self, job: ResearchJob | None) -> dict[str, object]:
        if not job:
            return {
                "status": "unknown",
                "current_stage": "planning",
                "stage_progress": 0,
                "total_urls": 0,
                "processed_urls": 0,
                "verified_businesses": 0,
                "discovered_businesses": 0,
                "failed_urls": 0,
                "enrichment_status": "pending",
            }
        return {
            "id": job.id,
            "session_id": job.session_id,
            "status": job.status,
            "current_stage": job.current_stage,
            "stage_progress": job.stage_progress,
            "total_urls": job.total_urls,
            "processed_urls": job.processed_urls,
            "verified_businesses": job.verified_businesses,
            "discovered_businesses": job.discovered_businesses,
            "failed_urls": job.failed_urls,
            "enrichment_status": job.enrichment_status,
            "error_message": job.error_message,
            "candidate_urls": self._loads(job.candidate_urls_json),
            "partial_businesses": self._loads(job.partial_businesses_json),
            "created_at": job.created_at.isoformat() if job.created_at else None,
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        }

    def _loads(self, value: str | None) -> list[str]:
        try:
            loaded = json.loads(value or "[]")
        except (TypeError, ValueError):
            return []
        return loaded if isinstance(loaded, list) else []

    def _now(self) -> datetime:
        return datetime.now(timezone.utc).replace(tzinfo=None)


research_job_service = ResearchJobService()
