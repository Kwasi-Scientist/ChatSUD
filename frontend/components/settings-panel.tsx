"use client";

export function SettingsPanel({
  open,
  region,
  privacyMode,
  onClose,
  onRegionChange,
  onPrivacyChange
}: {
  open: boolean;
  region: string;
  privacyMode: boolean;
  onClose: () => void;
  onRegionChange: (value: string) => void;
  onPrivacyChange: (value: boolean) => void;
}) {
  return (
    <aside
      className={`fixed left-0 top-0 z-30 h-full w-full max-w-sm transform border-r border-[var(--border)] bg-[var(--surface)] p-5 shadow-2xl transition-transform duration-300 ${open ? "translate-x-0" : "-translate-x-full"}`}
    >
      <div className="mb-6 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-[var(--text)]">Settings</h2>
        <button
          className="rounded-lg border border-[var(--border)] px-3 py-1.5 text-sm text-[var(--muted-strong)] transition hover:bg-[var(--surface-soft)]"
          onClick={onClose}
        >
          Close
        </button>
      </div>
      <div className="space-y-6">
        <div>
          <label className="mb-2 block text-sm font-medium text-[var(--muted-strong)]">Region</label>
          <select
            className="w-full rounded-lg border border-[var(--border)] bg-[var(--surface-raised)] px-3 py-2.5 text-sm outline-none transition focus:border-[var(--muted)]"
            value={region}
            onChange={(event) => onRegionChange(event.target.value)}
          >
            <option value="US">United States</option>
            <option value="UK">United Kingdom</option>
            <option value="EU">Europe</option>
            <option value="GLOBAL">Global</option>
          </select>
        </div>
        <div className="rounded-xl border border-[var(--border)] bg-[var(--surface-raised)] p-4">
          <div className="mb-2 flex items-center justify-between">
            <span className="font-medium text-[var(--text)]">Privacy Mode</span>
            <input
              checked={privacyMode}
              type="checkbox"
              className="h-4 w-4 accent-[var(--accent)]"
              onChange={(event) => onPrivacyChange(event.target.checked)}
            />
          </div>
          <p className="text-sm text-[var(--muted)]">
            When enabled, the backend avoids storing chat turns between requests.
          </p>
        </div>
      </div>
    </aside>
  );
}
