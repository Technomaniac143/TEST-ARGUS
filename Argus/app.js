const API_BASE_URL = "http://localhost:8000";

const timelineSteps = [
  {
    title: "Searching Google",
    detail: "Scout found 54 candidate URLs from maps, clinics, and directories.",
  },
  {
    title: "Searching Bing",
    detail: "Scout added 39 secondary results and cross-market directory pages.",
  },
  {
    title: "Searching DuckDuckGo",
    detail: "Scout discovered independent profile and review pages.",
  },
  {
    title: "Extracting data",
    detail: "Collector parsed names, phones, addresses, hours, services, and socials.",
  },
  {
    title: "Removing duplicates",
    detail: "RapidFuzz matched names, phones, websites, and street addresses.",
  },
  {
    title: "Verifying evidence",
    detail: "Verifier attached source receipts to every field and assigned confidence.",
  },
  {
    title: "Detecting conflicts",
    detail: "Conflict detector isolated directory mismatches without guessing.",
  },
  {
    title: "Generating analyst report",
    detail: "Analyst and judge converted evidence into recommendations.",
  },
];

const businesses = [
  {
    id: "bham-heart",
    name: "Birmingham Heart Specialists",
    address: "2010 Brookwood Medical Center Dr, Birmingham, AL",
    phone: "205-555-0184",
    website: "https://birminghamheart.example",
    email: "referrals@birminghamheart.example",
    services: "Cardiology, echocardiography, vascular screening",
    dna: 94,
    dnaBreakdown: {
      "Evidence Strength": 96,
      "Source Diversity": 93,
      Completeness: 91,
      Freshness: 95,
      "Conflict Risk": 2,
    },
    confidence: 96,
    risk: "LOW",
    recommendation: "HIGH",
    conflict: false,
    analyst:
      "Birmingham Heart Specialists appears consistently across five independent sources. Phone, address, services, and physician roster agree across the clinic website, Google, LinkedIn, and two directories. No material conflicts were detected.",
    evidence: {
      Phone: {
        value: "205-555-0184",
        sources: ["Website", "Google", "LinkedIn", "Healthgrades"],
      },
      Address: {
        value: "2010 Brookwood Medical Center Dr, Birmingham, AL",
        sources: ["Website", "Google", "Yellow Pages"],
      },
      Website: {
        value: "https://birminghamheart.example",
        sources: ["Google", "LinkedIn", "Directory"],
      },
      Services: {
        value: "Cardiology, echocardiography, vascular screening",
        sources: ["Website", "Google"],
      },
    },
    conflicts: [],
  },
  {
    id: "crestline-cardio",
    name: "Crestline Cardiology Center",
    address: "48 Office Park Dr, Mountain Brook, AL",
    phone: "205-555-0119",
    website: "https://crestlinecardio.example",
    email: "care@crestlinecardio.example",
    services: "Preventive cardiology, stress testing, heart rhythm monitoring",
    dna: 88,
    dnaBreakdown: {
      "Evidence Strength": 90,
      "Source Diversity": 86,
      Completeness: 87,
      Freshness: 89,
      "Conflict Risk": 4,
    },
    confidence: 91,
    risk: "LOW",
    recommendation: "HIGH",
    conflict: false,
    analyst:
      "Crestline Cardiology Center has strong source diversity and clean agreement on core contact data. Fresh activity from the website and Google profile supports a high-confidence recommendation.",
    evidence: {
      Phone: {
        value: "205-555-0119",
        sources: ["Website", "Google", "Yelp"],
      },
      Address: {
        value: "48 Office Park Dr, Mountain Brook, AL",
        sources: ["Website", "Google", "Yellow Pages"],
      },
      Hours: {
        value: "Mon-Fri, 8:00 AM-5:00 PM",
        sources: ["Website", "Google"],
      },
      Socials: {
        value: "LinkedIn profile active within 30 days",
        sources: ["LinkedIn"],
      },
    },
    conflicts: [],
  },
  {
    id: "southern-pulse",
    name: "Southern Pulse Cardiology",
    address: "700 19th St S, Birmingham, AL",
    phone: "205-555-0267",
    website: "https://southernpulse.example",
    email: "info@southernpulse.example",
    services: "Interventional cardiology, imaging, cardiac rehab",
    dna: 76,
    dnaBreakdown: {
      "Evidence Strength": 84,
      "Source Diversity": 81,
      Completeness: 79,
      Freshness: 82,
      "Conflict Risk": 18,
    },
    confidence: 84,
    risk: "MEDIUM",
    recommendation: "REVIEW",
    conflict: true,
    analyst:
      "Southern Pulse Cardiology is a plausible candidate, but one phone mismatch appears in Yelp data. Website, Google, and LinkedIn agree, so the record remains usable with a review flag.",
    evidence: {
      Phone: {
        value: "205-555-0267",
        sources: ["Website", "Google", "LinkedIn"],
      },
      Address: {
        value: "700 19th St S, Birmingham, AL",
        sources: ["Website", "Google"],
      },
      Rating: {
        value: "4.6 average across public profiles",
        sources: ["Google", "Healthgrades", "Yelp"],
      },
      Services: {
        value: "Interventional cardiology, imaging, cardiac rehab",
        sources: ["Website"],
      },
    },
    conflicts: [
      {
        field: "Phone",
        value1: "205-555-0267",
        value2: "205-555-0299",
        source1: "Website",
        source2: "Yelp",
      },
    ],
  },
];

const elements = {
  form: document.querySelector("#searchForm"),
  query: document.querySelector("#queryInput"),
  parsedCategory: document.querySelector("#parsedCategory"),
  parsedLocation: document.querySelector("#parsedLocation"),
  modeIndicator: document.querySelector("#modeIndicator"),
  timeline: document.querySelector("#timelineList"),
  runState: document.querySelector("#runState"),
  metricBusinesses: document.querySelector("#metricBusinesses"),
  metricVerified: document.querySelector("#metricVerified"),
  metricDuplicates: document.querySelector("#metricDuplicates"),
  metricSources: document.querySelector("#metricSources"),
  metricDuration: document.querySelector("#metricDuration"),
  businessGrid: document.querySelector("#businessGrid"),
  evidenceTitle: document.querySelector("#evidenceTitle"),
  evidenceConfidence: document.querySelector("#evidenceConfidence"),
  evidenceFields: document.querySelector("#evidenceFields"),
  analystName: document.querySelector("#analystName"),
  analystSummary: document.querySelector("#analystSummary"),
  dnaBreakdown: document.querySelector("#dnaBreakdown"),
  evidenceGraph: document.querySelector("#evidenceGraph"),
  judgeRecommendation: document.querySelector("#judgeRecommendation"),
  judgeRisk: document.querySelector("#judgeRisk"),
  reportExecutive: document.querySelector("#reportExecutive"),
  reportTop: document.querySelector("#reportTop"),
  reportQuality: document.querySelector("#reportQuality"),
  reportConflicts: document.querySelector("#reportConflicts"),
  reportWeak: document.querySelector("#reportWeak"),
  reportChallengeMetrics: document.querySelector("#reportChallengeMetrics"),
  reportScaleMetrics: document.querySelector("#reportScaleMetrics"),
  reportCoverage: document.querySelector("#reportCoverage"),
  downloadJson: document.querySelector("#downloadJson"),
  downloadCsv: document.querySelector("#downloadCsv"),
};

let activeBusinesses = businesses;
let selectedBusinessId = activeBusinesses[0].id;
let activeFilter = "all";
let runTimer = null;
let eventSource = null;
let activeSession = null;

function parseQuery(value) {
  const normalized = value.trim().toLowerCase();
  const parts = normalized.split(/\s+in\s+/);
  return {
    category: parts[0] || "businesses",
    location: parts[1] || "target market",
  };
}

function renderTimeline(activeIndex = -1) {
  elements.timeline.innerHTML = timelineSteps
    .map((step, index) => {
      const state =
        index < activeIndex ? "done" : index === activeIndex ? "running" : "";
      const marker = index < activeIndex ? "✓" : index === activeIndex ? "…" : "";
      return `
        <div class="timeline-item ${state}">
          <div class="timeline-dot" aria-hidden="true">${marker}</div>
          <div class="timeline-copy">
            <strong>${step.title}</strong>
            <span>${step.detail}</span>
          </div>
          <span class="source-pill">${state === "done" ? "complete" : state || "queued"}</span>
        </div>
      `;
    })
    .join("");
}

function renderTimelineEvents(events) {
  if (!events.length) {
    renderTimeline();
    return;
  }

  elements.timeline.innerHTML = events
    .map((item, index) => {
      const isLast = index === events.length - 1;
      const state = item.status === "complete" || !isLast ? "done" : "running";
      const marker = state === "done" ? "✓" : "…";
      return `
        <div class="timeline-item ${state}">
          <div class="timeline-dot" aria-hidden="true">${marker}</div>
          <div class="timeline-copy">
            <strong>${item.message}</strong>
            <span>${Number(item.elapsed_seconds || 0).toFixed(1)}s — ${item.event.replaceAll("_", " ")}</span>
          </div>
          <span class="source-pill">${item.status}</span>
        </div>
      `;
    })
    .join("");
}

function renderMetrics(session = null) {
  if (!session) {
    elements.metricBusinesses.textContent = "127";
    elements.metricVerified.textContent = "104";
    elements.metricDuplicates.textContent = "23";
    elements.metricSources.textContent = "18";
    elements.metricDuration.textContent = "14s";
    return;
  }

  const verified = session.businesses.filter((business) => business.confidence >= 70).length;
  elements.metricBusinesses.textContent = session.businesses_found || session.job?.discovered_businesses || session.businesses.length;
  elements.metricVerified.textContent = session.job?.verified_businesses ?? verified;
  elements.metricDuplicates.textContent = session.duplicates_removed ?? 0;
  elements.metricSources.textContent = session.sources_searched ?? 0;
  elements.metricDuration.textContent = `${session.duration ?? 0}s`;
}

function renderBusinesses() {
  if (!activeBusinesses.length) {
    const report = activeSession?.report || {};
    const suggestions = (report.suggested_queries || [])
      .map((query) => `<li>${escapeHtml(query)}</li>`)
      .join("");
    elements.businessGrid.innerHTML = `
      <div class="field-card">
        <div class="field-head">
          <strong>No offline corpus match</strong>
          <span class="source-pill">${escapeHtml(report.support_level || "UNSUPPORTED_OFFLINE_QUERY")}</span>
        </div>
        <p>${escapeHtml(report.unsupported_message || "No businesses were returned for this query.")}</p>
        <p>Parsed category: ${escapeHtml(activeSession?.category || "")}. Parsed location: ${escapeHtml(activeSession?.location || "")}.</p>
        <strong>Suggested supported queries</strong>
        <ul>${suggestions}</ul>
      </div>
    `;
    return;
  }

  const filtered = activeBusinesses.filter((business) => {
    if (activeFilter === "low") return business.risk === "LOW";
    if (activeFilter === "conflict") return business.conflict;
    return true;
  });

  elements.businessGrid.innerHTML = filtered
    .map((business) => {
      const riskClass =
        business.risk === "LOW" ? "good" : business.risk === "MEDIUM" ? "warn" : "danger";
      const selected = business.id === selectedBusinessId ? "selected" : "";

      return `
        <article class="business-card ${selected}" data-business-id="${business.id}" tabindex="0">
          <div>
            <h4>${business.rank ? `#${business.rank} ` : ""}${business.name}</h4>
            <p class="card-meta">${business.address}<br />${business.phone}</p>
          </div>
          <div class="badge-row">
            <span class="badge good">${business.recommendationLabel || business.recommendation}</span>
            <span class="badge good">${business.confidence}% confidence</span>
            <span class="badge ${riskClass}">${business.risk} risk</span>
            <span class="badge ${riskClass}">${business.reliability || business.risk} reliability</span>
            <span class="badge ${business.conflict ? "warn" : "good"}">
              ${business.conflict ? "conflict found" : "verified"}
            </span>
            ${business.qualityFlags.slice(0, 3).map((flag) => `<span class="badge warn">${escapeHtml(flag)}</span>`).join("")}
            <span class="badge good">${escapeHtml(business.marketPosition)}</span>
            <span class="badge warn">${escapeHtml(business.marketCluster)}</span>
          </div>
          <div class="dna-meter">
            <strong>DNA score ${business.dna}/100</strong>
            <div class="meter-track" aria-hidden="true">
              <div class="meter-fill" style="width: ${business.dna}%"></div>
            </div>
          </div>
        </article>
      `;
    })
    .join("");
}

function renderEvidence() {
  const business = activeBusinesses.find((item) => item.id === selectedBusinessId) || activeBusinesses[0];
  if (!business) {
    const report = activeSession?.report || {};
    elements.evidenceTitle.textContent = "Offline corpus coverage";
    elements.evidenceConfidence.textContent = "0%";
    elements.analystName.textContent = "Unsupported query handling";
    elements.analystSummary.innerHTML = `
      <p>${escapeHtml(report.unsupported_message || "Run a supported query to inspect evidence receipts.")}</p>
      <p>Live mode can search public sources when internet access is available.</p>
    `;
    elements.judgeRecommendation.textContent = report.support_level || "UNSUPPORTED_OFFLINE_QUERY";
    elements.judgeRisk.textContent = "REVIEW";
    elements.dnaBreakdown.innerHTML = "";
    elements.evidenceGraph.innerHTML = "";
    elements.evidenceFields.innerHTML = "";
    return;
  }
  elements.evidenceTitle.textContent = business.name;
  elements.evidenceConfidence.textContent = `${business.confidence}%`;
  elements.analystName.textContent = `${business.name} explanation`;
  elements.analystSummary.innerHTML = renderExplanation(business);
  elements.judgeRecommendation.textContent = business.recommendation || business.reliability;
  elements.judgeRisk.textContent = business.risk;
  elements.dnaBreakdown.innerHTML = Object.entries(business.dnaBreakdown)
    .map(([label, score]) => {
      const suffix = label === "Conflict Risk" ? "" : "/100";
      return `
        <div class="dna-row">
          <span>${label}</span>
          <strong>${score}${suffix}</strong>
        </div>
      `;
    })
    .join("");

  elements.evidenceGraph.innerHTML = renderEvidenceGraphTree(business);

  const evidenceCards = Object.entries(business.evidence)
    .map(([field, item]) => {
      const sourceList = item.sources
        .map((source) => {
          const reliability = item.sourceReliability?.[source];
          const suffix = reliability ? ` · ${reliability.method} · ${reliability.status} · Reliability ${reliability.score}` : "";
          return `<span class="source-pill">✓ ${source}${suffix}</span>`;
        })
        .join("");
      const agreement = item.agreement ? `<span class="source-pill">agreement ${item.agreement}</span>` : "";

      const conflicts = business.conflicts
        .filter((conflict) => conflict.field === field)
        .map(
          (conflict) => `
            <div class="conflict-card">
              Conflict: ${conflict.source1} reports ${conflict.value1}; ${conflict.source2} reports ${conflict.value2}.
            </div>
          `,
        )
        .join("");

      return `
        <article class="field-card">
          <div class="field-head">
            <strong>${field}</strong>
            <span class="field-value">${item.value}</span>
          </div>
          <div class="source-list">${sourceList}${agreement}</div>
          ${conflicts}
        </article>
      `;
    })
    .join("");

  elements.evidenceFields.innerHTML = evidenceCards;
}

function renderReport(session = null) {
  if (!session?.report) {
    elements.reportExecutive.textContent = "Run a search to generate a final research report.";
    elements.reportTop.innerHTML = "";
    elements.reportQuality.textContent = "Awaiting research session.";
    elements.reportConflicts.textContent = "0";
    elements.reportWeak.textContent = "0";
    elements.reportChallengeMetrics.innerHTML = "";
    elements.reportScaleMetrics.innerHTML = "";
    elements.reportCoverage.innerHTML = "";
    elements.modeIndicator.textContent = "mode: static preview";
    return;
  }

  const report = session.report;
  const executiveReport = report.executive_report || {};
  elements.reportExecutive.textContent = [
    executiveReport.executive_summary || report.executive_summary,
    ...(executiveReport.key_findings || []).slice(0, 3),
  ].join(" ");
  elements.reportTop.innerHTML = report.top_recommendations
    .concat(report.top_recommendations.length ? [] : report.suggested_queries || [])
    .map((name) => `<li>${escapeHtml(name)}</li>`)
    .join("");
  elements.reportQuality.textContent = report.offline_mode
    ? `${executiveReport.data_quality_summary || report.data_quality_summary} Offline Competition Mode uses a packaged public-source corpus so ARGUS can demonstrate discovery, extraction, verification, deduplication, conflict detection, and reporting without internet access.`
    : executiveReport.data_quality_summary || report.data_quality_summary;
  elements.reportConflicts.textContent = report.conflicts_found;
  elements.reportWeak.textContent = report.weak_records_count;
  elements.reportChallengeMetrics.innerHTML = [
    ["Businesses verified", report.businesses_verified],
    ["Sources searched", report.sources_searched],
    ["Research duration", `${report.research_duration}s`],
    ["Website coverage", `${report.records_with_website_percentage}%`],
    ["Phone coverage", `${report.records_with_phone_percentage}%`],
    ["Working hours coverage", `${report.records_with_working_hours_percentage}%`],
    ["License coverage", `${report.records_with_license_percentage}%`],
    ["Avg source reliability", `${report.source_reliability_average}/100`],
    ["Active Mode", report.active_mode || (report.offline_mode ? "Offline Competition" : "Online Research")],
    ["Fallback used", report.fallback_used ? "yes" : "no"],
    ["Fallback reason", report.fallback_reason || "none"],
    ["Online results", report.online_results_count ?? 0],
    ["Filtered URLs", report.filtered_urls_count ?? 0],
    ["Adapter Health", `${report.source_health?.adapter_health_average ?? 0}/100`],
    ["Multi-source adapters", Object.keys(report.adapter_health || report.source_health?.adapter_health || {}).length],
    ["Job status", report.job?.status || "unknown"],
    ["Current Stage", report.job?.current_stage || "planning"],
    ["Progress", `${report.job?.stage_progress ?? 0}%`],
    ["URLs processed", `${report.job?.processed_urls ?? 0}/${report.job?.total_urls ?? 0}`],
    ["Businesses verified", report.job?.verified_businesses ?? report.businesses_verified],
    ["Deep enrichment status", report.job?.enrichment_status || "pending"],
    ["Failed URLs", report.job?.failed_urls ?? 0],
    ["Executive Report", "visible"],
    ["Offline mode", report.offline_mode ? "yes" : "no"],
    ["Query support", report.support_level || "LIVE_MODE"],
    ["Cache hit", report.cache_hit ? "yes" : "no"],
    ["Cache age", report.cache_age_seconds == null ? "fresh" : `${report.cache_age_seconds}s`],
    ["Export ready", report.export_ready ? "yes" : "no"],
  ]
    .map(([label, value]) => `<div class="report-stat"><span>${label}</span><strong>${value}</strong></div>`)
    .join("");
  elements.modeIndicator.textContent = `Active Mode: ${report.active_mode || (report.offline_mode ? "Offline Competition" : "Online Research")}`;
  elements.reportScaleMetrics.innerHTML = [
    ["Raw records discovered", report.discovered_records_raw],
    ["Processed records", report.processed_records],
    ["Duplicates removed", report.duplicates_removed],
    ["Final businesses", report.final_unique_businesses],
  ]
    .map(([label, value]) => `<div class="report-stat"><span>${label}</span><strong>${value}</strong></div>`)
    .join("");
  const corpus = report.offline_corpus_coverage || {};
  const corpusRows = report.offline_mode
    ? [
        ["Offline Corpus Coverage", corpus.message || report.support_level],
        ["Supported queries", (corpus.supported_queries || []).join("; ")],
        ["Supported offline regions", (corpus.supported_regions || []).join("; ")],
        ["Tamil Nadu cities", (corpus.tamil_nadu_supported_cities || []).join("; ")],
        ["Tamil Nadu categories", (corpus.tamil_nadu_supported_categories || []).join("; ")],
        ["Tamil Nadu supported pairs", corpus.tamil_nadu_supported_query_count || 0],
        ["Available source classes", (corpus.available_source_classes || []).join("; ")],
        ["Records in local corpus", corpus.records_in_local_corpus || 0],
        ["Current query support level", report.support_level],
        ["Live-mode source plan", (report.live_source_plan || []).slice(0, 4).join("; ")],
      ]
    : [];
  elements.reportCoverage.innerHTML = [
    ["Executive Research Report", executiveReport.risk_summary || "Risk summary pending"],
    ...Object.entries(report.challenge_requirement_coverage || {}).map(([label, value]) => [
      `Challenge: ${label}`,
      value,
    ]),
    ...Object.entries(report.requirement_coverage || {}),
    ["Key Findings", (executiveReport.key_findings || []).slice(0, 2).join(" ") || "No key findings yet"],
    ["Recommended Next Actions", (executiveReport.recommended_next_actions || []).slice(0, 2).join("; ") || "No actions yet"],
    ["Major Contradictions", (executiveReport.major_contradictions || []).slice(0, 3).join("; ") || "No contradictions"],
    ["Market Structure Summary", executiveReport.market_structure_summary || "Market structure pending"],
    ["Competitive Insight Summary", executiveReport.competitive_insight_summary || "Competitive insight pending"],
    ["Demo Command Center", (report.demo_command_center || []).slice(0, 5).join("; ")],
    ["Executive Intelligence", executiveIntelligenceSummary(report)],
    ["SWOT Analysis", swotSummary(report.swot || {})],
    ["Market Narrative", narrativeSummary(report.market_narratives || {})],
    ["Executive Scorecard", scorecardSummary(report.scorecard || {})],
    ["Recommendations", recommendationsSummary(report.recommendations || {})],
    ["Best Overall Business", report.benchmarks?.best_overall_business || "No benchmark"],
    ["Highest Trust Business", report.benchmarks?.highest_trust_business || "No benchmark"],
    ["Highest Risk Business", report.benchmarks?.highest_risk_business || "No benchmark"],
    ...Object.entries(report.source_health || {}).map(([label, value]) => [
      `Source Health: ${label.replaceAll("_", " ")}`,
      Array.isArray(value)
        ? value.slice(0, 4).join("; ") || "none"
        : typeof value === "object" && value
          ? Object.entries(value).slice(0, 4).map(([name, health]) => `${name}: ${health.health_score ?? "n/a"}`).join("; ")
          : value,
    ]),
    ["Adapter Health", adapterHealthSummary(report.adapter_health || report.source_health?.adapter_health || {})],
    ["Session History", (report.recent_jobs || []).slice(0, 3).map((job) => `${job.query || "research"}: ${job.status}`).join("; ") || "No recent jobs"],
    ["Contradiction Map", `${(report.contradiction_map || []).length} contradiction(s)`],
    ["Human Review Queue", `${(report.review_queue || []).length} item(s)`],
    ["Market Overview", marketOverviewText(report.market_overview || {})],
    ["Knowledge Graph Summary", `${report.knowledge_graph?.nodes?.length || 0} nodes, ${report.knowledge_graph?.edges?.length || 0} edges`],
    ["Market Cluster", (report.clusters || []).map((item) => `${item.cluster_name}: ${item.cluster_metrics?.count || 0}`).join("; ")],
    ["Market Position", (report.market_positions || []).slice(0, 3).map((item) => `${item.business_name}: ${item.market_position}`).join("; ")],
    ["Business Similarity", activeBusinesses[0]?.similarBusinesses?.[0] ? `${activeBusinesses[0].name} ~ ${activeBusinesses[0].similarBusinesses[0].business_name}: ${activeBusinesses[0].similarBusinesses[0].score}` : "No similarity pairs"],
    ["Relationship Graph Summary", `${report.relationship_graph?.nodes?.length || 0} nodes, ${report.relationship_graph?.edges?.length || 0} edges`],
    ["Market Ecosystem", ecosystemSummary(report.ecosystem_summary || {})],
    ["Most Connected Business", report.ecosystem_summary?.most_connected_business || "No connected business"],
    ["Most Similar Pair", similarPairSummary(report.ecosystem_summary?.most_similar_pair || report.similar_pairs?.[0])],
    ["Most Unique Business", report.ecosystem_summary?.most_unique_business || "No unique business"],
    ["Recovery events", (session.timeline_events || []).filter((item) => String(item.event || "").startsWith("job_recover")).length],
    ["Outliers", Object.values(report.outliers || {}).flat().length],
    ["Competitive Intelligence", competitiveSummary(report.market_comparison || {})],
    ["Strengths", activeBusinesses.flatMap((item) => item.competitiveIntelligence?.strengths || []).slice(0, 4).join("; ") || "No strengths detected"],
    ["Weaknesses", activeBusinesses.flatMap((item) => item.competitiveIntelligence?.weaknesses || []).slice(0, 4).join("; ") || "No weaknesses detected"],
    ["Key risks", activeBusinesses.flatMap((item) => item.competitiveIntelligence?.risk_factors || []).slice(0, 4).join("; ") || "No major risks"],
    ["Biggest opportunity gaps", activeBusinesses.flatMap((item) => item.competitiveIntelligence?.opportunity_gaps || []).slice(0, 4).join("; ") || "No major gaps"],
    ["Top differentiated businesses", activeBusinesses.slice(0, 3).map((item) => item.name).join("; ")],
    ...((report.contradiction_map || []).slice(0, 3).map((item) => [
      `Contradiction: ${item.business_name}`,
      `${item.severity} ${fieldLabel(item.field)} - ${(item.values || []).join(" vs ")}`,
    ])),
    ...((report.review_queue || []).slice(0, 3).map((item) => [
      `Review: ${item.business_name}`,
      `${item.severity} - ${item.reason}`,
    ])),
    ...corpusRows,
  ]
    .map(([label, value]) => `<div class="report-stat"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`)
    .join("");
}

function adapterHealthSummary(adapterHealth) {
  const rows = Object.entries(adapterHealth || {}).slice(0, 5);
  if (!rows.length) return "No adapter activity in this mode";
  return rows.map(([name, health]) => `${name} ${health.health_score ?? "n/a"}`).join("; ");
}

function ecosystemSummary(ecosystem) {
  const clusters = (ecosystem.clusters || []).slice(0, 3).map((item) => `${item.name}: ${item.count}`).join("; ");
  const services = (ecosystem.shared_services || []).slice(0, 3).join(", ");
  return [clusters, services ? `services: ${services}` : ""].filter(Boolean).join(" | ") || "No ecosystem summary";
}

function similarPairSummary(pair) {
  if (!pair) return "No similar pair";
  return `${pair.business_a || ""} ~ ${pair.business_b || ""} (${pair.score || 0})`;
}

function executiveIntelligenceSummary(report) {
  const score = report.scorecard?.overall_intelligence_score ?? 0;
  const best = report.benchmarks?.best_overall_business || "No best overall business";
  return `${best} leads with overall intelligence ${score}/100`;
}

function swotSummary(swot) {
  const first = Object.entries(swot || {})[0];
  if (!first) return "No SWOT available";
  const [name, value] = first;
  return `${name}: ${(value.strengths || []).slice(0, 1).join(", ")} / ${(value.threats || []).slice(0, 1).join(", ")}`;
}

function narrativeSummary(narratives) {
  return narratives.market_structure || narratives.competitive_landscape || "No narrative available";
}

function scorecardSummary(scorecard) {
  return `Trust ${scorecard.trust_score ?? 0}, Coverage ${scorecard.coverage_score ?? 0}, Overall ${scorecard.overall_intelligence_score ?? 0}`;
}

function recommendationsSummary(recommendations) {
  const safe = (recommendations.businesses_safe_for_outreach || []).slice(0, 2).join(", ");
  const review = (recommendations.businesses_requiring_manual_review || []).length;
  return `${safe || "No safe outreach list yet"}; ${review} manual review`;
}

function renderEvidenceGraphTree(business) {
  const fieldRows = Object.entries(business.evidence)
    .map(([field, item]) => {
      const sources = item.sources.map((source) => `<li>Source: ${escapeHtml(source)}</li>`).join("");
      const conflicts = business.conflicts
        .filter((conflict) => conflict.field === field)
        .map(
          (conflict) => `
            <li class="conflict-card">
              ${escapeHtml(field)} conflict: ${escapeHtml(conflict.source1)} reports ${escapeHtml(conflict.value1)}; ${escapeHtml(conflict.source2)} reports ${escapeHtml(conflict.value2)}.
            </li>
          `,
        )
        .join("");
      return `
        <li>
          <strong>${escapeHtml(field)}</strong>
          <ul>
            <li>Value: ${escapeHtml(item.value)}</li>
            ${sources}
            ${conflicts}
          </ul>
        </li>
      `;
    })
    .join("");
  return `
    <div class="graph-node source">Evidence Graph</div>
    <div class="graph-node field">Business Similarity: ${(business.similarBusinesses || []).map((item) => `${escapeHtml(item.business_name)} ${item.score}`).join(" | ") || "No peers"}</div>
    <div class="graph-node field">Market Cluster: ${escapeHtml(business.marketCluster)} | Market Position: ${escapeHtml(business.marketPosition)}</div>
    <div class="graph-node field">Outliers: ${(business.outliers || []).map((item) => escapeHtml(item.outlier_reason)).join(", ") || "None detected"}</div>
    <ul class="evidence-tree">
      <li>
        <strong>${escapeHtml(business.name)}</strong>
        <ul>${fieldRows}</ul>
      </li>
    </ul>
  `;
}

function marketOverviewText(overview) {
  if (!overview.total_businesses) return "No market overview available";
  return `${overview.total_businesses} businesses | avg DNA ${overview.average_dna} | top cluster ${overview.top_cluster}`;
}

function competitiveSummary(comparison) {
  if (!comparison.strongest_business) return "No competitive comparison available";
  return `Strongest: ${comparison.strongest_business} | Weakest: ${comparison.weakest_business} | Best coverage: ${comparison.best_source_coverage}`;
}

function updateQueryMeta() {
  const parsed = parseQuery(elements.query.value);
  elements.parsedCategory.textContent = `category: ${parsed.category}`;
  elements.parsedLocation.textContent = `location: ${parsed.location}`;
}

function runResearch() {
  clearInterval(runTimer);
  let index = 0;
  elements.runState.textContent = "Running";
  renderTimeline(index);

  runTimer = setInterval(() => {
    index += 1;
    renderTimeline(index);

    if (index > timelineSteps.length) {
      clearInterval(runTimer);
      elements.runState.textContent = "Complete";
      document.querySelector("#dashboard").scrollIntoView({ behavior: "smooth" });
    }
  }, 620);
}

function fieldLabel(field) {
  return field
    .replaceAll("_", " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function renderExplanation(business) {
  const explanation = business.explanation || {};
  const reasons = explanation.reasons || [];
  const warnings = explanation.warnings || [];
  const reasonList = reasons.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
  const warningList = warnings.map((item) => `<li>${escapeHtml(item)}</li>`).join("");

  return `
    <p>${escapeHtml(explanation.summary || business.analyst)}</p>
    <p>${escapeHtml(business.recommendationReason || "")}</p>
    <strong>Strengths</strong>
    <ul>${reasonList || "<li>No strengths available.</li>"}</ul>
    <strong>Warnings</strong>
    <ul>${warningList || "<li>No warnings detected.</li>"}</ul>
  `;
}

function mapBackendBusiness(business) {
  const evidence = {};
  business.evidence.forEach((item) => {
    const label = fieldLabel(item.field);
    if (!evidence[label]) {
      evidence[label] = { value: item.value, sources: [], agreement: item.agreement, sourceReliability: {} };
    }
    if (!evidence[label].sources.includes(item.source)) {
      evidence[label].sources.push(item.source);
    }
    evidence[label].agreement = item.agreement || evidence[label].agreement;
    evidence[label].sourceReliability[item.source] = {
      type: item.source_type,
      score: item.reliability_score,
      label: item.reliability_label,
      method: item.extraction_method,
      status: item.crawl_status,
    };
  });

  const breakdown = business.dna_breakdown || {};
  return {
    id: String(business.id),
    rank: business.rank,
    name: business.name || "Unknown business",
    address: business.address || "Address not found",
    phone: business.phone || "Phone not found",
    website: business.website,
    email: business.email,
    services: evidence.Services?.value || "",
    dna: Math.round(business.dna_score || 0),
    dnaBreakdown: {
      "Evidence Strength": breakdown.evidence_strength ?? 0,
      "Source Diversity": breakdown.source_diversity ?? 0,
      Completeness: breakdown.completeness ?? 0,
      Freshness: breakdown.freshness ?? 0,
      "Conflict Penalty": breakdown.conflict_penalty ?? 0,
      "Final Score": breakdown.final_score ?? Math.round(business.dna_score || 0),
    },
    confidence: Math.round(business.confidence || 0),
    risk: business.risk || "UNKNOWN",
    reliability: business.reliability || "LOW",
    recommendation: business.recommendation || "REVIEW_REQUIRED",
    recommendationLabel: recommendationLabel(business),
    recommendationReason: business.recommendation_reason,
    confidenceLabel: business.confidence_label,
    riskLevel: business.risk_level,
    conflict: business.conflicts.length > 0,
    qualityFlags: business.analyst_quality_flags || [],
    similarBusinesses: business.similar_businesses || [],
    marketCluster: business.market_cluster || "Unassigned",
    marketPosition: business.market_position || "AVERAGE",
    percentileScore: business.percentile_score || 0,
    centralityScore: business.centrality_score || 0,
    topRelationship: business.top_relationship || "",
    sharedServicesCount: business.shared_services_count || 0,
    outliers: business.outliers || [],
    competitiveIntelligence: business.competitive_intelligence || {},
    analystOutput: business.analyst_output || {},
    swot: business.swot || {},
    overallIntelligenceScore: business.overall_intelligence_score || 0,
    executiveRecommendation: business.executive_recommendation || "",
    analyst: business.explanation?.summary || "Backend research completed.",
    explanation: business.explanation,
    evidenceGraph: business.evidence_graph,
    evidence,
    conflicts: business.conflicts.map((conflict) => ({
      field: fieldLabel(conflict.field),
      value1: conflict.value1,
      value2: conflict.value2,
      source1: conflict.source1,
      source2: conflict.source2,
    })),
  };
}

function recommendationLabel(business) {
  const label = String(business.recommendation || "REVIEW_REQUIRED").replaceAll("_", " ");
  if (business.rank && business.recommendation !== "REVIEW_REQUIRED") {
    return `#${business.rank} ${label}`;
  }
  return label;
}

function applySession(session) {
  activeSession = session;
  activeBusinesses = session.businesses.map(mapBackendBusiness);
  if (!activeBusinesses.length && session.job?.partial_businesses?.length) {
    activeBusinesses = session.job.partial_businesses.map((name, index) => ({
      id: `partial-${index}`,
      name,
      category: session.category,
      location: session.location,
      phone: null,
      address: null,
      website: null,
      email: null,
      confidence: 0,
      dna_score: 0,
      dna_breakdown: {},
      risk: "PENDING",
      reliability: "PENDING",
      recommendation: "REVIEW_REQUIRED",
      recommendation_reason: "Research is still running.",
      evidence: [],
      conflicts: [],
      explanation: { summary: "Partial business candidate discovered. Verification is in progress.", reasons: [], warnings: [] },
      analystQualityFlags: ["IN_PROGRESS"],
      competitiveIntelligence: {},
      similarBusinesses: [],
      outliers: [],
    }));
  }
  selectedBusinessId = activeBusinesses[0]?.id || null;
  if (session.timeline_events?.length) {
    renderTimelineEvents(session.timeline_events);
  }
  renderMetrics(session);
  renderReport(session);
  renderBusinesses();
  renderEvidence();
  updateQueryMeta();
}

function connectTimeline(sessionId) {
  if (eventSource) eventSource.close();
  const events = [];
  eventSource = new EventSource(`${API_BASE_URL}/api/research/${sessionId}/events`);

  const handleEvent = (event) => {
    const item = JSON.parse(event.data);
    events.push(item);
    elements.runState.textContent = item.status === "queued" ? "Queued" : item.status === "complete" ? "Complete" : item.status === "failed" ? "Failed" : "Running";
    renderTimelineEvents(events);
    if (item.status === "complete" || item.status === "failed") {
      eventSource.close();
    }
  };

  [
    "job_queued",
    "job_started",
    "stage_changed",
    "research_started",
    "query_parsed",
    "source_plan_created",
    "source_search_started",
    "source_search_completed",
    "source_search_failed",
    "url_discovered",
    "url_processed",
    "business_candidate_found",
    "active_mode",
    "online_results_count",
    "fallback_used",
    "urls_filtered",
    "collection_started",
    "collection_failed",
    "url_failed",
    "business_extracted",
    "crawl_cache_hit",
    "crawl_cache_miss",
    "crawl_failed",
    "crawl_succeeded",
    "source_skipped",
    "searching_google_profiles",
    "searching_official_websites",
    "checking_professional_directories",
    "checking_license_registries",
    "searching_duckduckgo",
    "searching_bing",
    "search_results_found",
    "collecting_business_data",
    "business_discovered",
    "evidence_found",
    "deduplicating_records",
    "comparing_directory_records",
    "duplicate_detected",
    "verifying_evidence",
    "detecting_conflicts",
    "conflict_detected",
    "conflict_found",
    "computing_business_dna",
    "dna_computed",
    "business_verified",
    "business_enriched",
    "generating_argus_explanation",
    "report_ready",
    "job_completed",
    "job_failed",
    "research_complete",
    "research_failed",
  ].forEach((eventName) => eventSource.addEventListener(eventName, handleEvent));

  eventSource.onerror = () => {
    eventSource.close();
  };
}

async function runBackendResearch() {
  clearInterval(runTimer);
  elements.runState.textContent = "Queued";
  renderTimelineEvents([{ event: "job_queued", message: "Research job queued", status: "queued" }]);

  const response = await fetch(`${API_BASE_URL}/api/research/start`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query: elements.query.value }),
  });
  if (!response.ok) throw new Error("Research request failed");

  const started = await response.json();
  connectTimeline(started.session_id);
  const session = await waitForResearchCompletion(started.session_id);
  elements.runState.textContent = session.report_ready ? "Complete" : session.status;
  document.querySelector("#dashboard").scrollIntoView({ behavior: "smooth" });
}

async function waitForResearchCompletion(sessionId) {
  let lastSession = null;
  for (let attempt = 0; attempt < 180; attempt += 1) {
    const detailResponse = await fetch(`${API_BASE_URL}/api/research/${sessionId}`);
    if (!detailResponse.ok) throw new Error("Research detail request failed");
    lastSession = await detailResponse.json();
    applySession(lastSession);
    const status = lastSession.job?.status || lastSession.status;
    elements.runState.textContent = status === "complete" ? "Complete" : status === "queued" ? "Queued" : status === "failed" ? "Failed" : "Running";
    if (lastSession.report_ready || status === "failed" || status === "cancelled") {
      return lastSession;
    }
    await new Promise((resolve) => setTimeout(resolve, 500));
  }
  return lastSession;
}

elements.form.addEventListener("submit", async (event) => {
  event.preventDefault();
  updateQueryMeta();
  try {
    await runBackendResearch();
  } catch (error) {
    activeSession = null;
    activeBusinesses = businesses;
    selectedBusinessId = activeBusinesses[0].id;
    renderMetrics();
    renderReport();
    renderBusinesses();
    renderEvidence();
    runResearch();
  }
});

elements.downloadJson.addEventListener("click", () => {
  if (!activeSession) return;
  downloadFile(
    "argus-research-report.json",
    "application/json",
    JSON.stringify(activeSession, null, 2),
  );
});

elements.downloadCsv.addEventListener("click", () => {
  if (!activeSession) return;
  const rows = [
    ["business_name", "address", "phone", "website", "email", "dna_score", "reliability", "recommendation", "conflict_count", "evidence_count", "top_sources", "quality_flags", "review_required", "top_conflict", "market_position", "cluster", "top_similar_business", "similarity_score", "centrality_score", "top_relationship", "shared_services_count", "overall_intelligence_score", "swot_summary", "executive_recommendation", "strengths", "weaknesses", "opportunity_gaps", "risk_factors", "differentiation_summary"],
    ...activeSession.businesses.map((business) => [
      business.name,
      business.address,
      business.phone,
      business.website,
      business.email,
      business.dna_score,
      business.reliability,
      business.recommendation,
      business.conflicts.length,
      business.evidence.length,
      [...new Set(business.evidence.map((item) => item.source))].slice(0, 5).join("; "),
      (business.analyst_quality_flags || []).join("; "),
      (business.analyst_quality_flags || []).includes("NEEDS_HUMAN_REVIEW") ? "yes" : "no",
      business.conflicts[0] ? `${business.conflicts[0].field}: ${business.conflicts[0].value1} vs ${business.conflicts[0].value2}` : "",
      business.market_position,
      business.market_cluster,
      business.similar_businesses?.[0]?.business_name || "",
      business.similar_businesses?.[0]?.score || "",
      business.centrality_score || 0,
      business.top_relationship || "",
      business.shared_services_count || 0,
      business.overall_intelligence_score || 0,
      business.swot ? `S:${(business.swot.strengths || []).join("; ")} W:${(business.swot.weaknesses || []).join("; ")}` : "",
      business.executive_recommendation || "",
      (business.competitive_intelligence?.strengths || []).join("; "),
      (business.competitive_intelligence?.weaknesses || []).join("; "),
      (business.competitive_intelligence?.opportunity_gaps || []).join("; "),
      (business.competitive_intelligence?.risk_factors || []).join("; "),
      business.competitive_intelligence?.differentiation_summary || "",
    ]),
  ];
  const csv = rows.map((row) => row.map(csvCell).join(",")).join("\n");
  downloadFile("argus-research-report.csv", "text/csv", csv);
});

function csvCell(value) {
  return `"${String(value ?? "").replaceAll('"', '""')}"`;
}

function downloadFile(filename, type, content) {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

elements.query.addEventListener("input", updateQueryMeta);

document.addEventListener("click", (event) => {
  const card = event.target.closest("[data-business-id]");
  if (card) {
    selectedBusinessId = card.dataset.businessId;
    renderBusinesses();
    renderEvidence();
    document.querySelector("#evidence").scrollIntoView({ behavior: "smooth" });
  }

  const segment = event.target.closest("[data-filter]");
  if (segment) {
    activeFilter = segment.dataset.filter;
    document
      .querySelectorAll("[data-filter]")
      .forEach((item) => item.classList.toggle("active", item === segment));
    renderBusinesses();
  }
});

document.addEventListener("keydown", (event) => {
  const card = event.target.closest("[data-business-id]");
  if (card && (event.key === "Enter" || event.key === " ")) {
    event.preventDefault();
    selectedBusinessId = card.dataset.businessId;
    renderBusinesses();
    renderEvidence();
  }
});

const observer = new IntersectionObserver(
  (entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      document.querySelectorAll(".nav-link").forEach((link) => {
        link.classList.toggle("active", link.dataset.nav === entry.target.id);
      });
    });
  },
  { rootMargin: "-45% 0px -45% 0px", threshold: 0 },
);

document.querySelectorAll("main section").forEach((section) => observer.observe(section));

updateQueryMeta();
renderTimeline();
renderMetrics();
renderReport();
renderBusinesses();
renderEvidence();
