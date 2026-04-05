"use client";

import { RetrievedSource } from "../lib/types";

export function SourceDrawer({
  open,
  sources,
  onClose
}: {
  open: boolean;
  sources: RetrievedSource[];
  onClose: () => void;
}) {
  return (
    <aside
      className={`fixed right-0 top-0 z-30 h-full w-full max-w-md transform border-l border-[var(--border)] bg-[var(--panel-strong)] p-6 shadow-2xl transition-transform duration-300 ${open ? "translate-x-0" : "translate-x-full"}`}
    >
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Retrieved Sources</h2>
        <button className="rounded-full border px-3 py-1 text-sm" onClick={onClose}>
          Close
        </button>
      </div>
      <div className="space-y-4 overflow-y-auto pb-10">
        {sources.map((source) => (
          <article key={`${source.source}-${source.score}`} className="rounded-2xl border border-[var(--border)] bg-white/80 p-4">
            <div className="mb-2 flex items-center justify-between gap-3">
              <h3 className="text-sm font-semibold">{source.title}</h3>
              <span className="text-xs text-[var(--muted)]">{source.score.toFixed(2)}</span>
            </div>
            <p className="text-sm text-[var(--muted)]">{source.snippet}</p>
            <div className="mt-3 flex flex-wrap gap-2">
              {source.tags.map((tag) => (
                <span key={tag} className="rounded-full bg-[var(--accent-soft)] px-2 py-1 text-xs">
                  {tag}
                </span>
              ))}
            </div>
          </article>
        ))}
      </div>
    </aside>
  );
}

