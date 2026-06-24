# ARGUS Requirement Gap Audit

Audit date: 2026-06-21  
Scope: Current ARGUS implementation versus the official specification supplied in `ARGUS RESET`.

## Executive Summary

ARGUS currently works well as a demo-grade, deterministic business intelligence prototype. It has a stable FastAPI backend, a static frontend, demo-mode datasets, evidence receipts, deduplication, conflict detection, DNA scoring, source reliability labels, ranking, report output, exports, caching metadata, timeline replay, and Playwright smoke coverage.

The largest gap is that real-mode research is not yet a professional-scale research agent. Real public-source discovery is shallow, collector extraction is basic, collection is sequential, and many advanced fields are present mainly through deterministic demo data rather than public-source extraction. The system is challenge-presentable in demo mode, but real-mode judging would expose major gaps in scale, source breadth, and data quality.

## Requirement Matrix

| Requirement | Current Status | Risk | Exact Files Involved | Exact Fix Needed | Priority |
|---|---|---:|---|---|---:|
| Parse input into category/location | Implemented | Low | `backend/agents/scout.py`, `backend/services/research.py` | Improve parser for more query forms, plurals, and locations with commas. | P2 |
| AI-powered professional researcher behavior | Partial | High | `backend/services/research.py`, `backend/services/explanation.py`, `backend/services/judge.py` | Add real planning/research orchestration and optional approved AI reasoning layer later; current system is deterministic, not AI-powered. | P1 |
| Google search pages | Partial | High | `backend/services/search.py` | Current Google HTML adapter is fragile and not tested against blocks. Add robust public-search scraping strategy with rate limits and parser tests. | P1 |
| Bing | Partial | Medium | `backend/services/search.py` | Existing HTML adapter needs pagination, result normalization, and blocked-page handling. | P1 |
| DuckDuckGo | Partial | Medium | `backend/services/search.py` | Existing HTML adapter needs pagination, source metadata, and tests. | P1 |
| Official websites | Partial | High | `backend/services/collector.py`, `backend/data/demo_businesses.py` | Demo mode simulates official sources; real mode only visits discovered URLs and extracts basic regex fields. Add website classification and deeper crawl. | P1 |
| Yelp / Yellow Pages / LinkedIn / Facebook | Simulated | High | `backend/data/demo_businesses.py`, `backend/services/source_reliability.py` | Demo data labels these sources; real-mode adapters do not exist. Add public-page adapters where legally/technically feasible. | P1 |
| Industry directories / professional associations | Simulated | High | `backend/data/demo_businesses.py` | Add domain-specific directory adapters and source-class mapping. | P1 |
| Government licensing databases | Simulated | High | `backend/data/demo_businesses.py` | Add registry-specific lookup adapters by category/location. | P1 |
| Healthcare/legal/public review directories | Simulated | High | `backend/data/demo_businesses.py` | Add vertical-specific adapters and extraction schemas. | P1 |
| No paid APIs | Implemented | Low | `backend/services/search.py`, `requirements.txt` | Maintain this constraint. | P3 |
| No fabricated data in real mode | Implemented | Medium | `backend/services/search.py`, `backend/config.py` | Real mode avoids mock fallback, but verify all demo-only branches stay gated by `ARGUS_DEMO_MODE`. | P1 |
| Discover many businesses | Partial | High | `backend/services/search.py`, `backend/data/demo_businesses.py` | Demo returns 8 unique businesses. Real mode fetches limited search results. Add pagination, fan-out discovery, and source adapters. | P1 |
| Scale to hundreds/thousands/tens of thousands raw records | Simulated | High | `backend/services/report.py` | Demo report simulates scale metrics; no actual large-scale processing pipeline exists. Add queueing, pagination, batching, and durable job state. | P1 |
| Collect business_name | Implemented | Medium | `backend/services/collector.py`, `backend/data/demo_businesses.py` | Real extraction is title/search-result based. Improve structured data parsing. | P2 |
| Collect address | Partial | Medium | `backend/services/collector.py` | Regex only; add schema.org, contact page parsing, and directory parsers. | P2 |
| Collect phone | Partial | Medium | `backend/services/collector.py`, `backend/utils/text.py` | Regex works for simple US formats; add normalization and source-specific extraction. | P2 |
| Collect email | Partial | Medium | `backend/services/collector.py`, `backend/utils/text.py` | Regex works when visible; add contact-page crawl. | P2 |
| Collect website | Partial | Medium | `backend/services/collector.py` | Current website often equals result URL host; add official-site detection. | P2 |
| Collect working_hours | Partial | Medium | `backend/services/collector.py`, `backend/data/demo_businesses.py` | Demo has hours; real regex is basic. Add structured hours parser. | P2 |
| Collect rating/review_count | Simulated | High | `backend/data/demo_businesses.py` | Real collector does not persist rating/review_count as business fields. Add schema/model fields and source adapters. | P1 |
| Collect services/specialties/license/certifications/awards/social/images/source_urls | Partial | High | `backend/schemas/extraction.py`, `backend/models/business.py`, `backend/models/evidence.py`, `backend/data/demo_businesses.py` | Mostly evidence-only/demo-only. Add first-class schema/model fields or normalized evidence contract for all requested fields. | P1 |
| Never invent missing values | Partial | Medium | `backend/services/collector.py`, `backend/data/demo_businesses.py` | Real mode keeps missing values null; demo mode is curated. Ensure UI distinguishes demo mode from real research. | P1 |
| Cross-check verification | Partial | Medium | `backend/services/verification.py`, `backend/api/research.py` | Evidence is stored per field/source; confidence is simple count-based. Add agreement-aware verification by source class and consistency. | P1 |
| Conflict preservation | Implemented | Low | `backend/services/conflicts.py`, `backend/models/conflict.py`, `backend/services/verification.py` | Expand conflict logic beyond phone/address/website/email and include severity. | P2 |
| Deduplication by name/phone/address/website | Implemented | Medium | `backend/services/deduplication.py` | Current RapidFuzz rules work for demos; add clustering and explainable merge traces for scale. | P2 |
| Search summary report fields | Implemented | Low | `backend/services/report.py`, `backend/api/research.py`, `backend/schemas/research.py` | Maintain schema stability. | P3 |
| Ranked businesses | Implemented | Low | `backend/services/judge.py`, `backend/api/research.py`, `app.js` | Add explainable sort factors in API. | P2 |
| Data quality percentages | Implemented | Low | `backend/services/report.py` | Current license/working-hours percentages rely on evidence fields. Keep as report metrics. | P3 |
| Concurrent collection | Missing | High | `backend/services/collector.py`, `backend/services/research.py` | Replace sequential `for result in results` with bounded `asyncio.gather`, retries, and timeouts. | P1 |
| Streaming newly discovered businesses | Partial | Medium | `backend/services/research.py`, `backend/services/timeline.py`, `app.js` | Emits `business_discovered` after collection; not while search/discovery is actively streaming from live providers. | P1 |
| Incremental updates | Partial | Medium | `backend/services/timeline.py`, `app.js` | SSE events exist, but API result is mostly returned after full pipeline. Add job endpoint and progressive result retrieval. | P1 |
| Cache previous research | Partial | Medium | `backend/services/research.py`, `backend/services/report.py` | Cache uses completed DB sessions and in-memory metadata. Persist cache metadata and invalidate/refresh by age. | P1 |
| Avoid duplicate work | Partial | Medium | `backend/services/research.py`, `backend/services/deduplication.py` | Same-query cache avoids rerun in-process; no URL-level fetch cache or source-level cache. | P1 |
| Source reliability tracking | Implemented | Low | `backend/services/source_reliability.py`, `backend/api/research.py`, `app.js` | Add source consistency/completeness as dynamic factors, not only static source-type scores. | P2 |
| Source reliability based on type/consistency/completeness/agreement | Partial | Medium | `backend/services/source_reliability.py`, `backend/api/research.py` | Current score is source-type static. Add dynamic modifiers from evidence agreement and completeness. | P1 |
| Structured database-ready output | Partial | Medium | `backend/models/*`, `backend/schemas/*`, `backend/api/research.py` | Models support sessions/business/evidence/conflicts, but many requested fields are evidence-only and not fully normalized. | P1 |

## What Is Truly Implemented?

- FastAPI backend with health, research start, research detail, and SSE endpoints.
- SQLite fallback and PostgreSQL-compatible SQLAlchemy models.
- Query parsing for simple `category in location` and related patterns.
- Search provider abstraction with demo provider, mock provider, and HTML search adapters.
- Basic real-mode collector using `httpx`, BeautifulSoup, trafilatura, and regex utilities.
- Evidence persistence per field/source/url.
- Conflict detection for phone, address, website, and email.
- Deduplication using RapidFuzz plus phone/website matching.
- DNA scoring with evidence strength, weighted source diversity, completeness, freshness, and conflict penalty.
- Rule-based explanation engine.
- Rule-based judge/recommendation engine.
- Final report with challenge-facing metrics.
- Source reliability labels and scores per evidence receipt.
- SSE timeline and replay events.
- Static frontend connected to backend.
- JSON/CSV exports.
- Playwright smoke test coverage.
- Demo-mode curated datasets for five supported queries.

## What Is Simulated?

- Multi-source results for Google Business Profile, Yelp, Yellow Pages, LinkedIn, Facebook, professional directories, government registries, industry associations, healthcare/legal directories, and licensing sources are simulated through `backend/data/demo_businesses.py`.
- Large-scale discovery metrics are simulated in demo mode by `backend/services/report.py`.
- Source diversity strength is demo-realistic, not live-source-derived, unless real adapters are later implemented.
- License, awards, ratings, review counts, specialties, certifications, and social profile values are curated demo evidence rather than real public-source extraction.
- Professional-research behavior is deterministic workflow logic, not AI reasoning.

## What Would Fail During Judging?

1. If judges disable demo mode and expect rich real-world results, source coverage becomes shallow.
2. Real-mode Google/Bing/DuckDuckGo HTML adapters may be blocked or return inconsistent markup.
3. No real Yelp, Yellow Pages, LinkedIn, Facebook, licensing, professional association, healthcare, or legal directory adapters exist.
4. Real collector is sequential and not scalable.
5. Real collector extracts only basic fields reliably.
6. Thousands/tens-of-thousands scale is not implemented, only simulated.
7. Cache metadata is partly in memory and not robust across restarts.
8. Source reliability does not yet account for dynamic consistency/completeness/agreement.
9. Streaming is timeline-first, not true progressive result streaming from live providers.
10. Some requested fields are not first-class database columns.

## Top 10 Missing Capabilities

1. Real multi-source adapters for Yelp, Yellow Pages, LinkedIn, Facebook, license registries, professional associations, and vertical directories.
2. Bounded concurrent collection with retries, backoff, and per-domain limits.
3. Search pagination and fan-out discovery beyond top results.
4. Durable job orchestration for long-running research.
5. Progressive result storage and retrieval while research is still running.
6. URL/source-level fetch cache to avoid duplicate network work.
7. Dynamic source reliability based on source type, agreement, completeness, and conflict history.
8. Full extraction schema/model support for rating, review_count, specialties, license_information, certifications, awards, social_profiles, images_urls, and source_urls.
9. Robust official-website detection and contact-page crawling.
10. Real-scale dedup clustering with merge explanations.

## Top 5 Novelty Features Worth Preserving

1. Business DNA score with explainable components.
2. Evidence receipts and agreement counts per field.
3. Conflict preservation rather than guessing.
4. Rule-based final report with judge recommendations and challenge metrics.
5. Research timeline/replay that makes the workflow feel investigative.

## Recommended Next Implementation Phase

Priority phase: Real-source research hardening.

1. Add bounded concurrent collection and pagination.
2. Add source adapters in this order: official websites, Yellow Pages, Yelp, licensing registry, professional directory.
3. Add first-class extraction fields for all required collect targets.
4. Add URL-level cache and persisted normalized-query cache metadata.
5. Add progressive result endpoint so discovered businesses can appear before the full report is complete.
6. Add dynamic source reliability modifiers for agreement, completeness, and conflicts.

This phase would move ARGUS from demo-grade to judging-resistant real research behavior.
