import { useAuth } from "../context/AuthContext";
import { useCompany } from "../context/CompanyContext";
import { useNavigate } from "react-router-dom";

export default function Topbar() {
  const { user, logout } = useAuth();
  const { companies, selectedCompanyId, selectCompany } = useCompany();
  const navigate = useNavigate();

  return (
    <header className="flex items-center justify-between border-b border-slate-800 bg-slate-950/80 px-6 py-3">
      <div className="flex items-center gap-3">
        <select
          className="input max-w-xs"
          value={selectedCompanyId || ""}
          onChange={(e) => selectCompany(e.target.value)}
        >
          {companies.length === 0 && <option value="">No companies yet</option>}
          {companies.map((c) => (
            <option key={c.id} value={c.id}>
              {c.name}
            </option>
          ))}
        </select>
        <button className="btn-secondary text-xs" onClick={() => navigate("/companies")}>
          + Manage Companies
        </button>
      </div>
      <div className="flex items-center gap-4">
        <span className="text-sm text-slate-400">{user?.full_name}</span>
        <button className="btn-secondary text-xs" onClick={logout}>
          Logout
        </button>
      </div>
    </header>
  );
}
