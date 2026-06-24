import type { Business, ResearchReport } from "@/lib/api";

function asList(value: unknown): string[] {
  if (!value) return [];
  if (Array.isArray(value)) {
    return value.map((item) => {
      if (typeof item === "string") return item;
      if (item && typeof item === "object") {
        const record = item as Record<string, unknown>;
        return String(record.business_name || record.name || record.reason || record.summary || record.recommended_action || record.field || "Reported signal");
      }
      return String(item);
    }).filter(Boolean);
  }
  return [String(value)];
}

function pickName(value: unknown, fallback = "No signal yet") {
  if (typeof value === "string") return value;
  if (value && typeof value === "object") {
    const record = value as Record<string, unknown>;
    return String(record.business_name || record.name || record.label || record.summary || fallback);
  }
  return fallback;
}

function InsightCard({ eyebrow, title, items }: { eyebrow: string; title: string; items: string[] }) {
  return (
    <article className="rounded-[28px] border border-white/70 bg-white/58 p-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.72)]">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">{eyebrow}</p>
      <h3 className="font-display mt-2 text-xl font-semibold tracking-tight text-ink">{title}</h3>
      <ul className="mt-4 space-y-3 text-sm leading-6 text-slate-700">
        {(items.length ? items : ["ARGUS is waiting for enough verified evidence to produce this insight."]).slice(0, 4).map((item, index) => (
          <li className="flex gap-3" key={`${eyebrow}-${item}-${index}`}>
            <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-accent/70" />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </article>
  );
}

export function EditorialInsights({ report, businesses }: { report?: ResearchReport; businesses?: Business[] }) {
  const top = businesses?.[0];
  const reviewQueue = asList(report?.review_queue);
  const risks = [
    ...asList(report?.risk_summary),
    ...reviewQueue,
    ...asList(report?.contradiction_map).slice(0, 2),
  ].filter(Boolean);
  const opportunities = [
    ...asList(report?.recommendations && (report.recommendations as Record<string, unknown>).high_opportunity_businesses),
    ...asList(top?.competitive_intelligence?.opportunity_gaps),
  ].filter(Boolean);
  const leaders = [
    pickName(report?.benchmarks && (report.benchmarks as Record<string, unknown>).best_overall_business, top?.name || "Top ranked business pending"),
    ...asList(report?.top_recommendations),
  ].filter(Boolean);
  const differentiated = [
    pickName(report?.benchmarks && (report.benchmarks as Record<string, unknown>).most_differentiated, "Differentiation pending"),
    ...asList(top?.competitive_intelligence?.strengths).slice(0, 2),
  ].filter(Boolean);
  const connected = [
    pickName(report?.benchmarks && (report.benchmarks as Record<string, unknown>).most_connected, "Relationship analysis pending"),
    pickName(report?.network_analysis && (report.network_analysis as Record<string, unknown>).most_connected_business, "Network centrality pending"),
  ].filter(Boolean);
  const lowCoverage = businesses
    ?.filter((business) => (business.dna_score || 0) < 70 || business.analyst_quality_flags?.includes("WEAK_SOURCE_COVERAGE"))
    .slice(0, 4)
    .map((business) => `${business.name || "Unnamed business"} needs stronger source coverage`) || [];

  return (
    <section className="premium-panel rounded-[36px] p-6 md:p-7">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">Editorial intelligence</p>
          <h2 className="font-display text-4xl font-semibold tracking-tight text-ink">Most Important Findings</h2>
        </div>
        <span className="premium-chip rounded-full px-3 py-1 text-xs font-semibold">Analyst-ready</span>
      </div>
      <p className="mt-4 max-w-4xl text-sm leading-7 text-slate-700">
        ARGUS condenses the verified evidence, market structure, relationship signals, and review risks into reader-friendly findings instead of raw payloads.
      </p>
      <div className="mt-6 grid gap-4 xl:grid-cols-3">
        <InsightCard eyebrow="Key findings" title="Market leaders" items={leaders} />
        <InsightCard eyebrow="Risks" title="Businesses requiring review" items={risks} />
        <InsightCard eyebrow="Opportunities" title="Coverage and growth gaps" items={opportunities} />
        <InsightCard eyebrow="Differentiation" title="Standout signals" items={differentiated} />
        <InsightCard eyebrow="Relationships" title="Most connected" items={connected} />
        <InsightCard eyebrow="Low coverage" title="Evidence gaps" items={lowCoverage} />
      </div>
    </section>
  );
}
