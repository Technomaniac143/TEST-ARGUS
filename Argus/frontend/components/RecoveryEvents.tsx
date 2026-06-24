import type { TimelineEvent } from "@/lib/api";
import { SectionCard } from "@/components/ui";

export function RecoveryEvents({ events }: { events?: TimelineEvent[] }) {
  const recovery = (events || []).filter((event) => event.event?.includes("recover")).slice(-5);
  return (
    <SectionCard title="Recovery Events">
      {recovery.length ? recovery.map((event, index) => <p className="text-sm leading-6 text-slate-700" key={`${event.event}-${event.message}-${index}`}>{event.message}</p>) : <p className="text-sm text-muted">No recovery events in this session.</p>}
    </SectionCard>
  );
}
