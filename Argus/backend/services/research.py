import json
import time
import asyncio
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.agents.scout import ScoutAgent
from backend.database.session import SessionLocal, engine
from backend.models.business import Business
from backend.models.research_cache import ResearchCache
from backend.models.research_session import ResearchSession
from backend.schemas.research import TimelineEvent
from backend.schemas.search import SearchResult
from backend.services.collector import CollectorService
from backend.services.conflicts import ConflictDetectionService
from backend.services.deduplication import DeduplicationService
from backend.services.dna import BusinessDnaService
from backend.services.search import SearchService
from backend.services.research_jobs import research_job_service
from backend.services.timeline import timeline_hub
from backend.services.verification import VerificationService
from backend.config import get_settings

logger = logging.getLogger(__name__)


class ResearchService:
    """Coordinates the ARGUS research pipeline."""

    def __init__(self) -> None:
        self.scout = ScoutAgent()
        self.search = SearchService()
        self.collector = CollectorService()
        self.deduplication = DeduplicationService()
        self.conflicts = ConflictDetectionService()
        self.dna = BusinessDnaService()
        self.verification = VerificationService()
        self._started_at: dict[int, float] = {}
        self._cache_hits: dict[int, dict[str, object]] = {}
        self._tasks: dict[int, asyncio.Task] = {}
        self._session_modes: dict[int, str] = {}

    def queue(self, session_id: int) -> None:
        task = self._tasks.get(session_id)
        if task and not task.done():
            return
        self._tasks[session_id] = asyncio.create_task(self.run(session_id))

    def start(self, db: Session, query: str, mode: str | None = None) -> ResearchSession:
        parsed = self.scout.parse_query(query)
        settings = get_settings()
        requested_mode = self._normalize_requested_mode(mode) or self.search._mode(settings)
        cache_key = self._cache_key(parsed.category, parsed.location, settings.argus_demo_mode, getattr(settings, "argus_offline_mode", False), requested_mode)
        now = datetime.now(timezone.utc).replace(tzinfo=None)
        cache = db.execute(select(ResearchCache).where(ResearchCache.cache_key == cache_key)).scalars().first()
        if cache and cache.expires_at > now:
            cached = db.get(ResearchSession, cache.session_id)
            if cached and cached.status == "complete" and cached.businesses_found > 0:
                research_job_service.get_or_create(db, cached.id)
                cache.hit_count += 1
                db.commit()
                self._cache_hits[cached.id] = {
                    "cache_hit": True,
                    "cached_at": cache.created_at.isoformat(),
                    "cache_age_seconds": round((now - cache.created_at).total_seconds(), 2),
                    "cache_key": cache.cache_key,
                    "hit_count": cache.hit_count,
                }
                self._session_modes[cached.id] = requested_mode
                return cached

        session = ResearchSession(query=query, status="started")
        db.add(session)
        db.commit()
        db.refresh(session)
        research_job_service.get_or_create(db, session.id)
        self._session_modes[session.id] = requested_mode
        return session

    def cache_metadata(self, session_id: int) -> dict[str, object]:
        return self._cache_hits.get(session_id, {"cache_hit": False, "cached_at": None, "cache_age_seconds": None, "cache_key": None})

    def is_cache_hit(self, session_id: int) -> bool:
        return bool(self._cache_hits.get(session_id, {}).get("cache_hit", False))

    async def run(self, session_id: int) -> None:
        started_at = time.perf_counter()
        self._started_at[session_id] = started_at
        db = SessionLocal()
        try:
            session = db.get(ResearchSession, session_id)
            if session is None:
                return
            job = research_job_service.get_or_create(db, session.id)
            if job.status == "cancelled":
                await self._event(session_id, "job_failed", "Research job was cancelled", status="failed")
                return
            research_job_service.start(db, job)

            await self._event(session_id, "job_started", "Research job started", job.stage_progress)
            await self._event(session_id, "research_started", "Research started", job.stage_progress)

            parsed = self.scout.parse_query(session.query)
            session.category = parsed.category
            session.location = parsed.location
            session.status = "running"
            db.commit()
            await self._event(session_id, "query_parsed", "Query parsed", job.stage_progress)
            await self._event(session_id, "cache_miss", "Research cache miss")

            settings = get_settings()
            mode = self._session_modes.get(session_id) or self.search._mode(settings)
            research_job_service.stage(db, job, "planning")
            await self._ensure_not_cancelled(db, job, session_id)
            await self._event(session_id, "stage_changed", "Stage changed: planning", job.stage_progress)
            if mode == "offline":
                await self._event(session_id, "source_plan_created", "Offline corpus source plan created")
                for label in [
                    "Google Business Profiles",
                    "official websites",
                    "Yelp",
                    "Yellow Pages",
                    "LinkedIn",
                    "Facebook",
                    "professional directories",
                    "license registries",
                    "public review platforms",
                ]:
                    await self._event(session_id, "source_search_started", f"Searching offline {label}")
            elif mode == "demo":
                await self._event(session_id, "searching_google_profiles", "Searching Google Business Profiles")
                await self._event(session_id, "searching_official_websites", "Searching official websites")
                await self._event(session_id, "checking_professional_directories", "Checking professional directories")
                await self._event(session_id, "checking_license_registries", "Checking license registries")
            else:
                targets = self.search.planner.plan(parsed, getattr(settings, "argus_max_source_queries", settings.argus_max_source_targets))
                await self._event(session_id, "source_plan_created", f"Source plan created: {len(targets)} targets")
                for target in targets:
                    await self._event(session_id, "source_search_started", f"Searching {target.label}")
                await self._event(session_id, "searching_duckduckgo", "Searching DuckDuckGo")
                await self._event(session_id, "searching_bing", "Searching Bing")
            research_job_service.stage(db, job, "discovering")
            await self._ensure_not_cancelled(db, job, session_id)
            await self._event(session_id, "stage_changed", "Stage changed: discovering", job.stage_progress)
            results, sources_searched = await self.search.search(parsed, mode_override=mode)
            research_job_service.set_urls(db, job, [result.url for result in results])
            metadata = self.search.last_metadata
            session.sources_searched = sources_searched
            db.commit()
            await self._event(session_id, "active_mode", f"Active Mode: {self._mode_label(str(metadata.get('active_mode', mode)))}")
            if metadata.get("online_results_count") is not None:
                await self._event(session_id, "online_results_count", f"Online results count: {metadata.get('online_results_count')}")
            for adapter_event in metadata.get("adapter_events", []):
                event_name = str(adapter_event.get("event", "adapter_event"))
                adapter = adapter_event.get("adapter", "Adapter")
                if event_name == "adapter_started":
                    await self._event(session_id, "adapter_started", f"{adapter} started page {adapter_event.get('page')}")
                elif event_name == "adapter_finished":
                    await self._event(session_id, "adapter_finished", f"{adapter} finished with {adapter_event.get('results', 0)} result(s)")
                elif event_name == "adapter_failed":
                    await self._event(session_id, "adapter_failed", f"{adapter} failed: {adapter_event.get('reason', 'unknown error')}")
                elif event_name == "page_discovered":
                    await self._event(session_id, "page_discovered", f"{adapter} discovered {adapter_event.get('url')}")
            if metadata.get("adapter_health"):
                await self._event(session_id, "adapter_health", f"Adapter health: {json.dumps(metadata.get('adapter_health'))}")
            for failure in metadata.get("failed_searches", []):
                await self._event(session_id, "source_search_failed", f"{failure.get('provider')} failed: {failure.get('query')}")
            if metadata.get("fallback_used"):
                await self._event(session_id, "fallback_used", f"Fallback used: {metadata.get('fallback_reason')}")
            if metadata.get("filtered_urls_count"):
                await self._event(session_id, "urls_filtered", f"Filtered URLs: {metadata.get('filtered_urls_count')}")
            await self._event(session_id, "search_results_found", f"Search results found: {len(results)}")
            if mode != "demo":
                await self._event(session_id, "source_search_completed", f"Source searches completed: {sources_searched}")
            for result in results:
                await self._event(session_id, "url_discovered", f"URL discovered: {result.url}")
                await self._event(session_id, "url_processed", f"URL processed: {result.url}", job.stage_progress)
                await self._event(session_id, "business_candidate_found", f"Business candidate found: {result.title}", job.stage_progress)
                if result.adapter_name:
                    await self._event(session_id, "page_processed", f"{result.adapter_name} page processed: {result.url}")

            research_job_service.stage(db, job, "collecting")
            await self._ensure_not_cancelled(db, job, session_id)
            await self._event(session_id, "stage_changed", "Stage changed: collecting", job.stage_progress)
            await self._event(session_id, "collecting_business_data", "Collecting business data")
            await self._event(session_id, "collection_started", "Concurrent collection started")
            collected = await self.collector.collect(
                results,
                parsed,
                on_failure=lambda result: self._collection_failed(session_id, result.url),
                on_crawl_event=lambda event, message: self._event(session_id, event, message),
            )
            research_job_service.processed(db, job, len(collected))
            research_job_service.discovered(db, job, collected)
            for record in collected:
                await self._event(session_id, "business_discovered", f"Discovered {record.name or 'business'}")
                await self._event(session_id, "business_extracted", f"Extracted {record.name or 'business'}")
                await self._event(session_id, "evidence_found", f"Evidence receipts found: {len(record.evidence)}")

            research_job_service.stage(db, job, "deduplicating")
            await self._ensure_not_cancelled(db, job, session_id)
            await self._event(session_id, "stage_changed", "Stage changed: deduplicating", job.stage_progress)
            await self._event(session_id, "deduplicating_records", "Deduplicating records")
            if mode in {"demo", "offline", "auto"}:
                await self._event(session_id, "comparing_directory_records", "Comparing directory records")
            deduped, duplicates_removed = self.deduplication.deduplicate(collected)
            session.duplicates_removed = duplicates_removed
            if duplicates_removed:
                await self._event(session_id, "duplicate_detected", f"Duplicates removed: {duplicates_removed}")

            research_job_service.stage(db, job, "verifying")
            await self._ensure_not_cancelled(db, job, session_id)
            await self._event(session_id, "stage_changed", "Stage changed: verifying", job.stage_progress)
            await self._event(session_id, "verifying_evidence", "Verifying evidence")
            await self._event(session_id, "detecting_conflicts", "Detecting conflicts")
            research_job_service.stage(db, job, "enriching")
            await self._ensure_not_cancelled(db, job, session_id)
            await self._event(session_id, "stage_changed", "Stage changed: enriching", job.stage_progress)
            deduped = await self._deep_enrichment(db, job, session_id, deduped, parsed, mode)
            await self._event(session_id, "computing_business_dna", "Computing Business DNA")
            if mode in {"demo", "offline", "auto"}:
                await self._event(session_id, "generating_argus_explanation", "Generating Argus explanation")

            verified_count = 0
            for extracted in deduped:
                conflict_items = self.conflicts.detect(extracted)
                for conflict in conflict_items:
                    await self._event(session_id, "conflict_detected", f"Conflict detected for {extracted.name}: {conflict.field}")
                    await self._event(session_id, "conflict_found", f"Conflict found for {extracted.name}: {conflict.field}", job.stage_progress)
                dna_score = self.dna.score(extracted, conflict_items)
                await self._event(session_id, "dna_computed", f"Business DNA computed for {extracted.name}: {dna_score.dna_score}")
                confidence = self.verification.confidence(extracted, len(conflict_items))
                business = Business(
                    session_id=session.id,
                    name=extracted.name,
                    category=extracted.category,
                    location=extracted.location,
                    phone=extracted.phone,
                    address=extracted.address,
                    website=extracted.website,
                    email=extracted.email,
                    confidence=confidence,
                    dna_score=dna_score.dna_score,
                    risk=self._risk(dna_score.dna_score, len(conflict_items)),
                )
                db.add(business)
                db.flush()
                self.verification.store_evidence(db, business, extracted)
                self.verification.store_conflicts(db, business, conflict_items)
                verified_count += 1
                research_job_service.verified(db, job, verified_count)
                await self._event(session_id, "business_verified", f"Verified {extracted.name}", job.stage_progress)

            research_job_service.stage(db, job, "ranking")
            await self._ensure_not_cancelled(db, job, session_id)
            await self._event(session_id, "stage_changed", "Stage changed: ranking", job.stage_progress)
            session.businesses_found = len(deduped)
            session.duration = round(time.perf_counter() - started_at, 2)
            session.status = "complete"
            research_job_service.stage(db, job, "reporting")
            await self._event(session_id, "stage_changed", "Stage changed: reporting", job.stage_progress)
            await self._event(session_id, "report_ready", "Final research report ready", job.stage_progress)
            research_job_service.stage(db, job, "completed")
            await self._event(session_id, "job_completed", "Research job completed", job.stage_progress, status="complete")
            await self._event(session_id, "research_complete", "Research complete", job.stage_progress, status="complete")
            session.timeline_summary = self._timeline_json(session_id)
            self._store_cache(db, session)
            db.commit()
            self._log_pool_status("job_complete")
        except Exception as exc:
            session = db.get(ResearchSession, session_id)
            if session:
                job = research_job_service.get_or_create(db, session.id)
                research_job_service.fail(db, job, str(exc))
                session.status = "failed"
                session.duration = round(time.perf_counter() - started_at, 2)
                session.timeline_summary = self._timeline_json(session_id)
                db.commit()
            await self._event(session_id, "job_failed", f"Research job failed: {exc}", status="failed")
            await self._event(session_id, "research_failed", f"Research failed: {exc}", status="failed")
        finally:
            self._started_at.pop(session_id, None)
            task = self._tasks.get(session_id)
            if task and task.done():
                self._tasks.pop(session_id, None)
            db.close()

    def _log_pool_status(self, label: str) -> None:
        try:
            logger.info("db_pool_status %s %s", label, engine.pool.status())
        except Exception:
            logger.info("db_pool_status %s unavailable", label)

    async def _ensure_not_cancelled(self, db, job, session_id: int) -> None:
        db.refresh(job)
        if job.status == "cancelled":
            await self._event(session_id, "job_failed", "Research job cancelled", status="failed")
            raise RuntimeError("Research job cancelled")

    async def _collection_failed(self, session_id: int, url: str) -> None:
        progress = 0
        with SessionLocal() as db:
            session = db.get(ResearchSession, session_id)
            if session:
                job = research_job_service.get_or_create(db, session.id)
                research_job_service.failed_url(db, job, url)
                progress = job.stage_progress
        await self._event(session_id, "url_failed", f"URL failed: {url}", progress)
        await self._event(session_id, "collection_failed", f"Collection failed: {url}", progress)

    async def _deep_enrichment(self, db, job, session_id: int, deduped, parsed, mode: str):
        if mode in {"offline", "demo", "auto"}:
            research_job_service.enrichment(db, job, "completed_from_existing_corpus")
            await self._event(session_id, "business_enriched", "Deep enrichment completed from existing verified corpus", job.stage_progress)
            return deduped
        urls: list[SearchResult] = []
        for business in deduped[:5]:
            if not business.website:
                continue
            for url in self.collector.contact_page_urls(business.website, 4)[1:]:
                urls.append(
                    SearchResult(
                        title=business.name or "Business contact page",
                        url=url,
                        source="Official Website",
                        source_type="official_website",
                        adapter_name="Official Website",
                    )
                )
        if not urls:
            research_job_service.enrichment(db, job, "no_enrichment_targets")
            return deduped
        enriched = await self.collector.collect(
            urls,
            parsed,
            on_failure=lambda result: self._collection_failed(session_id, result.url),
            on_crawl_event=lambda event, message: self._event(session_id, event, message),
        )
        for source in enriched:
            for target in deduped:
                if source.website and source.website == target.website:
                    existing = {(item.field, item.value, item.source) for item in target.evidence}
                    for item in source.evidence:
                        key = (item.field, item.value, item.source)
                        if key not in existing:
                            target.evidence.append(item)
                    await self._event(session_id, "business_enriched", f"Business enriched: {target.name}", job.stage_progress)
                    break
        research_job_service.enrichment(db, job, "completed")
        return deduped

    async def _event(self, session_id: int, event: str, message: str, progress: int | None = None, status: str = "running") -> None:
        if progress is not None and "Progress:" not in message:
            message = f"{message} | Progress: {progress}%"
        elapsed_seconds = round(time.perf_counter() - self._started_at.get(session_id, time.perf_counter()), 2)
        await timeline_hub.publish(
            TimelineEvent(
                session_id=session_id,
                event=event,
                message=message,
                status=status,
                elapsed_seconds=elapsed_seconds,
                stage=self._stage_from_message(message, event),
                progress=float(progress or 0),
            )
        )

    def _stage_from_message(self, message: str, event: str) -> str | None:
        if event == "stage_changed" and "Stage changed:" in message:
            return message.split("Stage changed:", 1)[1].split("|", 1)[0].strip()
        stage_events = {
            "job_started": "planning",
            "business_candidate_found": "discovering",
            "url_processed": "discovering",
            "business_verified": "verifying",
            "business_enriched": "enriching",
            "report_ready": "reporting",
            "job_completed": "completed",
        }
        return stage_events.get(event)

    def _risk(self, dna_score: int, conflict_count: int) -> str:
        if conflict_count >= 2 or dna_score < 55:
            return "HIGH"
        if conflict_count == 1 or dna_score < 75:
            return "MEDIUM"
        return "LOW"

    def _timeline_json(self, session_id: int) -> str:
        events = [
            {
                "event": item.event,
                "message": item.message,
                "status": item.status,
                "elapsed_seconds": item.elapsed_seconds,
            }
            for item in timeline_hub.history(session_id)
        ]
        return json.dumps(events)

    def _cache_key(self, category: str, location: str, demo_mode: bool, offline_mode: bool, mode: str) -> str:
        return f"{category.strip().lower()}::{location.strip().lower()}::mode={mode}::demo={int(demo_mode)}::offline={int(offline_mode)}"

    def _store_cache(self, db: Session, session: ResearchSession) -> None:
        if not session.category or not session.location:
            return
        settings = get_settings()
        mode = self._session_modes.get(session.id) or self.search._mode(settings)
        cache_key = self._cache_key(session.category, session.location, settings.argus_demo_mode, getattr(settings, "argus_offline_mode", False), mode)
        expires_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(seconds=settings.argus_cache_ttl_seconds)
        cache = db.execute(select(ResearchCache).where(ResearchCache.cache_key == cache_key)).scalars().first()
        if cache:
            cache.session_id = session.id
            cache.demo_mode = settings.argus_demo_mode
            cache.expires_at = expires_at
        else:
            db.add(
                ResearchCache(
                    cache_key=cache_key,
                    session_id=session.id,
                    demo_mode=settings.argus_demo_mode,
                    expires_at=expires_at,
                )
            )

    def _mode_label(self, mode: str) -> str:
        return {
            "online": "Online Research",
            "offline": "Offline Competition",
            "demo": "Demo Dataset",
            "auto": "Auto",
            "auto_fallback": "Auto Fallback",
        }.get(mode, mode)

    def _normalize_requested_mode(self, mode: str | None) -> str | None:
        if not mode:
            return None
        normalized = mode.strip().lower()
        if normalized in {"online", "offline", "demo", "auto"}:
            return normalized
        return None


research_service = ResearchService()
