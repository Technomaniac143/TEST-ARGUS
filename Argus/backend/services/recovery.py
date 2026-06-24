from sqlalchemy import select

from backend.database.session import SessionLocal
from backend.models.research_job import ResearchJob
from backend.models.research_session import ResearchSession
from backend.schemas.research import TimelineEvent
from backend.services.research_jobs import research_job_service
from backend.services.timeline import timeline_hub


class StartupRecoveryService:
    """Recovers queued/running in-process research jobs after backend restart."""

    async def recover(self) -> dict[str, int]:
        from backend.services.research import research_service

        recovered = 0
        failed = 0
        with SessionLocal() as db:
            jobs = db.execute(
                select(ResearchJob).where(ResearchJob.status.in_(["queued", "running"]))
            ).scalars().all()
            for job in jobs:
                session = db.get(ResearchSession, job.session_id)
                if not session:
                    research_job_service.fail(db, job, "Recovery failed: research session missing")
                    failed += 1
                    await timeline_hub.publish(
                        TimelineEvent(
                            session_id=job.session_id,
                            event="job_recovery_failed",
                            message="Recovery failed: research session missing",
                            status="failed",
                            stage=job.current_stage,
                            progress=job.stage_progress,
                        )
                    )
                    continue
                await timeline_hub.publish(
                    TimelineEvent(
                        session_id=session.id,
                        event="job_recovered",
                        message=f"Recovered job at stage {job.current_stage}",
                        status="running",
                        stage=job.current_stage,
                        progress=job.stage_progress,
                    )
                )
                research_job_service.queue(db, job)
                session.status = "queued"
                db.commit()
                research_service.queue(session.id)
                recovered += 1
                await timeline_hub.publish(
                    TimelineEvent(
                        session_id=session.id,
                        event="job_resumed",
                        message=f"Resumed job from {research_job_service.resumable_stage(job)}",
                        status="running",
                        stage=research_job_service.resumable_stage(job),
                        progress=job.stage_progress,
                    )
                )
            return {"recovered": recovered, "failed": failed}


recovery_service = StartupRecoveryService()
