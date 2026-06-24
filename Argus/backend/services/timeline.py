import asyncio
import json
from collections import defaultdict
from collections.abc import AsyncGenerator

from sqlalchemy import select

from backend.database.session import SessionLocal
from backend.models.timeline_event import PersistedTimelineEvent
from backend.schemas.research import TimelineEvent


class TimelineHub:
    """Small in-memory pub/sub hub for research timeline events."""

    def __init__(self) -> None:
        self._queues: dict[int, list[asyncio.Queue[TimelineEvent]]] = defaultdict(list)
        self._history: dict[int, list[TimelineEvent]] = defaultdict(list)

    async def publish(self, event: TimelineEvent) -> None:
        self._persist(event)
        self._history[event.session_id].append(event)
        for queue in self._queues[event.session_id]:
            await queue.put(event)

    def history(self, session_id: int) -> list[TimelineEvent]:
        if not self._history.get(session_id):
            self._history[session_id] = self._load(session_id)
        return list(self._history.get(session_id, []))

    async def stream(self, session_id: int) -> AsyncGenerator[str, None]:
        queue: asyncio.Queue[TimelineEvent] = asyncio.Queue()
        self._queues[session_id].append(queue)
        try:
            for event in self.history(session_id):
                yield self._format_event(event)
            if self._history.get(session_id, []) and self._history[session_id][-1].status in {"complete", "failed"}:
                return
            while True:
                event = await queue.get()
                yield self._format_event(event)
                if event.status in {"complete", "failed"}:
                    break
        finally:
            self._queues[session_id].remove(queue)

    def _format_event(self, event: TimelineEvent) -> str:
        return f"event: {event.event}\ndata: {json.dumps(event.model_dump())}\n\n"

    def _persist(self, event: TimelineEvent) -> None:
        with SessionLocal() as db:
            db.add(
                PersistedTimelineEvent(
                    session_id=event.session_id,
                    event_type=event.event,
                    message=event.message,
                    payload=json.dumps(event.payload or {}),
                    stage=event.stage,
                    progress=event.progress,
                )
            )
            db.commit()

    def _load(self, session_id: int) -> list[TimelineEvent]:
        with SessionLocal() as db:
            rows = db.execute(
                select(PersistedTimelineEvent)
                .where(PersistedTimelineEvent.session_id == session_id)
                .order_by(PersistedTimelineEvent.id)
            ).scalars().all()
            events = []
            for row in rows:
                try:
                    payload = json.loads(row.payload or "{}")
                except ValueError:
                    payload = {}
                events.append(
                    TimelineEvent(
                        session_id=row.session_id,
                        event=row.event_type,
                        message=row.message,
                        status="complete" if row.event_type in {"research_complete", "job_completed"} else "running",
                        elapsed_seconds=0,
                        payload=payload,
                        stage=row.stage,
                        progress=row.progress or 0,
                    )
                )
            return events


timeline_hub = TimelineHub()
