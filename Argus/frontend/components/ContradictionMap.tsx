import type { ResearchReport } from "@/lib/api";
import { SectionCard, StatGrid, text } from "@/components/ui";

export function ContradictionMap({ report }: { report?: ResearchReport }) {
  const rows = ((report?.contradiction_map as Array<Record<string, unknown>> | undefined) || []).slice(0, 6);
  return (
    <SectionCard title="Contradiction Map">
      <StatGrid rows={rows.length ? rows.map((item, index) => [`${index + 1}. ${text(item.business_name)} - ${text(item.field)}`, `${text(item.severity)} - ${text(item.values)}`]) : [["Contradictions", "No contradictions detected"]]} />
    </SectionCard>
  );
}
