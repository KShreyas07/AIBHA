import { useCallback, useEffect, useState } from "react";
import { Line, Pie } from "react-chartjs-2";
import AppLayout from "../components/AppLayout";
import StatCard from "../components/StatCard";
import HealthGauge from "../components/HealthGauge";
import api from "../services/api";
import { useCompany } from "../context/CompanyContext";
import { CHART_COLORS, baseLineOptions, basePieOptions } from "../chartSetup";

const money = (v) => (v == null ? "—" : `$${Number(v).toLocaleString(undefined, { maximumFractionDigits: 0 })}`);

const RISK_COLOR = { Healthy: "text-emerald-400", Warning: "text-amber-400", Critical: "text-red-400" };

function trendDataset(points, label, color) {
  return {
    labels: points.map((p) => p.period.slice(0, 7)),
    datasets: [
      {
        label,
        data: points.map((p) => p.value),
        borderColor: color,
        backgroundColor: `${color}33`,
        fill: true,
        tension: 0.35,
      },
    ],
  };
}

function pieDataset(obj) {
  return {
    labels: Object.keys(obj),
    datasets: [
      {
        data: Object.values(obj),
        backgroundColor: [CHART_COLORS.brand, CHART_COLORS.green, CHART_COLORS.amber, CHART_COLORS.red],
        borderWidth: 0,
      },
    ],
  };
}

export default function Dashboard() {
  const { selectedCompanyId, selectedCompany } = useCompany();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");

  const fetchDashboard = useCallback(async () => {
    if (!selectedCompanyId) return;
    setLoading(true);
    try {
      const { data } = await api.get(`/dashboard/${selectedCompanyId}`);
      setData(data);
    } finally {
      setLoading(false);
    }
  }, [selectedCompanyId]);

  useEffect(() => {
    fetchDashboard();
  }, [fetchDashboard]);

  const runAnalysis = async () => {
    if (!selectedCompanyId) return;
    setRunning(true);
    setError("");
    try {
      await api.post(`/analyze/${selectedCompanyId}`);
      await api.post(`/predict/${selectedCompanyId}`);
      await api.post(`/recommendations/${selectedCompanyId}`);
      await fetchDashboard();
    } catch (err) {
      setError(err.response?.data?.detail || "Analysis failed — make sure you have uploaded and processed data.");
    } finally {
      setRunning(false);
    }
  };

  if (!selectedCompanyId) {
    return (
      <AppLayout>
        <p className="text-slate-400">Select or create a company first from the top bar.</p>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-white">{selectedCompany?.name || "Dashboard"}</h1>
          <p className="text-sm text-slate-400">{selectedCompany?.industry}</p>
        </div>
        <button className="btn-primary" onClick={runAnalysis} disabled={running}>
          {running ? "Analyzing…" : "Run Full Analysis"}
        </button>
      </div>

      {error && <p className="mb-4 rounded-lg bg-red-950 px-3 py-2 text-sm text-red-400">{error}</p>}

      {!loading && data && !data.has_data && (
        <p className="text-slate-400">No processed data yet. Head to Upload Data, then come back and run analysis.</p>
      )}

      {data?.has_data && (
        <>
          <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
            <StatCard label="Revenue" value={money(data.cards.revenue)} />
            <StatCard label="Profit" value={money(data.cards.profit)} accent={data.cards.profit >= 0 ? "text-emerald-400" : "text-red-400"} />
            <StatCard label="Expenses" value={money(data.cards.expenses)} />
            <StatCard label="Cash Flow" value={money(data.cards.cash_flow)} />
            <StatCard label="Health Score" value={data.cards.health_score ?? "—"} />
            <StatCard
              label="Risk Level"
              value={data.cards.risk_level ?? "—"}
              accent={RISK_COLOR[data.cards.risk_level] || "text-white"}
            />
            <StatCard label="Prediction" value={data.cards.prediction ?? "—"} />
          </div>

          <div className="mt-6 grid grid-cols-1 gap-6 lg:grid-cols-3">
            <div className="card flex flex-col items-center justify-center lg:col-span-1">
              <p className="mb-2 text-sm font-medium text-slate-300">Business Health Score</p>
              <HealthGauge score={data.health_score_gauge.score} label={data.health_score_gauge.label} />
            </div>
            <div className="card lg:col-span-2">
              <p className="mb-3 text-sm font-medium text-slate-300">Revenue Trend</p>
              <div className="h-52">
                <Line data={trendDataset(data.charts.revenue_trend, "Revenue", CHART_COLORS.brand)} options={baseLineOptions} />
              </div>
            </div>
          </div>

          <div className="mt-6 grid grid-cols-1 gap-6 md:grid-cols-2">
            <div className="card">
              <p className="mb-3 text-sm font-medium text-slate-300">Profit Trend</p>
              <div className="h-48">
                <Line data={trendDataset(data.charts.profit_trend, "Profit", CHART_COLORS.green)} options={baseLineOptions} />
              </div>
            </div>
            <div className="card">
              <p className="mb-3 text-sm font-medium text-slate-300">Expense Trend</p>
              <div className="h-48">
                <Line data={trendDataset(data.charts.expense_trend, "Expenses", CHART_COLORS.amber)} options={baseLineOptions} />
              </div>
            </div>
            <div className="card">
              <p className="mb-3 text-sm font-medium text-slate-300">Cash Flow Trend</p>
              <div className="h-48">
                <Line data={trendDataset(data.charts.cash_flow_trend, "Cash Balance", CHART_COLORS.slate)} options={baseLineOptions} />
              </div>
            </div>
            <div className="card">
              <p className="mb-3 text-sm font-medium text-slate-300">Expense Breakdown</p>
              <div className="h-48">
                <Pie data={pieDataset(data.pie_charts.expenses)} options={basePieOptions} />
              </div>
            </div>
          </div>

          <div className="mt-6 grid grid-cols-1 gap-6 md:grid-cols-2">
            <div className="card">
              <p className="mb-3 text-sm font-medium text-slate-300">Revenue Composition</p>
              <div className="h-48">
                <Pie data={pieDataset(data.pie_charts.revenue_composition)} options={basePieOptions} />
              </div>
            </div>
            <div className="card">
              <p className="mb-3 text-sm font-medium text-slate-300">Inventory</p>
              <div className="h-48">
                <Pie data={pieDataset(data.pie_charts.inventory)} options={basePieOptions} />
              </div>
            </div>
          </div>
        </>
      )}
    </AppLayout>
  );
}
