import type { Business } from "@/lib/api";
import { ListBlock, SectionCard } from "@/components/ui";

export function SWOTAnalysis({ business }: { business?: Business }) {
  const swot = (business?.swot || {}) as Record<string, unknown[]>;
  return (
    <SectionCard title="SWOT Analysis">
      <div className="grid gap-4 md:grid-cols-2">
        <div><h3 className="font-semibold text-slate-100">Strengths</h3><ListBlock items={swot.strengths} /></div>
        <div><h3 className="font-semibold text-slate-100">Weaknesses</h3><ListBlock items={swot.weaknesses} /></div>
        <div><h3 className="font-semibold text-slate-100">Opportunities</h3><ListBlock items={swot.opportunities} /></div>
        <div><h3 className="font-semibold text-slate-100">Threats</h3><ListBlock items={swot.threats} /></div>
      </div>
    </SectionCard>
  );
}
