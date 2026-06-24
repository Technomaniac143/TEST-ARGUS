import type { Business } from "@/lib/api";
import { SectionCard, StatGrid } from "@/components/ui";

export function BusinessDNA({ business }: { business?: Business }) {
  const dna = (business?.dna_breakdown || {}) as Record<string, number>;
  return (
    <SectionCard title="Business DNA">
      <StatGrid rows={[
        ["Final score", business?.dna_score ?? 0],
        ["Evidence strength", dna.evidence_strength ?? 0],
        ["Source diversity", dna.source_diversity ?? 0],
        ["Completeness", dna.completeness ?? 0],
        ["Conflict penalty", dna.conflict_penalty ?? 0],
      ]} />
    </SectionCard>
  );
}
