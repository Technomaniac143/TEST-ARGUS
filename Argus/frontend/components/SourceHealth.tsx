import type { ResearchReport } from "@/lib/api";
import { SectionCard, StatGrid, text } from "@/components/ui";

export function SourceHealth({ report }: { report?: ResearchReport }) {
  const health = (report?.source_health || {}) as Record<string, unknown>;
  return (
    <SectionCard title="Source Health">
      <StatGrid rows={[
        ["URLs discovered", text(health.urls_discovered, "0")],
        ["URLs crawled", text(health.urls_crawled, "0")],
        ["Cache hits", text(health.crawl_cache_hits, "0")],
        ["Cache misses", text(health.crawl_cache_misses, "0")],
        ["Failures", text(health.crawl_failures, "0")],
        ["Successful sources", text(health.successful_sources)],
      ]} />
    </SectionCard>
  );
}
