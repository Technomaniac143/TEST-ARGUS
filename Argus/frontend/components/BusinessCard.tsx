import type { Business } from "@/lib/api";

export function BusinessCard({ business }: { business: Business }) {
  return (
    <article className="premium-panel group flex min-h-52 flex-col justify-between rounded-[30px] p-5 transition duration-200 hover:-translate-y-1 hover:shadow-[0_26px_70px_rgba(15,23,42,0.11)]">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="font-display text-lg font-semibold text-ink">{business.name || "Unnamed business"}</h3>
          <p className="mt-1 text-sm leading-5 text-muted">{business.address || business.location || "Address pending"}</p>
        </div>
        <span className="rounded-full bg-indigo-50 px-3 py-1 text-sm font-semibold text-accent">{business.dna_score ?? 0}</span>
      </div>
      <div className="mt-5 grid gap-2 text-sm leading-6 text-slate-700">
        <span>Reliability: {business.reliability || "Pending"}</span>
        <span>Risk: {business.risk || "Pending"}</span>
        <span>{business.executive_recommendation || business.recommendation || "Review pending"}</span>
      </div>
    </article>
  );
}
