import type { Business, ResearchReport } from "@/lib/api";
import { SectionCard, StatGrid, text } from "@/components/ui";

export function CompetitiveIntelligence({ report, business }: { report?: ResearchReport; business?: Business }) {
  const comparison = (report?.market_comparison || {}) as Record<string, unknown>;
  const intel = (business?.competitive_intelligence || {}) as Record<string, unknown>;
  return (
    <SectionCard title="Competitive Intelligence">
      <StatGrid rows={[
        ["Strongest business", text(comparison.strongest_business)],
        ["Weakest business", text(comparison.weakest_business)],
        ["Highest rated", text(comparison.highest_rated)],
        ["Strengths", text(intel.strengths)],
        ["Weaknesses", text(intel.weaknesses)],
        ["Differentiation", text(intel.differentiation_summary)],
      ]} />
    </SectionCard>
  );
}
