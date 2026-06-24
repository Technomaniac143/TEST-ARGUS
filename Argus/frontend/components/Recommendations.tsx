import type { ResearchReport } from "@/lib/api";
import { ListBlock, SectionCard } from "@/components/ui";

export function Recommendations({ report }: { report?: ResearchReport }) {
  const recommendations = (report?.recommendations || {}) as Record<string, unknown[]>;
  return (
    <SectionCard title="Recommendations">
      <div className="grid gap-4 md:grid-cols-2">
        <div><h3 className="font-semibold text-slate-100">Immediate actions</h3><ListBlock items={recommendations.immediate_actions} /></div>
        <div><h3 className="font-semibold text-slate-100">Safe for outreach</h3><ListBlock items={recommendations.businesses_safe_for_outreach} /></div>
        <div><h3 className="font-semibold text-slate-100">Manual review</h3><ListBlock items={recommendations.businesses_requiring_manual_review} /></div>
        <div><h3 className="font-semibold text-slate-100">High opportunity</h3><ListBlock items={recommendations.high_opportunity_businesses} /></div>
      </div>
    </SectionCard>
  );
}
