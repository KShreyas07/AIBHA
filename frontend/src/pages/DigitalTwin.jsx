import { useCallback, useEffect, useRef, useState } from "react";
import { Radar } from "react-chartjs-2";
import AppLayout from "../components/AppLayout";
import api from "../services/api";
import { useCompany } from "../context/CompanyContext";
import { dnaTwinRadarDataset, twinRadarOptions } from "../chartSetup";

const money = (v) =>
  v == null ? "—" : `${v < 0 ? "−" : ""}$${Math.abs(v).toLocaleString(undefined, { maximumFractionDigits: 0 })}`;

const HEALTH_COLOR = { Excellent: "text-emerald-600", Good: "text-emerald-600", Average: "text-amber-600", Poor: "text-amber-600", Critical: "text-red-600" };

function Lever({ label, value, onChange, min, max, step = 1, suffix = "%" }) {
  return (
    <div>
      <div className="mb-1 flex items-center justify-between">
        <label className="label mb-0">{label}</label>
        <span className="text-sm font-medium text-ink-900">
          {value > 0 ? "+" : ""}
          {value}
          {suffix}
        </span>
      </div>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-full"
        style={{ accentColor: "#C2410C" }}
      />
    </div>
  );
}

function runwayText(months) {
  if (months == null) return "Stable / growing";
  return `${months} month${months === 1 ? "" : "s"}`;
}

export default function DigitalTwin() {
  const { selectedCompanyId } = useCompany();
  const [levers, setLevers] = useState({ revenue_change_pct: 0, expenses_change_pct: 0, debt_change_pct: 0, cash_injection: 0 });
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const debounceRef = useRef(null);

  const runSimulation = useCallback(async (nextLevers) => {
    if (!selectedCompanyId) return;
    setLoading(true);
    setError("");
    try {
      const { data } = await api.post(`/simulate/${selectedCompanyId}`, nextLevers);
      setResult(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Could not run simulation — process financial data for this company first.");
      setResult(null);
    } finally {
      setLoading(false);
    }
  }, [selectedCompanyId]);

  useEffect(() => {
    runSimulation(levers);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedCompanyId]);

  const updateLever = (key, value) => {
    const next = { ...levers, [key]: value };
    setLevers(next);
    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => runSimulation(next), 300);
  };

  const reset = () => {
    const next = { revenue_change_pct: 0, expenses_change_pct: 0, debt_change_pct: 0, cash_injection: 0 };
    setLevers(next);
    clearTimeout(debounceRef.current);
    runSimulation(next);
  };

  if (!selectedCompanyId) {
    return (
      <AppLayout>
        <p className="text-ink-500">Select or create a company first from the top bar.</p>
      </AppLayout>
    );
  }

  const scoreDelta = result ? Math.round((result.simulated.health_score - result.baseline.health_score) * 100) / 100 : 0;

  return (
    <AppLayout>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-ink-900">Digital Twin</h1>
          <p className="text-sm text-ink-500">
            Drag the levers to see how a hypothetical change would move your health score — nothing here is saved.
          </p>
        </div>
        <button className="btn-secondary" onClick={reset}>Reset</button>
      </div>

      {error && <p className="mb-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>}

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div className="card space-y-6">
          <Lever
            label="Revenue Change"
            value={levers.revenue_change_pct}
            onChange={(v) => updateLever("revenue_change_pct", v)}
            min={-50}
            max={100}
          />
          <Lever
            label="Expense Change"
            value={levers.expenses_change_pct}
            onChange={(v) => updateLever("expenses_change_pct", v)}
            min={-50}
            max={100}
          />
          <Lever
            label="Debt Change"
            value={levers.debt_change_pct}
            onChange={(v) => updateLever("debt_change_pct", v)}
            min={-100}
            max={100}
          />
          <Lever
            label="One-Time Cash Injection"
            value={levers.cash_injection}
            onChange={(v) => updateLever("cash_injection", v)}
            min={-20000}
            max={20000}
            step={500}
            suffix="$"
          />
        </div>

        <div className="card">
          <p className="mb-3 text-sm font-medium text-ink-700">Business DNA — Current vs. What-If</p>
          {result ? (
            <div className="mx-auto h-72 max-w-sm">
              <Radar data={dnaTwinRadarDataset(result.baseline.health_breakdown, result.simulated.health_breakdown)} options={twinRadarOptions} />
            </div>
          ) : (
            <p className="py-16 text-center text-sm text-ink-500">{loading ? "Simulating…" : "No data yet."}</p>
          )}
        </div>
      </div>

      {result && (
        <div className="mt-6 grid grid-cols-1 gap-6 md:grid-cols-2">
          <div className="card">
            <p className="mb-3 text-sm font-medium text-ink-700">Health Score</p>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs uppercase tracking-wide text-ink-500">Current</p>
                <p className={`text-3xl font-semibold ${HEALTH_COLOR[result.baseline.health_label] || "text-ink-900"}`}>
                  {result.baseline.health_score}
                </p>
                <p className="text-xs text-ink-400">{result.baseline.health_label}</p>
              </div>
              <span className="text-2xl text-ink-300">→</span>
              <div>
                <p className="text-xs uppercase tracking-wide text-ink-500">What-If</p>
                <p className={`text-3xl font-semibold ${HEALTH_COLOR[result.simulated.health_label] || "text-ink-900"}`}>
                  {result.simulated.health_score}
                </p>
                <p className="text-xs text-ink-400">{result.simulated.health_label}</p>
              </div>
              <span className={`rounded-full px-3 py-1 text-xs font-semibold ${scoreDelta >= 0 ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-700"}`}>
                {scoreDelta >= 0 ? "+" : ""}
                {scoreDelta}
              </span>
            </div>
          </div>

          <div className="card">
            <p className="mb-3 text-sm font-medium text-ink-700">Cash Runway</p>
            <div className="flex items-center justify-between">
              <div>
                <p className="text-xs uppercase tracking-wide text-ink-500">Current</p>
                <p className="text-2xl font-semibold text-ink-900">{runwayText(result.baseline.runway_months)}</p>
                <p className="text-xs text-ink-400">Burn {money(result.baseline.avg_monthly_burn)}/mo</p>
              </div>
              <span className="text-2xl text-ink-300">→</span>
              <div>
                <p className="text-xs uppercase tracking-wide text-ink-500">What-If</p>
                <p className="text-2xl font-semibold text-ink-900">{runwayText(result.simulated.runway_months)}</p>
                <p className="text-xs text-ink-400">Burn {money(result.simulated.avg_monthly_burn)}/mo</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </AppLayout>
  );
}
