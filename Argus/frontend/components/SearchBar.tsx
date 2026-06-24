import type { ArgusMode } from "@/lib/api";

type Props = {
  query: string;
  mode: ArgusMode;
  running: boolean;
  onQueryChange: (value: string) => void;
  onModeChange: (value: ArgusMode) => void;
  onSubmit: (query: string, mode: ArgusMode) => void;
};

export function SearchBar({ query, mode, running, onQueryChange, onModeChange, onSubmit }: Props) {
  return (
    <form
      className="premium-panel flex flex-col gap-3 rounded-[28px] p-2.5 md:flex-row md:items-center"
      onSubmit={(event) => {
        event.preventDefault();
        const form = event.currentTarget;
        const formData = new FormData(form);
        onSubmit(String(formData.get("query") || query), String(formData.get("mode") || mode) as ArgusMode);
      }}
    >
      <input
        name="query"
        value={query}
        onChange={(event) => onQueryChange(event.target.value)}
        className="min-h-14 flex-1 rounded-[22px] border border-transparent bg-white/70 px-5 text-lg text-ink outline-none transition placeholder:text-slate-400 focus:border-accent/30 focus:bg-white"
        placeholder="Cardiologists in Chennai"
      />
      <select
        name="mode"
        value={mode}
        onChange={(event) => onModeChange(event.target.value as ArgusMode)}
        className="min-h-14 rounded-[20px] border border-line/70 bg-white/70 px-4 text-sm font-semibold text-ink"
      >
        <option value="auto">Auto</option>
        <option value="offline">Offline</option>
        <option value="online">Online</option>
        <option value="demo">Demo</option>
      </select>
      <button className="min-h-14 rounded-[20px] bg-accent px-7 font-semibold text-white shadow-[0_14px_30px_rgba(55,48,163,0.18)] transition hover:-translate-y-0.5 hover:bg-indigo-800 active:translate-y-0 disabled:opacity-50" disabled={running}>
        {running ? "Running" : "Run Research"}
      </button>
    </form>
  );
}
