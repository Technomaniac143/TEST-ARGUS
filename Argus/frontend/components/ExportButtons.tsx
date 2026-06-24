import type { ResearchSession } from "@/lib/api";

export function ExportButtons({ session }: { session?: ResearchSession | null }) {
  const downloadJson = () => {
    if (!session) return;
    const blob = new Blob([JSON.stringify(session, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "argus-next-preview-report.json";
    anchor.click();
    URL.revokeObjectURL(url);
  };
  const downloadCsv = () => {
    if (!session) return;
    const rows = [
      ["business_name", "phone", "website", "dna_score", "reliability", "recommendation", "overall_intelligence_score", "centrality_score", "top_relationship"],
      ...session.businesses.map((business) => [
        business.name || "",
        business.phone || "",
        business.website || "",
        business.dna_score || 0,
        business.reliability || "",
        business.executive_recommendation || business.recommendation || "",
        business.overall_intelligence_score || 0,
        business.centrality_score || 0,
        business.top_relationship || "",
      ]),
    ];
    const csv = rows.map((row) => row.map((cell) => `"${String(cell).replaceAll('"', '""')}"`).join(",")).join("\n");
    const blob = new Blob([csv], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "argus-next-preview-report.csv";
    anchor.click();
    URL.revokeObjectURL(url);
  };
  return (
    <div className="flex gap-2">
      <button className="rounded-full border border-line/80 bg-white/70 px-4 py-2 text-sm font-semibold text-ink shadow-sm transition hover:-translate-y-0.5 disabled:opacity-50" onClick={downloadJson} disabled={!session}>
        Download JSON
      </button>
      <button className="rounded-full border border-line/80 bg-white/70 px-4 py-2 text-sm font-semibold text-ink shadow-sm transition hover:-translate-y-0.5 disabled:opacity-50" onClick={downloadCsv} disabled={!session}>
        Download CSV
      </button>
    </div>
  );
}
