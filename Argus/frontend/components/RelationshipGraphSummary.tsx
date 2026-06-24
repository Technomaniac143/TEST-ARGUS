import type { ResearchReport } from "@/lib/api";
import { SectionCard, StatGrid, text } from "@/components/ui";

export function RelationshipGraphSummary({ report }: { report?: ResearchReport }) {
  const graph = (report?.relationship_graph || {}) as { nodes?: unknown[]; edges?: unknown[] };
  const ecosystem = (report?.ecosystem_summary || {}) as Record<string, unknown>;
  return (
    <SectionCard title="Relationship Graph Summary">
      <StatGrid rows={[
        ["Nodes", graph.nodes?.length || 0],
        ["Edges", graph.edges?.length || 0],
        ["Most connected", text(ecosystem.most_connected_business)],
        ["Most similar pair", text(ecosystem.most_similar_pair)],
        ["Most unique", text(ecosystem.most_unique_business)],
      ]} />
    </SectionCard>
  );
}
