import type { ResearchSession } from "@/lib/api";

export function MetricsCards({ session }: { session?: ResearchSession | null }) {
  const report = session?.report;
  const rows = [
    ["Businesses", report?.businesses_found ?? session?.businesses_found ?? 0],
    ["Verified", report?.businesses_verified ?? session?.job?.verified_businesses ?? 0],
    ["Sources", report?.sources_searched ?? session?.sources_searched ?? 0],
    ["Duration", `${report?.research_duration ?? session?.duration ?? 0}s`],
  ];
  return (
    <section className="grid gap-3 md:grid-cols-4">
      {rows.map(([label, value]) => (
        <article className="premium-panel rounded-[28px] p-5" key={label}>
          <p className="text-xs font-semibold uppercase tracking-[0.16em] text-muted">{label}</p>
          <strong className="font-display mt-2 block text-3xl text-ink">{value}</strong>
        </article>
      ))}
    </section>
  );
}
