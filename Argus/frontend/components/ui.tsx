import type { ReactNode } from "react";

export function SectionCard({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="premium-panel rounded-[28px] p-5">
      <h2 className="font-display text-lg font-semibold text-ink">{title}</h2>
      <div className="mt-4">{children}</div>
    </section>
  );
}

export function StatGrid({ rows }: { rows: Array<[string, ReactNode]> }) {
  return (
    <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
      {rows.map(([label, value], index) => (
        <div className="rounded-[26px] border border-white/70 bg-white/58 p-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.75)]" key={`${label}-${index}`}>
          <span className="block text-xs font-semibold uppercase tracking-[0.16em] text-muted">{label}</span>
          <strong className="mt-2 block text-sm text-ink">{value || "none"}</strong>
        </div>
      ))}
    </div>
  );
}

export function ListBlock({ items }: { items?: unknown[] }) {
  const values = (items || []).slice(0, 6).map((item) => String(item));
  if (!values.length) return <p className="text-sm text-muted">No items reported.</p>;
  return (
    <ul className="space-y-2 text-sm leading-6 text-slate-700">
      {values.map((item, index) => <li key={`${item}-${index}`}>- {item}</li>)}
    </ul>
  );
}

export function text(value: unknown, fallback = "none"): string {
  if (value == null || value === "") return fallback;
  if (Array.isArray(value)) return value.map((item) => text(item)).join("; ");
  if (typeof value === "object") return JSON.stringify(value);
  return String(value);
}
