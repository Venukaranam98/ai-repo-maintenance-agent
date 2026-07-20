import { useEffect, useState } from "react";
import Navbar from "../components/Navbar.jsx";
import RunHistoryTable from "../components/RunHistoryTable.jsx";
import { api } from "../api/client.js";

export default function Dashboard() {
  const [repos, setRepos] = useState([]);
  const [runs, setRuns] = useState([]);
  const [triggering, setTriggering] = useState(null);

  async function refresh() {
    const [repoData, historyData] = await Promise.all([api.getMonitoredRepos(), api.getHistory()]);
    setRepos(repoData);
    setRuns(historyData);
  }

  useEffect(() => {
    refresh();
  }, []);

  async function handleTrigger(repoId) {
    setTriggering(repoId);
    await api.triggerScan(repoId);
    setTriggering(null);
    setTimeout(refresh, 3000);
  }

  return (
    <div className="min-h-screen bg-canvas-soft">
      <Navbar />
      <main className="max-w-6xl mx-auto px-6 py-10 space-y-10">
        <div>
          <h1 className="text-[24px] font-semibold tracking-tight mb-1">Dashboard</h1>
          <p className="text-sm text-body">Monitored repositories and recent agent activity.</p>
        </div>

        <section>
          <h2 className="text-[16px] font-medium mb-3">Monitored repositories</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {repos.map((r) => (
              <div key={r.id} className="card flex flex-col justify-between">
                <p className="font-mono text-sm mb-4">{r.full_name}</p>
                <button
                  onClick={() => handleTrigger(r.id)}
                  disabled={triggering === r.id}
                  className="btn-secondary text-xs self-start disabled:opacity-50"
                >
                  {triggering === r.id ? "Scanning…" : "Scan now"}
                </button>
              </div>
            ))}
            {repos.length === 0 && <p className="text-sm text-mute">No repos enabled yet — go to Repositories to add some.</p>}
          </div>
        </section>

        <section>
          <h2 className="text-[16px] font-medium mb-3">Run history</h2>
          <RunHistoryTable runs={runs} />
        </section>
      </main>
    </div>
  );
}
