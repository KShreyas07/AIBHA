import { useState } from "react";
import { Line } from "react-chartjs-2";
import AppLayout from "../components/AppLayout";
import api from "../services/api";
import { useCompany } from "../context/CompanyContext";
import { CHART_COLORS, baseLineOptions } from "../chartSetup";

const METRICS = [
  { value: "revenue", label: "Revenue" },
  { value: "profit", label: "Profit" },
  { value: "expenses", label: "Expenses" },
  { value: "cash_flow", label: "Cash Flow" },
];

export default function Forecast() {
  const { selectedCompanyId } = useCompany();
  const [metric, setMetric] = useState("revenue");
  const [horizon, setHorizon] = useState(6);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const runForecast = async () => {
    if (!selectedCompanyId) return;
    setLoading(true);
    setError("");
    try {
      const { data } = await api.post(`/forecast/${selectedCompanyId}`, null, {
        params: { metric, horizon_months: horizon },
      });
      setResult(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Forecast failed — you need at least 3 months of processed data.");
    } finally {
      setLoading(false);
    }
  };

  const chartData = result && {
    labels: result.points.map((p) => p.period.slice(0, 7)),
    datasets: [
      {
        label: METRICS.find((m) => m.value === metric)?.label,
        data: result.points.map((p) => p.predicted_value),
        borderColor: CHART_COLORS.brand,
        backgroundColor: `${CHART_COLORS.brand}33`,
        fill: true,
        tension: 0.35,
      },
      {
        label: "Upper Bound",
        data: result.points.map((p) => p.upper_bound),
        borderColor: `${CHART_COLORS.slate}80`,
        borderDash: [4, 4],
        pointRadius: 0,
      },
      {
        label: "Lower Bound",
        data: result.points.map((p) => p.lower_bound),
        borderColor: `${CHART_COLORS.slate}80`,
        borderDash: [4, 4],
        pointRadius: 0,
      },
    ],
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
      <h1 className="mb-6 text-2xl font-semibold text-ink-900">Forecast</h1>

      <div className="card mb-6 flex flex-wrap items-end gap-4">
        <div>
          <label className="label">Metric</label>
          <select className="input" value={metric} onChange={(e) => setMetric(e.target.value)}>
            {METRICS.map((m) => (
              <option key={m.value} value={m.value}>{m.label}</option>
            ))}
          </select>
        </div>
        <div>
          <label className="label">Horizon</label>
          <select className="input" value={horizon} onChange={(e) => setHorizon(Number(e.target.value))}>
            <option value={6}>6 Months</option>
            <option value={12}>12 Months</option>
          </select>
        </div>
        <button className="btn-primary" onClick={runForecast} disabled={loading}>
          {loading ? "Forecasting…" : "Generate Forecast"}
        </button>
        {result && <span className="text-xs text-ink-400">Model: {result.model_used}</span>}
      </div>

      {error && <p className="mb-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>}

      {result && (
        <div className="card">
          <div className="h-96">
            <Line data={chartData} options={baseLineOptions} />
          </div>
        </div>
      )}
    </AppLayout>
  );
}
