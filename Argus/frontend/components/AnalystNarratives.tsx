import type { ResearchReport } from "@/lib/api";
import { SectionCard, StatGrid } from "@/components/ui";

export function AnalystNarratives({ report }: { report?: ResearchReport }) {
  const narratives = (report?.market_narratives || {}) as Record<string, string>;
  return <SectionCard title="Analyst Narratives"><StatGrid rows={Object.entries(narratives).map(([key, value]) => [key.replaceAll("_", " "), value])} /></SectionCard>;
}
