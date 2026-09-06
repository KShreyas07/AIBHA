import { useCallback, useEffect, useState } from "react";
import AppLayout from "../components/AppLayout";
import api from "../services/api";
import { useCompany } from "../context/CompanyContext";

const METRICS = [
  { value: "revenue", label: "Revenue" },
  { value: "profit", label: "Profit" },
  { value: "expenses", label: "Expenses" },
  { value: "cash_flow", label: "Cash Balance" },
];

const METRIC_LABEL = Object.fromEntries(METRICS.map((m) => [m.value, m.label]));

const money = (v) => (v == null ? "—" : `$${Number(v).toLocaleString(undefined, { maximumFractionDigits: 0 })}`);

function statusBadge(goal) {
  if (goal.achieved) return { text: "Achieved", className: "bg-emerald-50 text-emerald-700" };
  if (goal.on_track === true) return { text: "On Track", className: "bg-emerald-50 text-emerald-700" };
  if (goal.on_track === false) return { text: "Off Track", className: "bg-red-50 text-red-700" };
  return { text: "Not enough data to project", className: "bg-cream-100 text-ink-500" };
}

function ProgressBar({ pct, achieved, onTrack }) {
  const color = achieved || onTrack ? "bg-emerald-500" : onTrack === false ? "bg-red-500" : "bg-amber-500";
  return (
    <div className="h-2 w-full rounded-full bg-cream-100">
      <div className={`h-2 rounded-full ${color}`} style={{ width: `${Math.max(4, pct)}%` }} />
    </div>
  );
}

export default function Goals() {
  const { selectedCompanyId } = useCompany();
  const [goals, setGoals] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [creating, setCreating] = useState(false);
  const [form, setForm] = useState({ label: "", metric: "revenue", target_value: "", target_date: "" });

  const fetchGoals = useCallback(async () => {
    if (!selectedCompanyId) return;
    setLoading(true);
    try {
      const { data } = await api.get(`/goals/${selectedCompanyId}`);
      setGoals(data);
    } finally {
      setLoading(false);
    }
  }, [selectedCompanyId]);

  useEffect(() => {
    fetchGoals();
  }, [fetchGoals]);

  const createGoal = async (e) => {
    e.preventDefault();
    if (!selectedCompanyId || !form.label || !form.target_value || !form.target_date) return;
    setCreating(true);
    setError("");
    try {
      await api.post(`/goals/${selectedCompanyId}`, {
        label: form.label,
        metric: form.metric,
        target_value: Number(form.target_value),
        target_date: form.target_date,
      });
      setForm({ label: "", metric: "revenue", target_value: "", target_date: "" });
      await fetchGoals();
    } catch (err) {
      setError(err.response?.data?.detail || "Could not create goal — process financial data for this company first.");
    } finally {
      setCreating(false);
    }
  };

  const removeGoal = async (goalId) => {
    await api.delete(`/goals/${selectedCompanyId}/${goalId}`);
    setGoals((prev) => prev.filter((g) => g.id !== goalId));
  };

  if (!selectedCompanyId) {
    return (
      <AppLayout>
        <p className="text-ink-500">Select or create a company first from the top bar.</p>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <h1 className="mb-6 text-2xl font-semibold text-ink-900">Goal Tracking</h1>

      <form className="card mb-6 flex flex-wrap items-end gap-4" onSubmit={createGoal}>
        <div className="min-w-[200px] flex-1">
          <label className="label">Goal</label>
          <input
            className="input"
            placeholder="e.g. Reach $10k monthly revenue"
            value={form.label}
            onChange={(e) => setForm({ ...form, label: e.target.value })}
          />
        </div>
        <div>
          <label className="label">Metric</label>
          <select className="input" value={form.metric} onChange={(e) => setForm({ ...form, metric: e.target.value })}>
            {METRICS.map((m) => (
              <option key={m.value} value={m.value}>{m.label}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="label">Target Value ($)</label>
          <input
            type="number"
            className="input"
            value={form.target_value}
            onChange={(e) => setForm({ ...form, target_value: e.target.value })}
          />
        </div>
        <div>
          <label className="label">Target Date</label>
          <input
            type="date"
            className="input"
            value={form.target_date}
            onChange={(e) => setForm({ ...form, target_date: e.target.value })}
          />
        </div>
        <button className="btn-primary" type="submit" disabled={creating}>
          {creating ? "Adding…" : "Add Goal"}
        </button>
      </form>

      {error && <p className="mb-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>}
      {!loading && goals.length === 0 && (
        <p className="text-ink-500">No goals yet — set one above to start tracking progress.</p>
      )}

      <div className="space-y-4">
        {goals.map((g) => {
          const badge = statusBadge(g);
          return (
            <div key={g.id} className="card">
              <div className="mb-2 flex items-start justify-between gap-3">
                <div>
                  <p className="font-medium text-ink-900">{g.label}</p>
                  <p className="text-xs text-ink-400">
                    {METRIC_LABEL[g.metric]} · Target {money(g.target_value)} by {g.target_date}
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ${badge.className}`}>
                    {badge.text}
                  </span>
                  <button className="text-xs text-ink-400 hover:text-red-600" onClick={() => removeGoal(g.id)}>
                    Remove
                  </button>
                </div>
              </div>
              <ProgressBar pct={g.progress_pct} achieved={g.achieved} onTrack={g.on_track} />
              <div className="mt-2 flex justify-between text-xs text-ink-500">
                <span>Started at {money(g.baseline_value)}</span>
                <span>Now: {money(g.current_value)}</span>
                {g.projected_value != null && <span>Projected by target date: {money(g.projected_value)}</span>}
                <span>{g.progress_pct}%</span>
              </div>
            </div>
          );
        })}
      </div>
    </AppLayout>
  );
}
