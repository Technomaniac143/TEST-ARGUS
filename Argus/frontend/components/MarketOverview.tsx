import type { ResearchReport } from "@/lib/api";
import { SectionCard, StatGrid, text } from "@/components/ui";

export function MarketOverview({ report }: { report?: ResearchReport }) {
  const overview = (report?.market_overview || {}) as Record<string, unknown>;
  return (
    <SectionCard title="Market Overview">
      <StatGrid rows={[
        ["Total businesses", text(overview.total_businesses, "0")],
        ["Average DNA", text(overview.average_dna, "0")],
        ["Top cluster", text(overview.top_cluster)],
        ["High confidence", text(overview.high_confidence_businesses, "0")],
        ["Most common services", text(overview.most_common_services)],
        ["Most common specialties", text(overview.most_common_specialties)],
      ]} />
    </SectionCard>
  );
}
