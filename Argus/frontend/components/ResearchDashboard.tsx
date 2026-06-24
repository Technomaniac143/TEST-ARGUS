"use client";

import { motion } from "framer-motion";
import { useEffect, useMemo, useRef, useState } from "react";
import { AdapterHealth } from "@/components/AdapterHealth";
import { AnalystNarratives } from "@/components/AnalystNarratives";
import { BusinessCard } from "@/components/BusinessCard";
import { BusinessDNA } from "@/components/BusinessDNA";
import { CacheHitBanner } from "@/components/CacheHitBanner";
import { ChallengeCoverage } from "@/components/ChallengeCoverage";
import { CompetitiveIntelligence } from "@/components/CompetitiveIntelligence";
import { ContradictionMap } from "@/components/ContradictionMap";
import { EditorialInsights } from "@/components/EditorialInsights";
import { EvidenceGraphTree } from "@/components/EvidenceGraphTree";
import { ExecutiveReport } from "@/components/ExecutiveReport";
import { ExecutiveScorecard } from "@/components/ExecutiveScorecard";
import { ExportButtons } from "@/components/ExportButtons";
import { HumanReviewQueue } from "@/components/HumanReviewQueue";
import { IntelligenceGraph } from "@/components/IntelligenceGraph";
import { MarketEcosystem } from "@/components/MarketEcosystem";
import { MarketOverview } from "@/components/MarketOverview";
import { MetricsCards } from "@/components/MetricsCards";
import { ProgressPanel } from "@/components/ProgressPanel";
import { Recommendations } from "@/components/Recommendations";
import { RecoveryEvents } from "@/components/RecoveryEvents";
import { RelationshipGraphSummary } from "@/components/RelationshipGraphSummary";
import { SearchBar } from "@/components/SearchBar";
import { SourceHealth } from "@/components/SourceHealth";
import { SWOTAnalysis } from "@/components/SWOTAnalysis";
import { TopBar } from "@/components/TopBar";
import { UnsupportedQueryState } from "@/components/UnsupportedQueryState";
import {
  type ArgusMode,
  ApiError,
  type Business,
  type ResearchSession,
  type TimelineEvent,
  getBasicResearch,
  startResearch,
  streamResearchEvents,
} from "@/lib/api";

type Workspace = "research" | "intelligence" | "evidence" | "operations" | "review";

const workspaces: Array<{ id: Workspace; label: string; helper: string }> = [
  { id: "research", label: "Research", helper: "Live progress and ranked candidates" },
  { id: "intelligence", label: "Intelligence", helper: "Executive findings and narratives" },
  { id: "evidence", label: "Evidence", helper: "Graphs, sources, contradictions" },
  { id: "operations", label: "Operations", helper: "Coverage, health, recovery" },
  { id: "review", label: "Review", helper: "Human review and quality flags" },
];

function numberValue(value: unknown): number {
  return typeof value === "number" && Number.isFinite(value) ? value : 0;
}

function businessDnaScore(business?: Business): number | undefined {
  if (!business) return undefined;
  const score = business.dna_score ?? business.dnaScore;
  return typeof score === "number" && Number.isFinite(score) ? score : undefined;
}

function businessRisk(business?: Business): string | undefined {
  return business?.risk || business?.risk_level;
}

function businessFlags(business?: Business): string[] {
  return business?.analyst_quality_flags || business?.quality_flags || business?.flags || [];
}

function rankedBusinesses(session: ResearchSession | null): Business[] {
  const businesses = session?.businesses || [];
  return [...businesses].sort((left, right) => {
    const leftRank = numberValue((left as Record<string, unknown>).rank);
    const rightRank = numberValue((right as Record<string, unknown>).rank);
    if (leftRank && rightRank && leftRank !== rightRank) return leftRank - rightRank;
    return (
      numberValue(right.dna_score ?? right.dnaScore) - numberValue(left.dna_score ?? left.dnaScore) ||
      numberValue(right.confidence) - numberValue(left.confidence)
    );
  });
}

function recommendationFallback(session: ResearchSession | null): string {
  const topFromReport = session?.report?.top_recommended_businesses?.[0];
  if (topFromReport) {
    const name = topFromReport.name || topFromReport.business_name || topFromReport.title;
    if (name) return String(name);
  }
  const rankedFromReport = session?.report?.ranked_businesses?.[0];
  if (rankedFromReport) {
    const name = rankedFromReport.name || rankedFromReport.business_name || rankedFromReport.title;
    if (name) return String(name);
  }
  return session?.report?.top_recommendations?.[0] || "Run research to identify the strongest business";
}

function SignalFeed({ events }: { events: TimelineEvent[] }) {
  const visible = events.slice(-9).reverse();
  return (
    <section className="premium-panel rounded-[32px] p-6">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">Signal Feed</p>
      <h2 className="font-display mt-1 text-2xl font-semibold tracking-tight text-ink">Live Research Signals</h2>
      <div className="mt-5 space-y-3">
        {visible.length ? visible.map((event, index) => (
          <motion.div
            className="rounded-[22px] border border-white/70 bg-white/58 p-4"
            key={`${event.event}-${event.message}-${index}`}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.18, delay: index * 0.015 }}
          >
            <div className="flex items-center justify-between gap-3">
              <strong className="text-sm text-ink">{event.message}</strong>
              <span className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">{event.stage || event.status || event.event}</span>
            </div>
          </motion.div>
        )) : <p className="text-sm text-muted">Start a search to watch ARGUS discover, verify, and rank evidence.</p>}
      </div>
    </section>
  );
}

function WorkspaceTabs({ active, onChange }: { active: Workspace; onChange: (value: Workspace) => void }) {
  return (
    <nav className="premium-panel sticky top-20 z-20 rounded-[30px] p-2">
      <div className="grid gap-2 md:grid-cols-5">
        {workspaces.map((workspace) => {
          const selected = active === workspace.id;
          return (
            <button
              className={`rounded-[24px] px-4 py-3 text-left transition ${selected ? "bg-ink text-white shadow-[0_18px_38px_rgba(15,23,42,0.18)]" : "text-slate-700 hover:bg-white/70"}`}
              key={workspace.id}
              onClick={() => onChange(workspace.id)}
              type="button"
            >
              <span className="block text-sm font-semibold">{workspace.label}</span>
              <span className={`mt-1 block text-xs leading-4 ${selected ? "text-white/72" : "text-muted"}`}>{workspace.helper}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}

function TopRecommendation({ business, fallback }: { business?: Business; fallback: string }) {
  const dnaScore = businessDnaScore(business);
  const risk = businessRisk(business);
  const flags = businessFlags(business);
  return (
    <section className="premium-panel rounded-[32px] p-6">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">Top Recommendation</p>
      <h2 className="font-display mt-2 text-3xl font-semibold tracking-tight text-ink">{business?.name || fallback}</h2>
      <p className="mt-3 text-sm leading-6 text-slate-700">
        {business
          ? `${business.reliability || business.confidence_label || "Pending reliability"} reliability with DNA ${dnaScore ?? 0}. ${business.executive_recommendation || business.recommendation || "Recommendation pending."}`
          : "ARGUS will surface the strongest verified candidate here as evidence arrives."}
      </p>
      <div className="mt-5 grid gap-3 sm:grid-cols-3">
        <div className="rounded-[22px] border border-white/70 bg-white/58 p-4">
          <span className="text-xs font-semibold uppercase tracking-[0.16em] text-muted">DNA</span>
          <strong className="mt-1 block text-2xl text-ink">{dnaScore ?? "--"}</strong>
        </div>
        <div className="rounded-[22px] border border-white/70 bg-white/58 p-4">
          <span className="text-xs font-semibold uppercase tracking-[0.16em] text-muted">Risk</span>
          <strong className="mt-1 block text-sm text-ink">{risk || "Pending"}</strong>
        </div>
        <div className="rounded-[22px] border border-white/70 bg-white/58 p-4">
          <span className="text-xs font-semibold uppercase tracking-[0.16em] text-muted">Flags</span>
          <strong className="mt-1 block text-sm text-ink">{flags.slice(0, 2).join(", ") || "None"}</strong>
        </div>
      </div>
    </section>
  );
}

export function ResearchDashboard({ initialSessionId }: { initialSessionId?: string }) {
  const [query, setQuery] = useState("Cardiologists in Chennai");
  const [mode, setMode] = useState<ArgusMode>("offline");
  const [workspace, setWorkspace] = useState<Workspace>("research");
  const [sessionId, setSessionId] = useState<string | null>(initialSessionId || null);
  const [session, setSession] = useState<ResearchSession | null>(null);
  const [events, setEvents] = useState<TimelineEvent[]>([]);
  const [error, setError] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const currentSessionIdRef = useRef<string | null>(initialSessionId || null);
  const pollingFailureCountRef = useRef(0);

  const running = Boolean(
    sessionId &&
    session?.status !== "complete" &&
    session?.status !== "failed" &&
    !(session?.status === "partial" && session?.report_ready) &&
    session?.job?.status !== "failed" &&
    session?.job?.status !== "cancelled",
  );
  const topBusinesses = useMemo(() => rankedBusinesses(session).slice(0, 8), [session]);
  const selectedBusiness = topBusinesses[0];
  const reviewBusinesses = useMemo(
    () => (session?.businesses || []).filter((business) =>
      businessFlags(business).includes("NEEDS_HUMAN_REVIEW") ||
      businessFlags(business).includes("CONFLICT_DETECTED") ||
      (businessDnaScore(business) || 0) < 70,
    ).slice(0, 6),
    [session],
  );
  const allEvents = events.length ? events : session?.timeline_events || [];
  const topRecommendation = selectedBusiness?.name || recommendationFallback(session);

  useEffect(() => () => eventSourceRef.current?.close(), []);

  useEffect(() => {
    currentSessionIdRef.current = sessionId;
  }, [sessionId]);

  useEffect(() => {
    if (!initialSessionId) return;
    setSessionId(initialSessionId);
    connect(initialSessionId);
    void refreshOnce(initialSessionId);
  }, [initialSessionId]);

  useEffect(() => {
    if (!sessionId) return;
    let cancelled = false;
    const interval = window.setInterval(async () => {
      try {
        const latest = await getBasicResearch(sessionId);
        pollingFailureCountRef.current = 0;
        if (!cancelled && currentSessionIdRef.current === sessionId) setSession(latest);
        if (
          latest.status === "complete" ||
          latest.status === "failed" ||
          (latest.status === "partial" && latest.report_ready) ||
          latest.job?.status === "failed" ||
          latest.job?.status === "cancelled"
        ) {
          window.clearInterval(interval);
        }
      } catch (err) {
        if (!cancelled && err instanceof ApiError && err.status === 404 && currentSessionIdRef.current === sessionId) {
          eventSourceRef.current?.close();
          currentSessionIdRef.current = null;
          setSessionId(null);
          window.clearInterval(interval);
          setError("This research session is no longer available on the backend. Start a new search to create a fresh production session.");
        } else if (!cancelled) {
          pollingFailureCountRef.current += 1;
          if (pollingFailureCountRef.current >= 2) {
            eventSourceRef.current?.close();
            window.clearInterval(interval);
            setError("ARGUS paused live polling after repeated backend errors. Refresh or start a new search after the backend recovers.");
          } else {
            setError(err instanceof Error ? err.message : "Unable to refresh research session");
          }
        }
      }
    }, 700);
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [sessionId]);

  async function refreshOnce(id: string) {
    try {
      const latest = await getBasicResearch(id);
      pollingFailureCountRef.current = 0;
      if (currentSessionIdRef.current === id) setSession(latest);
    } catch (err) {
      if (err instanceof ApiError && err.status === 404 && currentSessionIdRef.current === id) {
        eventSourceRef.current?.close();
        currentSessionIdRef.current = null;
        setSessionId(null);
        setError("This research session is no longer available on the backend. Start a new search to create a fresh production session.");
      } else {
        setError(err instanceof Error ? err.message : "Unable to load session");
      }
    }
  }

  function connect(id: string) {
    eventSourceRef.current?.close();
    eventSourceRef.current = streamResearchEvents(
      id,
      (event) => setEvents((current) => [...current, event]),
      () => eventSourceRef.current?.close(),
    );
  }

  async function runResearch(submittedQuery = query, submittedMode = mode) {
    setError(null);
    setWorkspace("research");
    eventSourceRef.current?.close();
    currentSessionIdRef.current = null;
    setSessionId(null);
    setEvents([{ event: "job_queued", message: "Research job queued", status: "queued" }]);
    setSession(null);
    pollingFailureCountRef.current = 0;
    setQuery(submittedQuery);
    setMode(submittedMode);
    try {
      const started = await startResearch(submittedQuery, submittedMode);
      currentSessionIdRef.current = started.session_id;
      setSessionId(started.session_id);
      connect(started.session_id);
      await refreshOnce(started.session_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to start ARGUS research");
    }
  }

  return (
    <motion.main className="min-h-screen text-ink" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.35 }}>
      <TopBar mode={session?.report?.active_mode || mode} cacheHit={session?.cache_hit || session?.report?.cache_hit} status={session?.job?.status || session?.status || "ready"} />
      <header className="px-5 pb-10 pt-10 md:pt-16">
        <div className="mx-auto flex max-w-6xl flex-col gap-8">
          <div className="grid gap-8 lg:grid-cols-[1fr_0.82fr] lg:items-end">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.24em] text-accent">Autonomous intelligence workspace</p>
              <h1 className="font-display mt-4 text-7xl font-semibold leading-none tracking-tight text-ink md:text-8xl">ARGUS</h1>
              <p className="mt-4 max-w-2xl text-xl leading-8 text-muted">Autonomous Business Intelligence Analyst</p>
            </div>
            <TopRecommendation business={selectedBusiness} fallback={String(topRecommendation)} />
          </div>
          <SearchBar query={query} mode={mode} running={running} onQueryChange={setQuery} onModeChange={setMode} onSubmit={runResearch} />
          <div className="grid gap-4 md:grid-cols-4">
            <div className="premium-panel rounded-[28px] p-5 md:col-span-2">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">Active query</p>
              <strong className="font-display mt-2 block text-2xl text-ink">{session?.query || query}</strong>
            </div>
            <div className="premium-panel rounded-[28px] p-5">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">Current stage</p>
              <strong className="font-display mt-2 block text-2xl text-ink">{session?.job?.current_stage || session?.job?.status || "ready"}</strong>
            </div>
            <div className="premium-panel rounded-[28px] p-5">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">Workspace</p>
              <strong className="font-display mt-2 block text-2xl text-ink">{workspace}</strong>
            </div>
          </div>
        </div>
      </header>

      <section className="mx-auto grid max-w-6xl gap-7 px-5 pb-16">
        {error ? <div className="rounded-[24px] border border-red-200 bg-red-50 p-4 text-red-800">{error}</div> : null}
        <CacheHitBanner session={session} />
        <WorkspaceTabs active={workspace} onChange={setWorkspace} />
        <UnsupportedQueryState report={session?.report} />

        {workspace === "research" ? (
          <div className="grid gap-7">
            <div className="grid gap-5 xl:grid-cols-[1.05fr_0.95fr]">
              <ProgressPanel session={session} events={allEvents} />
              <SignalFeed events={allEvents} />
            </div>
            <MetricsCards session={session} />
            <div className="flex flex-col justify-between gap-3 md:flex-row md:items-end">
              <div>
                <p className="text-xs font-semibold uppercase tracking-[0.2em] text-muted">Ranked candidates</p>
                <h2 className="font-display text-4xl font-semibold tracking-tight">Top Business Results</h2>
              </div>
              <ExportButtons session={session} />
            </div>
            <motion.section className="grid gap-5 md:grid-cols-2 xl:grid-cols-4" initial="hidden" animate="visible" variants={{ visible: { transition: { staggerChildren: 0.04 } } }}>
              {topBusinesses.length ? topBusinesses.map((business) => (
                <motion.div key={business.id} variants={{ hidden: { opacity: 0, y: 12 }, visible: { opacity: 1, y: 0 } }} transition={{ duration: 0.25 }}>
                  <BusinessCard business={business} />
                </motion.div>
              )) : (
                <article className="premium-panel rounded-[28px] p-5 text-muted">Run research to display ranked business cards.</article>
              )}
            </motion.section>
          </div>
        ) : null}

        {workspace === "intelligence" ? (
          <div className="grid gap-7">
            <ExecutiveReport report={session?.report} />
            <EditorialInsights report={session?.report} businesses={session?.businesses} />
            <section className="grid gap-5 xl:grid-cols-2">
              <ExecutiveScorecard report={session?.report} />
              <Recommendations report={session?.report} />
              <SWOTAnalysis business={selectedBusiness} />
              <CompetitiveIntelligence report={session?.report} business={selectedBusiness} />
              <MarketOverview report={session?.report} />
              <AnalystNarratives report={session?.report} />
            </section>
          </div>
        ) : null}

        {workspace === "evidence" ? (
          <div className="grid gap-7">
            <IntelligenceGraph business={selectedBusiness} report={session?.report} />
            <section className="grid gap-5 xl:grid-cols-2">
              <EvidenceGraphTree business={selectedBusiness} />
              <RelationshipGraphSummary report={session?.report} />
              <ContradictionMap report={session?.report} />
              <BusinessDNA business={selectedBusiness} />
              <MarketEcosystem report={session?.report} />
            </section>
          </div>
        ) : null}

        {workspace === "operations" ? (
          <div className="grid gap-7">
            <section className="premium-panel rounded-[36px] p-7">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">Operations</p>
              <h2 className="font-display text-4xl font-semibold tracking-tight text-ink">Coverage and System Health</h2>
              <p className="mt-3 max-w-4xl text-sm leading-7 text-slate-700">
                ARGUS keeps source health, cache behavior, recovery events, and challenge coverage visible so the research process stays auditable.
              </p>
            </section>
            <section className="grid gap-5 xl:grid-cols-2">
              <SourceHealth report={session?.report} />
              <AdapterHealth report={session?.report} />
              <ChallengeCoverage report={session?.report} />
              <RecoveryEvents events={session?.timeline_events || events} />
            </section>
          </div>
        ) : null}

        {workspace === "review" ? (
          <div className="grid gap-7">
            <HumanReviewQueue report={session?.report} />
            <section className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
              {(reviewBusinesses.length ? reviewBusinesses : topBusinesses.slice(0, 3)).map((business) => (
                <BusinessCard business={business} key={`review-${business.id}`} />
              ))}
              {!topBusinesses.length ? <article className="premium-panel rounded-[28px] p-5 text-muted">Review signals will appear after research completes.</article> : null}
            </section>
          </div>
        ) : null}
      </section>
    </motion.main>
  );
}
