import type { ResearchSession } from "@/lib/api";

export function CacheHitBanner({ session }: { session?: ResearchSession | null }) {
  const cacheHit = Boolean(session?.cache_hit || session?.report?.cache_hit);
  const age = session?.cache_age_seconds ?? session?.report?.cache_age_seconds;
  if (!cacheHit) return null;
  const ageText = typeof age === "number" ? ` · verified result restored in ${Math.max(0, Math.round(age))} seconds.` : ".";
  return (
    <div className="rounded-full border border-emerald-200 bg-emerald-50/90 px-4 py-3 text-sm font-semibold text-emerald-800 shadow-sm">
      Cached research reused{ageText}
    </div>
  );
}
