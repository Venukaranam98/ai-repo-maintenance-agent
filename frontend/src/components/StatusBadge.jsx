export default function StatusBadge({ status }) {
  const map = {
    passed: "badge-passed",
    failed: "badge-failed",
    error: "badge-failed",
    pending: "badge-pending",
    no_gaps: "badge-pending",
  };
  const cls = map[status] || "badge-pending";
  return <span className={cls}>{status}</span>;
}
