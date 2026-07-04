import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import Navbar from "../components/Navbar.jsx";
import { api } from "../api/client.js";

export default function RepoDetail() {
  const { repoName } = useParams(); // e.g. "owner__repo" from the route
  const [runs, setRuns] = useState([]);

  useEffect(() => {
    api.getHistory().then((all) => {
      const decoded = repoName.replace("__", "/");
      setRuns(all.filter((r) => r.repo === decoded));
    });
  }, [repoName]);

  const trendData = runs
    .slice()
    .reverse()
    .map((r) => ({
      date: new Date(r.started_at).toLocaleDateString(),
      gaps: r.gap_summary?.gap_count ?? 0,
    }));

  return (
    <div className="min-h-screen bg-canvas-soft">
      <Navbar />
      <main className="max-w-4xl mx-auto px-6 py-10 space-y-8">
        <h1 className="text-[24px] font-semibold tracking-tight font-mono">{repoName.replace("__", "/")}</h1>

        <div className="card">
          <h2 className="text-[16px] font-medium mb-4">Gap count over time</h2>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={trendData}>
                <CartesianGrid stroke="#ebebeb" />
                <XAxis dataKey="date" tick={{ fontSize: 12, fill: "#888888" }} />
                <YAxis tick={{ fontSize: 12, fill: "#888888" }} allowDecimals={false} />
                <Tooltip />
                <Line type="monotone" dataKey="gaps" stroke="#0070f3" strokeWidth={2} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card">
          <h2 className="text-[16px] font-medium mb-4">Latest health report</h2>
          {runs[0]?.gap_summary ? (
            <ul className="space-y-2 text-sm">
              {runs[0].gap_summary.gaps.map((g, i) => (
                <li key={i} className="flex justify-between border-b border-hairline pb-2">
                  <span className="font-mono text-xs text-body">{g.file_path}</span>
                  <span className="text-mute text-xs">{g.category}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-mute">No health report yet.</p>
          )}
        </div>
      </main>
    </div>
  );
}
