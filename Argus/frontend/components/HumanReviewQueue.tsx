import type { ResearchReport } from "@/lib/api";
import { SectionCard, StatGrid, text } from "@/components/ui";

export function HumanReviewQueue({ report }: { report?: ResearchReport }) {
  const rows = ((report?.review_queue as Array<Record<string, unknown>> | undefined) || []).slice(0, 6);
  return (
    <SectionCard title="Human Review Queue">
      <StatGrid rows={rows.length ? rows.map((item, index) => [`${index + 1}. ${text(item.business_name)} - ${text(item.severity)}`, text(item.reason)]) : [["Review queue", "No manual review items"]]} />
    </SectionCard>
  );
}
