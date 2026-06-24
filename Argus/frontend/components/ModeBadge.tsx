export function ModeBadge({ mode, cacheHit }: { mode?: string; cacheHit?: boolean }) {
  return (
    <div className="premium-chip inline-flex items-center gap-2 rounded-full px-4 py-2 text-sm shadow-sm">
      <span className="font-semibold">Active Mode:</span>
      <span>{mode || "Waiting"}</span>
      {cacheHit ? <span className="rounded-full bg-emerald-100 px-2 py-0.5 text-emerald-700">cache hit</span> : null}
    </div>
  );
}
