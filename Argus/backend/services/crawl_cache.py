import hashlib
import json
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.config import get_settings
from backend.models.crawl_cache import CrawlCache
from backend.schemas.extraction import ExtractedBusiness, FieldEvidence
from backend.schemas.search import ParsedQuery, SearchResult
from backend.services.url_quality import UrlQualityService


class CrawlCacheService:
    """Persists per-URL crawl attempts and reusable extraction payloads."""

    def __init__(self) -> None:
        self.urls_seen: set[str] = set()

    def normalized_url(self, url: str) -> str:
        if url.startswith(("offline://", "demo://")):
            return url
        return UrlQualityService().normalize(url)

    def get_valid_success(self, db: Session, url: str) -> CrawlCache | None:
        normalized = self.normalized_url(url)
        now = self._now()
        cache = db.execute(select(CrawlCache).where(CrawlCache.normalized_url == normalized)).scalars().first()
        if cache and cache.status == "success" and cache.ttl_expires_at > now:
            return cache
        return None

    def is_valid_failure(self, db: Session, url: str) -> bool:
        normalized = self.normalized_url(url)
        now = self._now()
        cache = db.execute(select(CrawlCache).where(CrawlCache.normalized_url == normalized)).scalars().first()
        return bool(cache and cache.status == "failed" and cache.ttl_expires_at > now)

    def business_from_cache(self, cache: CrawlCache, parsed_query: ParsedQuery, result: SearchResult) -> ExtractedBusiness:
        payload = json.loads(cache.extracted_fields_json or "{}")
        evidence = [
            FieldEvidence(**item)
            for item in payload.get("evidence", [])
        ]
        business = ExtractedBusiness(
            name=payload.get("name"),
            category=parsed_query.category,
            location=parsed_query.location,
            phone=payload.get("phone"),
            address=payload.get("address"),
            website=payload.get("website"),
            email=payload.get("email"),
            services=payload.get("services"),
            working_hours=payload.get("working_hours"),
            source_url=result.url,
            source_name=payload.get("source_name") or result.source,
            evidence=evidence,
            raw_search_result=result,
        )
        return business

    def store_success(
        self,
        db: Session,
        result: SearchResult,
        business: ExtractedBusiness,
        text: str,
        html: str,
        http_status: int | None,
    ) -> None:
        normalized = self.normalized_url(result.url)
        now = self._now()
        payload = business.model_dump(mode="json")
        cache = self._get_or_create(db, result.url, normalized)
        cache.source_type = result.source_type
        cache.status = "success"
        cache.http_status = http_status
        cache.content_hash = hashlib.sha256(html.encode("utf-8", errors="ignore")).hexdigest() if html else None
        cache.extracted_text_preview = text[:500]
        cache.extracted_fields_json = json.dumps(payload)
        cache.error_message = None
        cache.last_attempted_at = now
        cache.last_success_at = now
        cache.attempt_count = (cache.attempt_count or 0) + 1
        cache.ttl_expires_at = now + timedelta(seconds=get_settings().argus_crawl_cache_ttl_seconds)
        db.commit()

    def store_failure(
        self,
        db: Session,
        result: SearchResult,
        error_message: str,
        http_status: int | None = None,
        status: str = "failed",
    ) -> None:
        normalized = self.normalized_url(result.url)
        now = self._now()
        cache = self._get_or_create(db, result.url, normalized)
        cache.source_type = result.source_type
        cache.status = status
        cache.http_status = http_status
        cache.error_message = error_message[:1000]
        cache.last_attempted_at = now
        cache.attempt_count = (cache.attempt_count or 0) + 1
        cache.ttl_expires_at = now + timedelta(seconds=get_settings().argus_crawl_cache_ttl_seconds)
        db.commit()

    def _get_or_create(self, db: Session, url: str, normalized: str) -> CrawlCache:
        cache = db.execute(select(CrawlCache).where(CrawlCache.normalized_url == normalized)).scalars().first()
        if cache:
            return cache
        cache = CrawlCache(
            url=url,
            normalized_url=normalized,
            ttl_expires_at=self._now() + timedelta(seconds=get_settings().argus_crawl_cache_ttl_seconds),
        )
        db.add(cache)
        db.flush()
        return cache

    def _now(self) -> datetime:
        return datetime.now(timezone.utc).replace(tzinfo=None)
