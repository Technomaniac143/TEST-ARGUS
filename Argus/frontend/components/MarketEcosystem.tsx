import type { ResearchReport } from "@/lib/api";
import { SectionCard, StatGrid, text } from "@/components/ui";

export function MarketEcosystem({ report }: { report?: ResearchReport }) {
  const ecosystem = (report?.ecosystem_summary || {}) as Record<string, unknown>;
  return (
    <SectionCard title="Market Ecosystem">
      <StatGrid rows={[
        ["Shared services", text(ecosystem.shared_services)],
        ["Dominant specialties", text(ecosystem.dominant_specialties)],
        ["Dominant certifications", text(ecosystem.dominant_certifications)],
        ["Most common flags", text(ecosystem.most_common_flags)],
        ["Outliers", text(ecosystem.outliers)],
      ]} />
    </SectionCard>
  );
}
