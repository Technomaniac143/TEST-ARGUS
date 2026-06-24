import { ModeBadge } from "@/components/ModeBadge";

export function TopBar({ mode, cacheHit, status }: { mode?: string; cacheHit?: boolean; status?: string }) {
  return (
    <header className="sticky top-0 z-40 border-b border-ink-900/[0.06] bg-marble/82 backdrop-blur-xl">
      <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-5">
        <div className="flex items-center gap-8">
          <div className="flex items-center gap-2">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" aria-hidden>
              <circle cx="10" cy="10" r="8.5" stroke="#0B1220" strokeWidth="1" opacity="0.22" />
              <circle cx="10" cy="10" r="3.2" fill="#3730A3" />
              <circle cx="10" cy="10" r="1" fill="#FBFDFF" />
            </svg>
            <span className="font-display text-[15px] font-medium tracking-tight text-ink-900">ARGUS</span>
          </div>
          <nav className="hidden items-center gap-6 text-[13px] text-ink-600 md:flex">
            {["Progress", "Intelligence", "Evidence", "Market", "Sources"].map((label) => (
              <span className="cursor-default transition-colors hover:text-ink-900" key={label}>{label}</span>
            ))}
          </nav>
        </div>
        <div className="flex items-center gap-4">
          <span className="hidden items-center gap-2 text-[12px] text-ink-500 sm:inline-flex">
            <span className={`h-1.5 w-1.5 rounded-full ${status === "complete" ? "bg-emerald-500" : status === "running" ? "bg-indigo-500" : "bg-ink-300"}`} />
            {status || "ready"}
          </span>
          <ModeBadge mode={mode} cacheHit={cacheHit} />
        </div>
      </div>
    </header>
  );
}
