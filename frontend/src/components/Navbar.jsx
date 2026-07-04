import { Link } from "react-router-dom";

export default function Navbar() {
  return (
    <header className="border-b border-hairline bg-white">
      <div className="max-w-6xl mx-auto px-6 h-14 flex items-center justify-between">
        <Link to="/dashboard" className="font-semibold text-[15px] tracking-tight">
          repo-agent
        </Link>
        <nav className="flex items-center gap-6 text-sm text-body">
          <Link to="/dashboard" className="hover:text-ink transition">Dashboard</Link>
          <Link to="/repos" className="hover:text-ink transition">Repositories</Link>
        </nav>
      </div>
    </header>
  );
}
