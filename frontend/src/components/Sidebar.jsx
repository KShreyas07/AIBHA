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
    <aside className="hidden w-64 shrink-0 flex-col border-r border-ink-100 bg-cream-50 p-4 md:flex">
      <div className="mb-8 flex items-center gap-2 px-2">
        <p className="font-display text-lg font-semibold text-ink-900 leading-tight">AIBHA</p>
      </div>
      <nav className="flex flex-1 flex-col gap-1">
        {NAV_ITEMS.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) =>
              `flex items-center gap-3 rounded-full px-3 py-2 text-sm font-medium transition ${
                isActive
                  ? "bg-ink-900 text-cream-50"
                  : "text-ink-500 hover:bg-cream-200 hover:text-ink-900"
              }`
            }
          >
            <span>{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </nav>
      <p className="px-2 text-xs text-ink-300">v1.0.0 · SME Edition</p>
    </aside>
  );
}
