import type { ResearchSession, TimelineEvent } from "@/lib/api";

export function ProgressPanel({ session, events }: { session?: ResearchSession | null; events: TimelineEvent[] }) {
  const job = session?.job;
  return (
    <section className="premium-panel rounded-[32px] p-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-muted">Research Progress</p>
          <h2 className="font-display text-2xl font-semibold text-ink">{job?.current_stage || "queued"}</h2>
        </div>
        <strong className="rounded-full bg-indigo-50 px-4 py-2 text-accent">{job?.stage_progress ?? 0}%</strong>
      </div>
      <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-200/80">
        <div className="h-full rounded-full bg-accent transition-all duration-500" style={{ width: `${job?.stage_progress ?? 0}%` }} />
      </div>
      <div className="mt-4 grid grid-cols-2 gap-3 text-sm text-slate-700 md:grid-cols-4">
        <span>Status: {job?.status || session?.status || "queued"}</span>
        <span>URLs: {job?.processed_urls ?? 0}/{job?.total_urls ?? 0}</span>
        <span>Verified: {job?.verified_businesses ?? 0}</span>
        <span>Failed URLs: {job?.failed_urls ?? 0}</span>
      </div>
      <div className="mt-5 max-h-40 overflow-auto border-t border-line/60 pt-4 text-sm leading-6 text-muted">
        {(events.length ? events : session?.timeline_events || []).slice(-8).map((event, index) => (
          <p key={`${event.event}-${index}`}>{event.message}</p>
        ))}
      </div>
    </section>
  );
}
