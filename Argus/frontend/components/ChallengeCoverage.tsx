import type { ResearchReport } from "@/lib/api";
import { SectionCard, StatGrid } from "@/components/ui";

export function ChallengeCoverage({ report }: { report?: ResearchReport }) {
  const coverage = (report?.challenge_requirement_coverage || report?.requirement_coverage || {}) as Record<string, string>;
  return <SectionCard title="Challenge Coverage"><StatGrid rows={Object.entries(coverage).slice(0, 18)} /></SectionCard>;
}
