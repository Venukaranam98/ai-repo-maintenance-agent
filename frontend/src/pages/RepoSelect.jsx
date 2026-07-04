import { useEffect, useState } from "react";
import Navbar from "../components/Navbar.jsx";
import { api } from "../api/client.js";

export default function RepoSelect() {
  const [repos, setRepos] = useState([]);
  const [selected, setSelected] = useState(new Set());
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.getAvailableRepos().then((data) => {
      setRepos(data);
      setLoading(false);
    });
  }, []);

  function toggle(fullName) {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(fullName) ? next.delete(fullName) : next.add(fullName);
      return next;
    });
  }

  async function handleSave() {
    setSaving(true);
    await api.selectRepos(Array.from(selected));
    setSaving(false);
  }

  return (
    <div className="min-h-screen bg-canvas-soft">
      <Navbar />
      <main className="max-w-3xl mx-auto px-6 py-10">
        <h1 className="text-[24px] font-semibold tracking-tight mb-1">Select repositories</h1>
        <p className="text-sm text-body mb-6">
          Only your public repositories are shown. The agent will only open pull requests — nothing is pushed directly to your default branch.
        </p>

        {loading ? (
          <p className="text-sm text-mute">Loading your repositories…</p>
        ) : (
          <div className="card divide-y divide-hairline p-0">
            {repos.map((r) => (
              <label key={r.full_name} className="flex items-center gap-3 px-4 py-3 cursor-pointer hover:bg-canvas-soft transition">
                <input
                  type="checkbox"
                  checked={selected.has(r.full_name)}
                  onChange={() => toggle(r.full_name)}
                  className="w-4 h-4"
                />
                <div>
                  <p className="text-sm font-mono">{r.full_name}</p>
                  {r.description && <p className="text-xs text-mute">{r.description}</p>}
                </div>
              </label>
            ))}
          </div>
        )}

        <button onClick={handleSave} disabled={saving || selected.size === 0} className="btn-primary mt-6 disabled:opacity-50">
          {saving ? "Saving…" : `Enable agent on ${selected.size || ""} repo(s)`}
        </button>
      </main>
    </div>
  );
}
