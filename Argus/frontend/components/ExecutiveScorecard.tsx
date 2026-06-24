import type { ResearchReport } from "@/lib/api";
import { SectionCard, StatGrid } from "@/components/ui";

export function ExecutiveScorecard({ report }: { report?: ResearchReport }) {
  const scorecard = (report?.scorecard || {}) as Record<string, number>;
  return <SectionCard title="Executive Scorecard"><StatGrid rows={Object.entries(scorecard).map(([key, value]) => [key.replaceAll("_", " "), value])} /></SectionCard>;
}
