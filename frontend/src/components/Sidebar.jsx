import { NavLink } from "react-router-dom";

const NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard", icon: "📊" },
  { to: "/companies", label: "Companies", icon: "🏢" },
  { to: "/upload", label: "Upload Data", icon: "📤" },
  { to: "/analytics", label: "Analytics", icon: "📈" },
  { to: "/forecast", label: "Forecast", icon: "🔮" },
  { to: "/recommendations", label: "Recommendations", icon: "💡" },
  { to: "/reports", label: "Reports", icon: "📄" },
  { to: "/settings", label: "Settings", icon: "⚙️" },
];

export default function Sidebar() {
  return (
    <aside className="hidden w-64 shrink-0 flex-col border-r border-slate-800 bg-slate-950/80 p-4 md:flex">
      <div className="mb-8 flex items-center gap-2 px-2">
        <span className="text-2xl">🧠</span>
        <div>
          <p className="text-sm font-semibold text-white leading-tight">AI Business</p>
          <p className="text-xs text-slate-400 leading-tight">Health Analyzer</p>
        </div>
      </div>
      <nav className="flex flex-1 flex-col gap-1">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition ${
                isActive
                  ? "bg-brand-600/20 text-brand-400"
                  : "text-slate-400 hover:bg-slate-900 hover:text-slate-100"
              }`
            }
          >
            <span>{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </nav>
      <p className="px-2 text-xs text-slate-600">v1.0.0 · SME Edition</p>
    </aside>
  );
}
