import type { ResearchReport } from "@/lib/api";

export function ExecutiveReport({ report }: { report?: ResearchReport }) {
  if (!report) return null;
  const scorecard = report.scorecard || {};
  const recommendations = report.recommendations || {};
  return (
    <section className="premium-panel rounded-[36px] p-7 md:p-8">
      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">Executive Report</p>
      <h2 className="font-display mt-2 text-4xl font-semibold tracking-tight text-ink">Executive Intelligence</h2>
      <p className="mt-4 max-w-5xl text-sm leading-7 text-slate-700">{report.executive_summary || "Report is being generated."}</p>
      <div className="mt-4 grid gap-3 md:grid-cols-3">
        {Object.entries(scorecard).slice(0, 6).map(([label, value]) => (
          <div className="rounded-2xl border border-line/80 bg-white/60 p-4" key={label}>
            <span className="block text-xs font-semibold uppercase tracking-[0.16em] text-muted">{label.replaceAll("_", " ")}</span>
            <strong className="mt-2 block text-lg text-ink">{String(value)}</strong>
          </div>
        ))}
      </div>
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        <div>
          <h3 className="font-display font-semibold">Top Recommendations</h3>
          <ul className="mt-2 list-inside list-disc text-sm leading-6 text-slate-700">
            {(report.top_recommendations || []).slice(0, 3).map((item) => <li key={item}>{item}</li>)}
          </ul>
        </div>
        <div>
          <h3 className="font-display font-semibold">Immediate Actions</h3>
          <ul className="mt-2 list-inside list-disc text-sm leading-6 text-slate-700">
            {(recommendations.immediate_actions || []).slice(0, 3).map((item) => <li key={item}>{item}</li>)}
          </ul>
        </div>
      </div>
    </section>
  );
}
