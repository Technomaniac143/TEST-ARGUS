import type { Business } from "@/lib/api";
import { SectionCard, text } from "@/components/ui";

export function EvidenceGraphTree({ business }: { business?: Business }) {
  const graph = business?.evidence_graph as { nodes?: Array<Record<string, unknown>>; edges?: Array<Record<string, unknown>> } | undefined;
  return (
    <SectionCard title="Evidence Graph">
      <p className="text-sm text-muted">{business?.name || "No business selected"}</p>
      <div className="mt-4 grid gap-3 md:grid-cols-2">
        {(business?.evidence || []).slice(0, 8).map((item, index) => (
          <div
            className="rounded-[22px] border border-line/70 bg-white/58 p-4 text-sm"
            key={`${business?.id || business?.name || "business"}-${text(item.field)}-${text(item.value)}-${text(item.source)}-${text(item.url)}-${index}`}
          >
            <strong className="text-ink">{text(item.field)}</strong>
            <p className="mt-1 text-slate-700">{text(item.value)}</p>
            <p className="mt-2 text-xs text-muted">{text(item.source)} - {text(item.extraction_method)}</p>
          </div>
        ))}
      </div>
      <p className="mt-4 text-xs text-muted">{graph?.nodes?.length || 0} graph nodes - {graph?.edges?.length || 0} graph edges</p>
    </SectionCard>
  );
}
