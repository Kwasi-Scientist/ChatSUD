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
      className={`fixed left-0 top-0 z-30 h-full w-full max-w-sm transform border-r border-[var(--border)] bg-[var(--panel-strong)] p-6 shadow-2xl transition-transform duration-300 ${open ? "translate-x-0" : "-translate-x-full"}`}
    >
      <div className="mb-6 flex items-center justify-between">
        <h2 className="text-lg font-semibold">Settings</h2>
        <button className="rounded-full border px-3 py-1 text-sm" onClick={onClose}>
          Close
        </button>
      </div>
      <div className="space-y-6">
        <div>
          <label className="mb-2 block text-sm font-semibold">Region</label>
          <select
            className="w-full rounded-2xl border border-[var(--border)] bg-white px-4 py-3"
            value={region}
            onChange={(event) => onRegionChange(event.target.value)}
          >
            <option value="US">United States</option>
            <option value="UK">United Kingdom</option>
            <option value="EU">Europe</option>
            <option value="GLOBAL">Global</option>
          </select>
        </div>
        <div className="rounded-2xl border border-[var(--border)] bg-white p-4">
          <div className="mb-2 flex items-center justify-between">
            <span className="font-semibold">Privacy Mode</span>
            <input
              checked={privacyMode}
              type="checkbox"
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

