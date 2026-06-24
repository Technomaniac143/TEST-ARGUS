import asyncio
import json
import re
from urllib.parse import urljoin, urlparse

import httpx
import trafilatura
from bs4 import BeautifulSoup

from backend.config import get_settings
from backend.data.demo_businesses import get_demo_business
from backend.database.session import SessionLocal
from backend.offline_corpus.corpus import resolve_offline_url
from backend.schemas.extraction import ExtractedBusiness, FieldEvidence
from backend.schemas.search import ParsedQuery, SearchResult
from backend.services.crawl_cache import CrawlCacheService
from backend.services.source_reliability import source_reliability
from backend.utils.text import (
    EMAIL_RE,
    HOURS_RE,
    IMAGE_URL_RE,
    PHONE_RE,
    SOCIAL_LINK_RE,
    extract_links,
    extract_rating,
    extract_review_count,
    first_match,
)


class CollectorService:
    """Fetches candidate pages and extracts basic business fields."""

    def __init__(self) -> None:
        self.crawl_cache = CrawlCacheService()

    async def collect(
        self,
        results: list[SearchResult],
        parsed_query: ParsedQuery,
        on_failure=None,
        on_crawl_event=None,
    ) -> list[ExtractedBusiness]:
        settings = get_settings()
        semaphore = asyncio.Semaphore(settings.argus_max_concurrency)

        async def guarded_collect(result: SearchResult) -> ExtractedBusiness | None:
            async with semaphore:
                try:
                    try:
                        return await self.collect_one(result, parsed_query, on_crawl_event=on_crawl_event)
                    except TypeError as exc:
                        if "on_crawl_event" not in str(exc):
                            raise
                        return await self.collect_one(result, parsed_query)
                except Exception:
                    if on_failure:
                        await on_failure(result)
                    return None

        collected = await asyncio.gather(*(guarded_collect(result) for result in results))
        return [business for business in collected if business is not None]

    async def collect_one(self, result: SearchResult, parsed_query: ParsedQuery, on_crawl_event=None) -> ExtractedBusiness:
        demo_business = get_demo_business(result.url)
        if demo_business:
            business = demo_business.model_copy(deep=True)
            self._enrich_evidence_trace(business, result, "manual_demo", "success")
            return business

        html = ""
        text = result.snippet
        source_name = self._source_label(result.source_type, result.source)
        http_status: int | None = None
        crawl_status = "success"
        extraction_method = "regex"

        if not result.url.startswith(("offline://", "demo://")):
            with SessionLocal() as db:
                cached = self.crawl_cache.get_valid_success(db, result.url)
                if cached:
                    if on_crawl_event:
                        await on_crawl_event("crawl_cache_hit", f"Crawl cache hit: {result.url}")
                    return self.crawl_cache.business_from_cache(cached, parsed_query, result)
                if on_crawl_event:
                    await on_crawl_event("crawl_cache_miss", f"Crawl cache miss: {result.url}")

        try:
            settings = get_settings()
            if result.url.startswith("offline://"):
                html = resolve_offline_url(result.url).read_text(encoding="utf-8")
                extraction_method = "corpus_html"
                if on_crawl_event:
                    await on_crawl_event("crawl_succeeded", f"Crawl succeeded: {result.url}")
            else:
                async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
                    response = await client.get(result.url, follow_redirects=True)
                    http_status = getattr(response, "status_code", 200)
                    response.raise_for_status()
                    html = response.text
                    if result.source_type == "official_website":
                        pages = self.contact_page_urls(str(response.url), getattr(settings, "argus_max_pages_per_site", 4))
                        for page_url in pages[1:]:
                            try:
                                page_response = await client.get(page_url, follow_redirects=True)
                                if page_response.status_code < 400:
                                    html += "\n" + page_response.text
                            except httpx.HTTPError:
                                continue
                if on_crawl_event:
                    await on_crawl_event("crawl_succeeded", f"Crawl succeeded: {result.url}")
        except httpx.HTTPError:
            crawl_status = "failed"
            with SessionLocal() as db:
                self.crawl_cache.store_failure(db, result, "HTTP crawl failed", http_status=http_status)
            if on_crawl_event:
                await on_crawl_event("crawl_failed", f"Crawl failed: {result.url}")
            html = ""

        if html:
            extracted = trafilatura.extract(html) or ""
            soup = BeautifulSoup(html, "html.parser")
            text = "\n".join(part for part in [result.snippet, soup.get_text("\n", strip=True), extracted] if part)
        else:
            soup = BeautifulSoup("", "html.parser")

        structured = self._extract_json_ld(soup)
        if structured:
            extraction_method = "json_ld"
        link_text = " ".join(
            str(value)
            for value in [
                " ".join(link.get("href", "") for link in soup.select("a[href^='tel:']")),
                " ".join(link.get("href", "") for link in soup.select("a[href^='mailto:']")),
            ]
            if value
        )
        name = structured.get("name") or self._extract_name(result, soup)
        phone = structured.get("phone") or self._extract_labeled(text, "Phone") or first_match(PHONE_RE, link_text) or first_match(PHONE_RE, text)
        email = structured.get("email") or self._extract_labeled(text, "Email") or first_match(EMAIL_RE, link_text) or first_match(EMAIL_RE, text)
        working_hours = structured.get("working_hours") or self._extract_labeled(text, "Hours") or first_match(HOURS_RE, text)
        address = structured.get("address") or self._extract_address(text, parsed_query.location)
        services = self._extract_services(text, result.snippet)
        website = structured.get("website") or self._extract_labeled(text, "Website") or self._extract_website(result.url)
        rating = structured.get("rating") or extract_rating(text)
        review_count = structured.get("review_count") or extract_review_count(text)
        social_profiles = structured.get("social_profiles") or self._extract_social_links(soup, text)
        images_urls = structured.get("images_urls") or self._extract_images(soup, text)
        license_information = self._extract_labeled(text, "License Information")
        certifications = self._extract_labeled(text, "Certifications")
        awards = self._extract_labeled(text, "Awards")

        business = ExtractedBusiness(
            name=name,
            category=parsed_query.category,
            location=parsed_query.location,
            phone=phone,
            address=address,
            website=website,
            email=email,
            services=services,
            working_hours=working_hours,
            source_url=result.url,
            source_name=source_name,
            raw_search_result=result,
        )
        business.evidence = self._build_evidence(business, result, extraction_method, crawl_status)
        for field, value in {
            "rating": rating,
            "review_count": review_count,
            "license_information": license_information,
            "certifications": certifications,
            "awards": awards,
            "social_profiles": social_profiles,
            "images_urls": images_urls,
            "source_urls": result.url,
        }.items():
            if value:
                method = "json_ld" if field in structured else extraction_method
                business.evidence.append(self._field_evidence(field, value, source_name, result, method, crawl_status))
        if crawl_status == "success" and not result.url.startswith(("offline://", "demo://")):
            with SessionLocal() as db:
                self.crawl_cache.store_success(db, result, business, text, html, http_status)
        return business

    def _extract_name(self, result: SearchResult, soup: BeautifulSoup) -> str | None:
        h1 = soup.select_one("h1")
        if h1 and h1.get_text(" ", strip=True):
            return h1.get_text(" ", strip=True)
        og_title = soup.select_one("meta[property='og:title']")
        if og_title and og_title.get("content"):
            return str(og_title["content"]).strip()
        if soup.title and soup.title.string:
            title = soup.title.string.strip()
            if title:
                return re.split(r"\s[-|]\s", title)[0].strip()
        return result.title or None

    def _extract_website(self, url: str) -> str | None:
        if url.startswith("offline://"):
            return None
        parsed = urlparse(url)
        if parsed.scheme and parsed.netloc:
            return f"{parsed.scheme}://{parsed.netloc}"
        return url or None

    def _extract_address(self, text: str, location: str) -> str | None:
        if not text:
            return None
        labeled = self._extract_labeled(text, "Address")
        if labeled:
            return labeled
        pattern = re.compile(rf"\d{{1,6}}\s+[A-Za-z0-9 .'-]+,\s*{re.escape(location)}[^.\n]*", re.I)
        match = pattern.search(text)
        return match.group(0).strip() if match else None

    def _extract_services(self, text: str, snippet: str) -> str | None:
        labeled = self._extract_labeled(text, "Services")
        if labeled:
            return labeled
        source = snippet or text[:300]
        terms = [
            "cardiology",
            "echocardiography",
            "vascular",
            "stress testing",
            "heart rhythm",
            "imaging",
            "cardiac rehab",
        ]
        found = [term for term in terms if term in source.lower()]
        return ", ".join(dict.fromkeys(found)) if found else None

    def contact_page_urls(self, url: str, max_pages: int = 4) -> list[str]:
        base = self._extract_website(url)
        if not base:
            return [url]
        suffixes = ["", "/contact", "/about", "/services", "/team", "/locations"]
        return [urljoin(base, suffix) for suffix in suffixes[:max_pages]]

    def _extract_json_ld(self, soup: BeautifulSoup) -> dict[str, str]:
        data: dict[str, str] = {}
        supported_types = {
            "LocalBusiness",
            "MedicalBusiness",
            "Physician",
            "Dentist",
            "LegalService",
            "RoofingContractor",
            "Plumber",
            "Organization",
        }
        for script in soup.select("script[type='application/ld+json']"):
            try:
                payload = json.loads(script.string or "{}")
            except json.JSONDecodeError:
                continue
            for item in self._jsonld_items(payload):
                item_types = item.get("@type", [])
                if isinstance(item_types, str):
                    item_types = [item_types]
                if not supported_types.intersection(set(item_types)):
                    continue
                data.setdefault("name", self._string(item.get("name")))
                data.setdefault("phone", self._string(item.get("telephone")))
                data.setdefault("email", self._string(item.get("email")))
                data.setdefault("website", self._string(item.get("url")))
                data.setdefault("working_hours", self._string(item.get("openingHours")))
                data.setdefault("social_profiles", self._string(item.get("sameAs")))
                data.setdefault("images_urls", self._string(item.get("image")))
                address = item.get("address")
                if isinstance(address, dict):
                    data.setdefault(
                        "address",
                        ", ".join(
                            part
                            for part in [
                                self._string(address.get("streetAddress")),
                                self._string(address.get("addressLocality")),
                                self._string(address.get("addressRegion")),
                                self._string(address.get("postalCode")),
                            ]
                            if part
                        ),
                    )
                rating = item.get("aggregateRating")
                if isinstance(rating, dict):
                    data.setdefault("rating", self._string(rating.get("ratingValue")))
                    data.setdefault("review_count", self._string(rating.get("reviewCount") or rating.get("ratingCount")))
        return {key: value for key, value in data.items() if value}

    def _jsonld_items(self, payload) -> list[dict]:
        if isinstance(payload, dict):
            graph = payload.get("@graph")
            if isinstance(graph, list):
                return [item for item in graph if isinstance(item, dict)]
            return [payload]
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        return []

    def _string(self, value) -> str | None:
        if isinstance(value, list):
            return ", ".join(str(item) for item in value if item)
        if value is None:
            return None
        return str(value).strip() or None

    def _extract_social_links(self, soup: BeautifulSoup, text: str) -> str | None:
        links = " ".join(link.get("href", "") for link in soup.select("a[href]"))
        return extract_links(SOCIAL_LINK_RE, f"{text} {links}")

    def _extract_images(self, soup: BeautifulSoup, text: str) -> str | None:
        og_image = soup.select_one("meta[property='og:image']")
        images = []
        if og_image and og_image.get("content"):
            images.append(str(og_image["content"]))
        images.extend(str(image.get("src")) for image in soup.select("img[src]") if image.get("src"))
        return extract_links(IMAGE_URL_RE, f"{text} {' '.join(images)}")

    def _extract_labeled(self, text: str, label: str) -> str | None:
        pattern = re.compile(rf"^{re.escape(label)}:[ \t]*([^\n]*)", re.I | re.M)
        match = pattern.search(text)
        if not match:
            return None
        value = match.group(1).strip(" .|")
        return value or None

    def _source_label(self, source_type: str, fallback: str) -> str:
        labels = {
            "official_website": "Official Website",
            "directory": fallback or "Yellow Pages",
            "review_platform": fallback or "Yelp",
            "professional_directory": fallback or "Professional Directory",
            "government_license_registry": "Government License Registry",
            "healthcare_directory": "Healthcare Directory",
            "legal_directory": "Legal Directory",
            "public_review_platform": "Public Review Platform",
            "social_profile": fallback or "Social Profile",
            "general_search": fallback or "Search Result",
            "demo_dataset": fallback or "ARGUS Demo Dataset",
        }
        return labels.get(source_type, fallback or "Search Result")

    def _build_evidence(
        self,
        business: ExtractedBusiness,
        result: SearchResult,
        extraction_method: str,
        crawl_status: str,
    ) -> list[FieldEvidence]:
        evidence: list[FieldEvidence] = []
        source = business.source_name
        for field in ["name", "phone", "address", "website", "email", "services", "working_hours"]:
            value = getattr(business, field)
            if value:
                evidence.append(self._field_evidence(field, str(value), source, result, extraction_method, crawl_status))
        return evidence

    def _field_evidence(
        self,
        field: str,
        value,
        source: str,
        result: SearchResult,
        extraction_method: str,
        crawl_status: str,
    ) -> FieldEvidence:
        reliability = source_reliability(source)
        return FieldEvidence(
            field=field,
            value=str(value),
            source=source,
            url=result.url,
            normalized_url=self.crawl_cache.normalized_url(result.url),
            source_type=result.source_type,
            extraction_method=extraction_method,
            reliability_score=int(reliability["reliability_score"]),
            crawl_status=crawl_status,
        )

    def _enrich_evidence_trace(
        self,
        business: ExtractedBusiness,
        result: SearchResult,
        extraction_method: str,
        crawl_status: str,
    ) -> None:
        for item in business.evidence:
            item.normalized_url = item.normalized_url or self.crawl_cache.normalized_url(item.url or result.url)
            item.source_type = item.source_type or result.source_type
            item.extraction_method = extraction_method
            item.crawl_status = crawl_status
            item.reliability_score = int(source_reliability(item.source)["reliability_score"])
