import asyncio
from abc import ABC, abstractmethod
from urllib.parse import quote_plus

import httpx
from bs4 import BeautifulSoup

from backend.adapters import default_adapters
from backend.adapters.base_adapter import SourceAdapter
from backend.config import get_settings
from backend.data.demo_businesses import demo_search_results
from backend.offline_corpus.corpus import offline_targets, search_offline
from backend.schemas.search import ParsedQuery, SearchResult, SourceTarget
from backend.services.source_planner import SourcePlannerService
from backend.services.url_quality import UrlQualityService


class SearchProvider(ABC):
    name: str

    @abstractmethod
    async def search(
        self,
        parsed_query: ParsedQuery,
        limit: int = 5,
        query_text: str | None = None,
        source_type: str = "general_search",
    ) -> list[SearchResult]:
        """Return search results for a parsed business query."""


class HtmlSearchProvider(SearchProvider):
    def __init__(self, name: str, url_template: str, selector: str):
        self.name = name
        self.url_template = url_template
        self.selector = selector

    async def search(
        self,
        parsed_query: ParsedQuery,
        limit: int = 5,
        query_text: str | None = None,
        source_type: str = "general_search",
    ) -> list[SearchResult]:
        settings = get_settings()
        query = quote_plus(query_text or f"{parsed_query.category} in {parsed_query.location}")
        url = self.url_template.format(query=query)
        headers = {"User-Agent": "Mozilla/5.0 ARGUS research bot"}

        timeout = getattr(settings, "argus_search_timeout_seconds", getattr(settings, "request_timeout_seconds", 10))
        async with httpx.AsyncClient(timeout=timeout, headers=headers) as client:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        results: list[SearchResult] = []
        for node in soup.select(self.selector):
            link = node if node.name == "a" else node.select_one("a")
            if not link or not link.get("href"):
                continue
            title = link.get_text(" ", strip=True)
            href = str(link["href"])
            if not title or href.startswith("/"):
                continue
            results.append(SearchResult(title=title, url=href, snippet="", source=self.name, source_type=source_type))
            if len(results) >= limit:
                break
        return results


class MockSearchProvider(SearchProvider):
    name = "Mock"

    async def search(
        self,
        parsed_query: ParsedQuery,
        limit: int = 5,
        query_text: str | None = None,
        source_type: str = "general_search",
    ) -> list[SearchResult]:
        location = parsed_query.location.title()
        category = parsed_query.category.title()
        samples = [
            (
                f"{location} Heart Specialists",
                "https://birminghamheart.example",
                f"{category} clinic at 2010 Brookwood Medical Center Dr, {location}, AL. Phone 205-555-0184. Email referrals@birminghamheart.example. Hours Mon-Fri 8am-5pm. Services echocardiography and vascular screening.",
            ),
            (
                f"Crestline Cardiology Center",
                "https://crestlinecardio.example",
                f"Preventive cardiology at 48 Office Park Dr, {location}, AL. Phone 205-555-0119. Email care@crestlinecardio.example. Hours Mon-Fri 8am-5pm. Services stress testing and heart rhythm monitoring.",
            ),
            (
                f"Southern Pulse Cardiology",
                "https://southernpulse.example",
                f"Interventional cardiology at 700 19th St S, {location}, AL. Phone 205-555-0267. Email info@southernpulse.example. Hours Mon-Fri 9am-4pm. Services imaging and cardiac rehab.",
            ),
            (
                f"Southern Pulse Cardiology",
                "https://directory.example/southern-pulse-cardio",
                f"Directory profile for Southern Pulse Cardiology at 700 19th St S, {location}, AL. Phone 205-555-0299. Services imaging and cardiac rehab.",
            ),
        ]
        return [
            SearchResult(title=title, url=url, snippet=snippet, source=self.name, source_type=source_type)
            for title, url, snippet in samples[:limit]
        ]


class DemoSearchProvider(SearchProvider):
    name = "ARGUS Demo Dataset"

    async def search(
        self,
        parsed_query: ParsedQuery,
        limit: int = 10,
        query_text: str | None = None,
        source_type: str = "demo_dataset",
    ) -> list[SearchResult]:
        limit = max(limit, 10)
        return [
            SearchResult(title=title, url=url, snippet=snippet, source=self.name, source_type=source_type)
            for title, url, snippet in demo_search_results(parsed_query)[:limit]
        ]


class OfflineSearchProvider(SearchProvider):
    name = "Offline Corpus"

    async def search(
        self,
        parsed_query: ParsedQuery,
        limit: int = 100,
        query_text: str | None = None,
        source_type: str = "general_search",
    ) -> list[SearchResult]:
        return search_offline(parsed_query, source_type=source_type, limit=max(limit, 100))


class SearchService:
    """Runs configured search providers and falls back to mock data if needed."""

    def __init__(self) -> None:
        settings = get_settings()
        self.providers: list[SearchProvider] = []
        self.online_providers: list[SearchProvider] = [
            HtmlSearchProvider(
                "DuckDuckGo",
                "https://duckduckgo.com/html/?q={query}",
                ".result__a",
            ),
            HtmlSearchProvider(
                "Bing",
                "https://www.bing.com/search?q={query}",
                "li.b_algo h2 a",
            ),
            HtmlSearchProvider(
                "Google",
                "https://www.google.com/search?q={query}",
                "a",
            ),
        ]
        self.planner = SourcePlannerService()
        self.url_quality = UrlQualityService()
        self.adapters: list[SourceAdapter] = default_adapters()
        self.last_metadata: dict[str, object] = {}
        mode = self._mode(settings)
        if mode == "offline":
            self.providers.append(OfflineSearchProvider())
        elif mode == "demo":
            self.providers.append(DemoSearchProvider())
        elif mode in {"online", "auto"}:
            self.providers.extend(self.online_providers)
        self.mock_provider = MockSearchProvider()

    async def search(self, parsed_query: ParsedQuery, limit_per_provider: int = 5, mode_override: str | None = None) -> tuple[list[SearchResult], int]:
        settings = get_settings()
        mode = mode_override or self._mode(settings)
        self.last_metadata = {
            "requested_mode": mode,
            "active_mode": mode,
            "fallback_used": False,
            "fallback_reason": None,
            "filtered_urls_count": 0,
            "filtered_urls": [],
            "failed_searches": [],
            "online_results_count": 0,
            "adapter_health": {},
            "adapter_events": [],
        }

        if mode == "online":
            return await self._online_search(parsed_query, settings)
        if mode == "auto":
            if not self.providers and getattr(settings, "argus_demo_mode", False):
                return await self._demo_search(parsed_query, settings, limit_per_provider)
            online_results, online_searched = await self._online_search(parsed_query, settings)
            self.last_metadata["online_results_count"] = len(online_results)
            if len(online_results) >= 5:
                self.last_metadata["active_mode"] = "online"
                return online_results, online_searched
            offline_results, offline_searched = await self._offline_search(parsed_query, settings)
            if offline_results:
                self.last_metadata["active_mode"] = "auto_fallback"
                self.last_metadata["fallback_used"] = True
                self.last_metadata["fallback_reason"] = "Online discovery returned fewer than 5 candidates"
                return offline_results, online_searched + offline_searched
            self.last_metadata["active_mode"] = "online"
            return online_results, online_searched
        if mode == "offline":
            return await self._offline_search(parsed_query, settings)
        if mode == "demo":
            return await self._demo_search(parsed_query, settings, limit_per_provider)
        return [], 0

    async def _demo_search(self, parsed_query: ParsedQuery, settings, limit_per_provider: int = 5) -> tuple[list[SearchResult], int]:
        searched = 0
        results: list[SearchResult] = []
        offline_mode = getattr(settings, "argus_offline_mode", False)
        demo_mode = getattr(settings, "argus_demo_mode", False)
        targets = [SourceTarget(source_type="demo_dataset", query=f"{parsed_query.category} {parsed_query.location}", label="Demo")]

        for target in targets:
            for provider in self.providers:
                searched += 1
                try:
                    results.extend(
                        await provider.search(
                            parsed_query,
                            limit=100 if offline_mode else min(limit_per_provider, settings.argus_max_results_per_source),
                            query_text=target.query,
                            source_type=target.source_type,
                        )
                    )
                except (httpx.HTTPError, ValueError):
                    continue

        if not results and demo_mode:
            results = await self.mock_provider.search(parsed_query, limit=limit_per_provider)
            searched = max(searched, 1)

        return self._dedupe_and_filter(results), searched

    async def _offline_search(self, parsed_query: ParsedQuery, settings) -> tuple[list[SearchResult], int]:
        searched = 0
        results: list[SearchResult] = []
        for target in offline_targets(parsed_query):
            searched += 1
            results.extend(await OfflineSearchProvider().search(parsed_query, limit=100, query_text=target.query, source_type=target.source_type))
        self.last_metadata["active_mode"] = "offline"
        return self._dedupe_and_filter(results), searched

    async def _online_search(self, parsed_query: ParsedQuery, settings) -> tuple[list[SearchResult], int]:
        targets = self.planner.plan(parsed_query, getattr(settings, "argus_max_source_queries", 12))
        max_pages = getattr(settings, "argus_max_pages_per_source", 3)
        providers = self.providers
        use_adapter_pack = bool(providers) and all(isinstance(provider, HtmlSearchProvider) for provider in providers)
        adapter_searches = 0
        if use_adapter_pack:
            adapter_results, adapter_searches = await self._adapter_search(parsed_query, targets, max_pages)
            if adapter_results:
                deduped = self._dedupe_and_filter(adapter_results)
                self.last_metadata["active_mode"] = "online"
                self.last_metadata["online_results_count"] = len(deduped)
                self.last_metadata["adapter_health"] = self.adapter_health()
                return deduped, adapter_searches

        searched = len(targets) * len(providers)
        if not providers:
            self.last_metadata["adapter_health"] = self.adapter_health()
            return [], 0

        async def provider_search(provider: SearchProvider, target: SourceTarget) -> list[SearchResult]:
            try:
                return await provider.search(
                    parsed_query,
                    limit=getattr(settings, "argus_max_results_per_query", 10),
                    query_text=target.query,
                    source_type=target.source_type,
                )
            except (httpx.HTTPError, ValueError, TimeoutError) as exc:
                failed = list(self.last_metadata.get("failed_searches", []))
                failed.append({"provider": provider.name, "query": target.query, "reason": str(exc)[:160]})
                self.last_metadata["failed_searches"] = failed
                return []

        batches = await asyncio.gather(
            *(provider_search(provider, target) for target in targets for provider in providers)
        )
        results = [item for batch in batches for item in batch]
        deduped = self._dedupe_and_filter(results)
        self.last_metadata["active_mode"] = "online"
        self.last_metadata["online_results_count"] = len(deduped)
        self.last_metadata["adapter_health"] = self.adapter_health()
        return deduped, searched + adapter_searches

    async def _adapter_search(
        self,
        parsed_query: ParsedQuery,
        targets: list[SourceTarget],
        max_pages: int,
    ) -> tuple[list[SearchResult], int]:
        adapter_jobs: list[tuple[SourceAdapter, SourceTarget, int]] = []
        for target in targets:
            for adapter in self._adapters_for_target(target):
                for page in range(1, max_pages + 1):
                    adapter_jobs.append((adapter, target, page))

        async def run_adapter(adapter: SourceAdapter, target: SourceTarget, page: int) -> list[SearchResult]:
            events = list(self.last_metadata.get("adapter_events", []))
            events.append({"event": "adapter_started", "adapter": adapter.adapter_name, "target": target.label, "page": page})
            self.last_metadata["adapter_events"] = events
            try:
                results = await adapter.discover(parsed_query, target, page)
            except Exception as exc:
                events = list(self.last_metadata.get("adapter_events", []))
                events.append({"event": "adapter_failed", "adapter": adapter.adapter_name, "target": target.label, "page": page, "reason": str(exc)[:160]})
                self.last_metadata["adapter_events"] = events
                return []
            events = list(self.last_metadata.get("adapter_events", []))
            events.append({"event": "adapter_finished", "adapter": adapter.adapter_name, "target": target.label, "page": page, "results": len(results)})
            for result in results:
                events.append({"event": "page_discovered", "adapter": adapter.adapter_name, "url": result.url})
            self.last_metadata["adapter_events"] = events
            return results

        batches = await asyncio.gather(*(run_adapter(adapter, target, page) for adapter, target, page in adapter_jobs))
        return [item for batch in batches for item in batch], len(adapter_jobs)

    def _adapters_for_target(self, target: SourceTarget) -> list[SourceAdapter]:
        label = target.label.lower()
        source_type = target.source_type
        matches = [
            adapter
            for adapter in self.adapters
            if adapter.adapter_name.lower() in label
            or adapter.source_type == source_type
            or (adapter.domain and adapter.domain.split(".")[0] in target.query.lower())
        ]
        if matches:
            return matches[:3]
        return [adapter for adapter in self.adapters if adapter.source_type in {source_type, "official_website"}][:2]

    def adapter_health(self) -> dict[str, object]:
        return {adapter.adapter_name: adapter.health() for adapter in self.adapters}

    def _dedupe_and_filter(self, results: list[SearchResult]) -> list[SearchResult]:
        unique: dict[str, SearchResult] = {}
        for result in results:
            if result.url.startswith("offline://") or result.url.startswith("demo://"):
                key = result.url
                unique.setdefault(key, result)
                continue
            reason = self.url_quality.reject_reason(result.url)
            if reason:
                filtered = list(self.last_metadata.get("filtered_urls", []))
                filtered.append({"url": result.url, "reason": reason})
                self.last_metadata["filtered_urls"] = filtered
                self.last_metadata["filtered_urls_count"] = len(filtered)
                continue
            key = self.url_quality.normalize(result.url)
            unique.setdefault(key, result.model_copy(update={"url": key}))
        return list(unique.values())

    def _mode(self, settings) -> str:
        configured = getattr(settings, "argus_mode", None)
        if configured:
            return str(configured).lower()
        if getattr(settings, "argus_offline_mode", False):
            return "offline"
        if getattr(settings, "argus_demo_mode", False):
            return "demo"
        return "online"
