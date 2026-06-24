import type { ResearchReport } from "@/lib/api";
import { SectionCard, StatGrid, text } from "@/components/ui";

export function AdapterHealth({ report }: { report?: ResearchReport }) {
  const adapters = (report?.adapter_health || {}) as Record<string, Record<string, unknown>>;
  const rows = Object.entries(adapters).slice(0, 8).map(([name, health]) => [name, `${text(health.health_score, "n/a")} health · ${text(health.failure_count, "0")} failures`] as [string, string]);
  return <SectionCard title="Adapter Health"><StatGrid rows={rows.length ? rows : [["Adapters", "No adapter activity in this mode"]]} /></SectionCard>;
}
