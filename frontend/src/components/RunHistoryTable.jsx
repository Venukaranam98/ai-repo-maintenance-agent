import StatusBadge from "./StatusBadge.jsx";

export default function RunHistoryTable({ runs }) {
  if (!runs.length) {
    return <p className="text-sm text-mute">No agent runs yet. Trigger a scan to see activity here.</p>;
  }

  return (
    <div className="card p-0 overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-canvas-soft text-mute text-xs uppercase tracking-wide">
          <tr>
            <th className="text-left px-4 py-3 font-medium">Repository</th>
            <th className="text-left px-4 py-3 font-medium">Started</th>
            <th className="text-left px-4 py-3 font-medium">Status</th>
            <th className="text-left px-4 py-3 font-medium">Commit</th>
            <th className="text-left px-4 py-3 font-medium">PR</th>
          </tr>
        </thead>
        <tbody>
          {runs.map((run) => (
            <tr key={run.id} className="border-t border-hairline">
              <td className="px-4 py-3 font-mono text-xs">{run.repo}</td>
              <td className="px-4 py-3 text-body">{new Date(run.started_at).toLocaleString()}</td>
              <td className="px-4 py-3"><StatusBadge status={run.status} /></td>
              <td className="px-4 py-3 text-body max-w-xs truncate">{run.commit_message || "—"}</td>
              <td className="px-4 py-3">
                {run.pr_url ? (
                  <a href={run.pr_url} target="_blank" rel="noreferrer" className="text-link hover:underline">
                    View PR
                  </a>
                ) : (
                  "—"
                )}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
