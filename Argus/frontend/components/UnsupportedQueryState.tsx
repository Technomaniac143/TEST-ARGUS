import type { ResearchReport } from "@/lib/api";

export function UnsupportedQueryState({ report }: { report?: ResearchReport }) {
  if (!report?.unsupported_message || report.support_level === "FULL_CORPUS_MATCH") return null;
  return (
    <section className="rounded-[28px] border border-amber-200 bg-amber-50/80 p-5 shadow-sm">
      <h2 className="font-display text-xl font-semibold text-amber-950">Unsupported Offline Query</h2>
      <p className="mt-2 text-sm leading-6 text-amber-900">{report.unsupported_message}</p>
      <div className="mt-3 flex flex-wrap gap-2">
        {(report.suggested_queries || []).slice(0, 5).map((query) => (
          <span className="rounded-full bg-white px-3 py-1 text-sm text-amber-950" key={query}>{query}</span>
        ))}
      </div>
    </section>
  );
}
