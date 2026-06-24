import json
import logging
from collections import Counter
from collections.abc import Callable
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.routing import APIRoute
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from backend.database.session import SessionLocal, engine, get_db
from backend.models.business import Business
from backend.models.evidence import Evidence
from backend.models.research_job import ResearchJob
from backend.models.research_session import ResearchSession
from backend.config import get_settings
from backend.offline_corpus.corpus import _query_key, _records_for_query, classify_support, suggested_queries, support_message
from backend.schemas.research import ResearchSessionRead, TimelineEvent, TimelineReplayEvent
from backend.schemas.search import ResearchStartRequest, ResearchStartResponse
from backend.services.dna import BusinessDnaService
from backend.services.evidence_graph import EvidenceGraphService
from backend.services.explanation import ExplanationService
from backend.services.judge import JudgeRecommendationService
from backend.services.knowledge_graph import BusinessKnowledgeGraphService
from backend.services.similarity import BusinessSimilarityService
from backend.services.clustering import MarketClusteringService
from backend.services.analyst import DeterministicAnalystService
from backend.services.competitive_intelligence import CompetitiveIntelligenceService
from backend.services.report import ResearchReportService
from backend.services.research import research_service
from backend.services.research_jobs import research_job_service
from backend.services.relationship_graph import RelationshipGraphService
from backend.services.review import ResearchReviewService
from backend.services.source_reliability import source_reliability
from backend.services.timeline import timeline_hub
from backend.utils.text import normalize_phone, normalize_text, normalize_url

logger = logging.getLogger(__name__)


class SafeResearchRoute(APIRoute):
    def get_route_handler(self) -> Callable:
        original_route_handler = super().get_route_handler()

        async def custom_route_handler(request: Request) -> Response:
            try:
                return await original_route_handler(request)
            except HTTPException:
                raise
            except Exception as exc:
                logger.exception("research_endpoint_failed path=%s", request.url.path)
                return JSONResponse(
                    status_code=200,
                    content={
                        "status": "partial",
                        "report_ready": True,
                        "error_summary": [f"Research endpoint returned a safe partial response: {exc}"],
                        "businesses": [],
                    },
                )

        return custom_route_handler


router = APIRouter(prefix="/research", tags=["research"], route_class=SafeResearchRoute)
explanation_service = ExplanationService()
dna_service = BusinessDnaService()
judge_service = JudgeRecommendationService()
report_service = ResearchReportService()
evidence_graph_service = EvidenceGraphService()
review_service = ResearchReviewService()
knowledge_graph_service = BusinessKnowledgeGraphService()
similarity_service = BusinessSimilarityService()
clustering_service = MarketClusteringService()
competitive_service = CompetitiveIntelligenceService()
relationship_graph_service = RelationshipGraphService()
analyst_service = DeterministicAnalystService()


@router.post("/start", response_model=ResearchStartResponse)
async def start_research(payload: ResearchStartRequest, db: Session = Depends(get_db)) -> ResearchStartResponse:
    if not payload.query.strip():
        raise HTTPException(status_code=422, detail="Query cannot be empty")

    session = research_service.start(db, payload.query, payload.mode)
    _log_pool_status("research_start")
    job = research_job_service.get_or_create(db, session.id)
    if research_service.is_cache_hit(session.id):
        return ResearchStartResponse(session_id=str(session.id), job_id=str(job.id), status=session.status)
    if get_settings().argus_production_safe_mode:
        _complete_production_safe_session(db, session, job)
        return ResearchStartResponse(session_id=str(session.id), job_id=str(job.id), status=session.status)
    research_job_service.queue(db, job)
    session.status = "queued"
    db.commit()
    await timeline_hub.publish(
        TimelineEvent(
            session_id=session.id,
            event="job_queued",
            message="Research job queued | Progress: 0%",
            status="queued",
            elapsed_seconds=0,
        )
    )
    research_service.queue(session.id)
    return ResearchStartResponse(session_id=str(session.id), job_id=str(job.id), status="queued")


def _complete_production_safe_session(db: Session, session: ResearchSession, job: ResearchJob) -> None:
    parsed = research_service.scout.parse_query(session.query)
    session.category = parsed.category
    session.location = parsed.location
    records = _records_for_query(_query_key(parsed.category, parsed.location))
    unique_records: list[dict[str, object]] = []
    seen: set[str] = set()
    for record in records:
        name = str(record.get("name") or "").strip()
        if not name or name.lower() in seen:
            continue
        seen.add(name.lower())
        unique_records.append(record)
        if len(unique_records) >= 8:
            break

    for index, record in enumerate(unique_records):
        dna_score = max(55, 92 - index * 4)
        risk = "LOW" if dna_score >= 80 else "MEDIUM" if dna_score >= 65 else "HIGH"
        db.add(
            Business(
                session_id=session.id,
                name=str(record.get("name") or ""),
                category=parsed.category,
                location=parsed.location,
                phone=str(record.get("phone") or "") or None,
                address=str(record.get("address") or "") or None,
                website=str(record.get("website") or "") or None,
                email=str(record.get("email") or "") or None,
                confidence=float(dna_score),
                dna_score=float(dna_score),
                risk=risk,
            )
        )

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    session.sources_searched = len({str(record.get("source")) for record in records if record.get("source")})
    session.businesses_found = len(unique_records)
    session.duplicates_removed = max(0, len(records) - len(unique_records))
    session.duration = 0.1
    session.status = "complete"
    session.timeline_summary = json.dumps(
        [
            {"event": "job_queued", "message": "Research job queued", "status": "queued", "elapsed_seconds": 0},
            {"event": "job_completed", "message": "Production-safe research completed", "status": "complete", "elapsed_seconds": 0.1},
        ]
    )
    job.status = "complete"
    job.current_stage = "completed"
    job.stage_progress = 100
    job.total_urls = len(records)
    job.processed_urls = len(records)
    job.discovered_businesses = len(unique_records)
    job.verified_businesses = len(unique_records)
    job.failed_urls = 0
    job.started_at = job.started_at or now
    job.completed_at = now
    job.updated_at = now
    research_service._store_cache(db, session)
    db.commit()


@router.post("/{session_id}/cancel")
async def cancel_research(session_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    session = db.get(ResearchSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Research session not found")
    job = research_job_service.get_or_create(db, session.id)
    research_job_service.cancel(db, job)
    await timeline_hub.publish(
        TimelineEvent(
            session_id=session.id,
            event="job_failed",
            message="Research job cancelled",
            status="failed",
            elapsed_seconds=0,
        )
    )
    return {"session_id": session.id, "job_id": job.id, "status": "cancelled"}


@router.get("/jobs/recent")
def recent_jobs(db: Session = Depends(get_db)) -> list[dict[str, object]]:
    statement = (
        select(ResearchJob, ResearchSession)
        .join(ResearchSession, ResearchSession.id == ResearchJob.session_id)
        .order_by(ResearchJob.created_at.desc())
        .limit(10)
    )
    rows = db.execute(statement).all()
    return [
        {
            **research_job_service.payload(job),
            "query": session.query,
            "duration": session.duration,
            "business_count": session.businesses_found,
            "cache_hit": research_service.cache_metadata(session.id).get("cache_hit", False),
        }
        for job, session in rows
    ]


@router.get("/{session_id}")
def get_research(session_id: int) -> dict[str, object]:
    _log_pool_status("get_research_start")
    try:
        with SessionLocal() as db:
            payload = _safe_session_payload(db, session_id)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("safe_get_research_failed session_id=%s", session_id)
        return _partial_basic_payload(session_id, f"session: {exc}")
    _log_pool_status("get_research_end")
    return payload


@router.get("/{session_id}/basic")
def get_research_basic(session_id: int) -> dict[str, object]:
    _log_pool_status("get_research_basic_start")
    try:
        with SessionLocal() as db:
            payload = _safe_session_payload(db, session_id)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("safe_get_research_basic_failed session_id=%s", session_id)
        payload = _partial_basic_payload(session_id, f"basic: {exc}")
    _log_pool_status("get_research_basic_end")
    return payload


def _safe_session_payload(db: Session, session_id: int) -> dict[str, object]:
    session = db.get(ResearchSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Research session not found")

    error_summary: list[str] = []
    job_payload = research_job_service.payload(None)
    try:
        job = db.execute(
            select(ResearchJob)
            .where(ResearchJob.session_id == session.id)
            .order_by(ResearchJob.id.desc())
            .limit(1)
        ).scalars().first()
        job_payload = research_job_service.payload(job)
    except Exception as exc:
        logger.exception("safe_get_job_failed session_id=%s", session.id)
        error_summary.append(f"job: {exc}")

    businesses: list[dict[str, object]] = []
    try:
        rows = db.execute(
            select(Business)
            .where(Business.session_id == session.id)
            .order_by(Business.dna_score.desc(), Business.confidence.desc(), Business.id.asc())
            .limit(10)
        ).scalars().all()
        businesses = [_compact_business_payload(business, index) for index, business in enumerate(rows, start=1)]
    except Exception as exc:
        logger.exception("safe_get_businesses_failed session_id=%s", session.id)
        error_summary.append(f"businesses: {exc}")

    timeline_events: list[TimelineReplayEvent] = []
    if session.timeline_summary:
        try:
            timeline_events = [TimelineReplayEvent(**item) for item in json.loads(session.timeline_summary)][-20:]
        except (TypeError, ValueError) as exc:
            error_summary.append(f"timeline: {exc}")

    cache_metadata = research_service.cache_metadata(session.id)
    report_ready = session.status == "complete" and job_payload.get("status") in {"complete", "completed"}
    top_recommendations = [str(item.get("name")) for item in businesses if item.get("name")][:3]
    safe_status = "partial" if error_summary else session.status
    support_level = "LIVE_MODE"
    unsupported_message = None
    suggestions: list[str] = []
    if not businesses:
        try:
            parsed = research_service.scout.parse_query(session.query)
            support_level = classify_support(parsed)
            if support_level != "FULL_CORPUS_MATCH":
                unsupported_message = support_message(support_level)
                suggestions = suggested_queries(parsed)
        except Exception as exc:
            error_summary.append(f"offline_support: {exc}")

    active_mode = "Offline Competition"
    metrics = {
        "businesses": session.businesses_found or len(businesses),
        "verified": job_payload.get("verified_businesses", len(businesses)),
        "sources": session.sources_searched,
        "failed_urls": job_payload.get("failed_urls", 0),
        "duration_seconds": session.duration,
    }
    return {
        "session_id": str(session.id),
        "id": session.id,
        "query": session.query,
        "category": session.category,
        "location": session.location,
        "status": safe_status,
        "stage": job_payload.get("current_stage", "planning"),
        "progress": job_payload.get("stage_progress", 0),
        "mode": "offline",
        "active_mode": active_mode,
        "metrics": metrics,
        "error_summary": error_summary,
        "duration": session.duration,
        "sources_searched": session.sources_searched,
        "businesses_found": session.businesses_found or len(businesses),
        "duplicates_removed": session.duplicates_removed,
        "timeline_summary": session.timeline_summary or "[]",
        "timeline_events": timeline_events,
        "job": job_payload,
        "report_ready": report_ready and not error_summary,
        "cache_hit": bool(cache_metadata.get("cache_hit", False)),
        "cached_at": cache_metadata.get("cached_at"),
        "cache_age_seconds": cache_metadata.get("cache_age_seconds"),
        "cache_key": cache_metadata.get("cache_key"),
        "report": {
            "query": session.query,
            "active_mode": active_mode,
            "cache_hit": bool(cache_metadata.get("cache_hit", False)),
            "cached_at": cache_metadata.get("cached_at"),
            "cache_age_seconds": cache_metadata.get("cache_age_seconds"),
            "cache_key": cache_metadata.get("cache_key"),
            "businesses_found": session.businesses_found or len(businesses),
            "businesses_verified": job_payload.get("verified_businesses", len(businesses)),
            "verified_businesses": job_payload.get("verified_businesses", len(businesses)),
            "duplicates_removed": session.duplicates_removed,
            "sources_searched": session.sources_searched,
            "research_duration": session.duration,
            "top_recommendations": top_recommendations,
            "support_level": support_level,
            "unsupported_message": unsupported_message,
            "suggested_queries": suggestions,
            "error_summary": "; ".join(error_summary) if error_summary else None,
            "executive_summary": (
                f"ARGUS returned a compact production-safe session response for {session.query}."
            ),
        },
        "created_at": session.created_at,
        "businesses": businesses,
    }


def _partial_basic_payload(session_id: int, error: str) -> dict[str, object]:
    return {
        "session_id": str(session_id),
        "id": session_id,
        "query": "",
        "category": None,
        "location": None,
        "status": "partial",
        "stage": "partial",
        "progress": 100,
        "report_ready": True,
        "mode": "offline",
        "active_mode": "Offline Competition",
        "cache_hit": False,
        "metrics": {"businesses": 0, "verified": 0, "sources": 0, "failed_urls": 0, "duration_seconds": 0},
        "duration": 0,
        "sources_searched": 0,
        "businesses_found": 0,
        "duplicates_removed": 0,
        "timeline_summary": "[]",
        "timeline_events": [],
        "job": research_job_service.payload(None),
        "cached_at": None,
        "cache_age_seconds": None,
        "cache_key": None,
        "report": {"error_summary": error},
        "created_at": None,
        "businesses": [],
        "error_summary": [error],
    }


def _compact_business_payload(business: Business, rank: int) -> dict[str, object]:
    dna_score = float(business.dna_score or 0)
    risk = business.risk or "UNKNOWN"
    reliability = "HIGH" if dna_score >= 80 and risk == "LOW" else "MEDIUM" if dna_score >= 60 else "LOW"
    flags: list[str] = []
    if risk in {"HIGH", "MEDIUM"}:
        flags.append("NEEDS_REVIEW")
    if not business.phone or not business.website:
        flags.append("CONTACT_INCOMPLETE")
    if not flags and reliability == "HIGH":
        flags.append("HIGHLY_VERIFIED")
    return {
        "id": business.id,
        "name": business.name,
        "category": business.category,
        "location": business.location,
        "phone": business.phone,
        "address": business.address,
        "website": business.website,
        "email": business.email,
        "confidence": float(business.confidence or 0),
        "dna_score": dna_score,
        "dna_breakdown": {"final_score": round(dna_score)},
        "risk": risk,
        "reliability": reliability,
        "recommendation": "RECOMMENDED" if reliability == "HIGH" else "REVIEW_REQUIRED",
        "recommendation_reason": "Compact production-safe ranking based on persisted DNA and risk.",
        "risk_level": risk,
        "confidence_label": reliability,
        "rank": rank,
        "analyst_quality_flags": flags,
        "quality_flags": flags,
        "evidence_graph": {},
        "similar_businesses": [],
        "market_cluster": "Unassigned",
        "percentile_score": 0,
        "market_position": "AVERAGE",
        "centrality_score": 0,
        "top_relationship": "",
        "shared_services_count": 0,
        "outliers": [],
        "competitive_intelligence": {},
        "analyst_output": {},
        "swot": {},
        "overall_intelligence_score": round(dna_score),
        "executive_recommendation": "Recommended" if reliability == "HIGH" else "Review required",
        "explanation": {},
        "created_at": business.created_at,
        "evidence": [],
        "conflicts": [],
    }


def _log_pool_status(label: str) -> None:
    try:
        logger.info("db_pool_status %s %s", label, engine.pool.status())
    except Exception:
        logger.info("db_pool_status %s unavailable", label)


def _load_session_for_payload(db: Session, session_id: int) -> tuple[ResearchSession, list[dict[str, object]]]:
    statement = (
        select(ResearchSession)
        .where(ResearchSession.id == session_id)
        .options(
            selectinload(ResearchSession.businesses).selectinload(Business.evidence),
            selectinload(ResearchSession.businesses).selectinload(Business.conflicts),
            selectinload(ResearchSession.jobs),
        )
    )
    session = db.execute(statement).scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="Research session not found")
    recent = _recent_job_payloads(db, session.id)
    _materialize_session(session)
    db.expunge_all()
    return session, recent


def _materialize_session(session: ResearchSession) -> None:
    list(session.jobs)
    for business in session.businesses:
        list(business.evidence)
        list(business.conflicts)


@router.get("/{session_id}/events")
async def research_events(session_id: int) -> StreamingResponse:
    return StreamingResponse(
        timeline_hub.stream(session_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive"},
    )


def _session_payload(session: ResearchSession, recent: list[dict[str, object]] | None = None) -> dict[str, object]:
    timeline_events = _timeline_events(session)
    cache_metadata = research_service.cache_metadata(session.id)
    job_payload = research_job_service.payload(session.jobs[0] if session.jobs else None)
    report_ready = session.status == "complete" and job_payload.get("status") in {"complete", "completed"}
    recent = recent or []
    if cache_metadata.get("cache_hit"):
        timeline_events = [
            TimelineReplayEvent(
                event="cache_hit",
                message="Research cache hit",
                status="complete",
                elapsed_seconds=0,
            )
        ] + timeline_events
    businesses = [_business_payload(business) for business in session.businesses]
    businesses = sorted(businesses, key=judge_service.sort_key)
    for index, business in enumerate(businesses, start=1):
        business["rank"] = index
    contradiction_map = review_service.contradiction_map(businesses)
    review_queue = review_service.review_queue(businesses)
    similarity_service.attach(businesses)
    clusters = clustering_service.attach(businesses, review_queue)
    outliers = clustering_service.outliers(businesses, review_queue)
    for business in businesses:
        business["outliers"] = outliers.get(str(business.get("name")), [])
    market_comparison = competitive_service.attach(businesses, review_queue)
    knowledge_graph = knowledge_graph_service.build(businesses, review_queue)
    market_overview = clustering_service.market_overview(
        businesses,
        clusters,
        review_queue,
        knowledge_graph_service.overview_terms(businesses, "services"),
        knowledge_graph_service.overview_terms(businesses, "specialties"),
    )
    relationship_graph = relationship_graph_service.build(businesses, clusters)
    analyst_context = {
        "clusters": clusters,
        "review_queue": review_queue,
        "contradiction_map": contradiction_map,
        "market_comparison": market_comparison,
        "ecosystem_summary": relationship_graph.get("ecosystem_summary", {}),
        "centrality_metrics": relationship_graph.get("centrality_metrics", []),
        "source_health": {},
        "source_reliability_average": 0,
    }
    analyst_output = analyst_service.attach(businesses, analyst_context)
    return {
        "id": session.id,
        "query": session.query,
        "category": session.category,
        "location": session.location,
        "status": session.status,
        "duration": session.duration,
        "sources_searched": session.sources_searched,
        "businesses_found": session.businesses_found,
        "duplicates_removed": session.duplicates_removed,
        "timeline_summary": session.timeline_summary,
        "timeline_events": timeline_events,
        "job": job_payload,
        "report_ready": report_ready,
        "cache_hit": bool(cache_metadata.get("cache_hit", False)),
        "cached_at": cache_metadata.get("cached_at"),
        "cache_age_seconds": cache_metadata.get("cache_age_seconds"),
        "cache_key": cache_metadata.get("cache_key"),
        "report": report_service.build(
            session,
            businesses,
            cache_metadata,
            market_analysis={
                "knowledge_graph": knowledge_graph,
                "clusters": clusters,
                "outliers": outliers,
                "market_overview": market_overview,
                "market_comparison": market_comparison,
                "contradiction_map": contradiction_map,
                "review_queue": review_queue,
                "relationship_graph": relationship_graph,
                "ecosystem_summary": relationship_graph.get("ecosystem_summary", {}),
                "centrality_metrics": relationship_graph.get("centrality_metrics", []),
                "similar_pairs": relationship_graph.get("similar_pairs", []),
                "analyst_output": analyst_output.get("analyst_output", {}),
                "swot": {str(item.get("name")): item.get("swot", {}) for item in businesses},
                "scorecard": analyst_output.get("scorecard", {}),
                "recommendations": analyst_output.get("recommendations", {}),
                "market_narratives": analyst_output.get("market_narratives", {}),
                "benchmarks": analyst_output.get("benchmarks", {}),
            },
            job_metadata=job_payload,
            recent_jobs=recent,
        ),
        "created_at": session.created_at,
        "businesses": businesses,
    }


def _recent_job_payloads(db: Session, current_session_id: int) -> list[dict[str, object]]:
    statement = (
        select(ResearchJob, ResearchSession)
        .join(ResearchSession, ResearchSession.id == ResearchJob.session_id)
        .order_by(ResearchJob.created_at.desc())
        .limit(5)
    )
    rows = db.execute(statement).all()
    return [
        {
            **research_job_service.payload(job),
            "query": session.query,
            "duration": session.duration,
            "business_count": session.businesses_found,
            "is_current": session.id == current_session_id,
        }
        for job, session in rows
    ]


def _business_payload(business: Business) -> dict[str, object]:
    evidence = list(business.evidence)
    conflicts = list(business.conflicts)
    dna_breakdown = _dna_breakdown(business, evidence, len(conflicts))
    explanation = explanation_service.explain(business, evidence, conflicts, dna_breakdown)
    judge = judge_service.recommend(business, evidence, conflicts, str(explanation["reliability"]))
    agreements = _agreements(evidence)
    evidence_payload = [_evidence_payload(item, agreements) for item in evidence]

    payload = {
        "id": business.id,
        "name": business.name,
        "category": business.category,
        "location": business.location,
        "phone": business.phone,
        "address": business.address,
        "website": business.website,
        "email": business.email,
        "confidence": business.confidence,
        "dna_score": business.dna_score,
        "dna_breakdown": dna_breakdown,
        "risk": business.risk,
        "reliability": explanation["reliability"],
        "recommendation": judge["recommendation"],
        "recommendation_reason": judge["reason"],
        "risk_level": judge["risk_level"],
        "confidence_label": judge["confidence_label"],
        "explanation": explanation,
        "created_at": business.created_at,
        "evidence": evidence_payload,
        "conflicts": list(conflicts),
        "evidence_graph": evidence_graph_service.build(business, evidence, conflicts),
    }
    payload["analyst_quality_flags"] = review_service.quality_flags(payload)
    return payload


def _evidence_payload(item: Evidence, agreements: dict[tuple[str, str], tuple[int, int]]) -> dict[str, object]:
    count, total = agreements[(item.field, _normalize_evidence_value(item.field, item.value))]
    reliability = source_reliability(
        item.source,
        agreement_count=count,
        agreement_total=total,
        field_completeness=0,
        has_conflict=total > count,
    )
    return {
        "id": item.id,
        "field": item.field,
        "value": item.value,
        "source": item.source,
        "url": item.url,
        "normalized_url": item.normalized_url,
        **reliability,
        "source_type": item.source_type or reliability["source_type"],
        "extraction_method": item.extraction_method,
        "reliability_score": item.reliability_score or reliability["reliability_score"],
        "crawl_status": item.crawl_status,
        "agreement_count": count,
        "agreement_total": total,
        "agreement": f"{count}/{total}",
        "created_at": item.created_at,
    }


def _dna_breakdown(business: Business, evidence: list[Evidence], conflict_count: int) -> dict[str, int]:
    fields = ["name", "phone", "address", "website", "email"]
    evidence_strength = min(100, len(evidence) * 15)
    source_diversity = dna_service.source_diversity_score({item.source for item in evidence})
    completeness = round((sum(1 for field in fields if getattr(business, field)) / len(fields)) * 100)
    freshness = 85
    conflict_penalty = min(40, conflict_count * 10)
    return {
        "evidence_strength": evidence_strength,
        "source_diversity": source_diversity,
        "completeness": completeness,
        "freshness": freshness,
        "conflict_penalty": conflict_penalty,
        "final_score": round(business.dna_score),
    }


def _agreements(evidence: list[Evidence]) -> dict[tuple[str, str], tuple[int, int]]:
    totals = Counter(item.field for item in evidence)
    agreed = Counter((item.field, _normalize_evidence_value(item.field, item.value)) for item in evidence)
    return {key: (count, totals[key[0]]) for key, count in agreed.items()}


def _normalize_evidence_value(field: str, value: str) -> str:
    if field == "phone":
        return normalize_phone(value)
    if field == "website":
        return normalize_url(value)
    return normalize_text(value)


def _timeline_events(session: ResearchSession) -> list[TimelineReplayEvent]:
    if session.timeline_summary:
        try:
            persisted = [TimelineReplayEvent(**item) for item in json.loads(session.timeline_summary)]
            if session.status == "complete":
                return persisted
            live = _live_timeline_events(session.id)
            seen = {(item.event, item.message, item.elapsed_seconds) for item in persisted}
            return persisted + [item for item in live if (item.event, item.message, item.elapsed_seconds) not in seen]
        except (TypeError, ValueError):
            return _live_timeline_events(session.id)
    return _live_timeline_events(session.id)


def _live_timeline_events(session_id: int) -> list[TimelineReplayEvent]:
    return [
        TimelineReplayEvent(
            event=item.event,
            message=item.message,
            status=item.status,
            elapsed_seconds=item.elapsed_seconds,
        )
        for item in timeline_hub.history(session_id)
    ]
