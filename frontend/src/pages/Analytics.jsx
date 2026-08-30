import { useEffect, useState } from "react";
import AppLayout from "../components/AppLayout";
import api from "../services/api";
import { useCompany } from "../context/CompanyContext";

const METRIC_LABELS = {
  profit_margin_pct: "Profit Margin",
  revenue_growth_pct: "Revenue Growth",
  cash_ratio: "Cash Ratio",
  operating_margin_pct: "Operating Margin",
  inventory_turnover: "Inventory Turnover",
};

function PercentileBar({ percentile }) {
  const color = percentile >= 60 ? "bg-emerald-500" : percentile >= 35 ? "bg-amber-500" : "bg-red-500";
  return (
    <div className="h-2 w-full rounded-full bg-cream-100">
      <div className={`h-2 rounded-full ${color}`} style={{ width: `${Math.max(4, percentile)}%` }} />
    </div>
  );
}

export default function Analytics() {
  const { selectedCompanyId } = useCompany();
  const [rows, setRows] = useState([]);
  const [benchmark, setBenchmark] = useState(null);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!selectedCompanyId) return;
    api.get(`/analyze/${selectedCompanyId}/financial-data`).then((r) => setRows(r.data));
    api
      .get(`/dashboard/${selectedCompanyId}/benchmark`)
      .then((r) => setBenchmark(r.data))
      .catch((err) => setError(err.response?.data?.detail || "Benchmark unavailable — run analysis first."));
  }, [selectedCompanyId]);

  if (!selectedCompanyId) {
    return (
      <AppLayout>
        <p className="text-ink-500">Select or create a company first from the top bar.</p>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <h1 className="mb-6 text-2xl font-semibold text-ink-900">Analytics</h1>

      <div className="card mb-6">
        <h2 className="mb-3 font-semibold text-ink-900">Industry Benchmarking</h2>
        {error && !benchmark && <p className="text-sm text-ink-400">{error}</p>}
        {benchmark && (
          <div className="space-y-4">
            {Object.entries(benchmark.metrics).map(([key, m]) => (
              <div key={key}>
                <div className="mb-1 flex justify-between text-sm">
                  <span className="text-ink-700">{METRIC_LABELS[key] || key}</span>
                  <span className="text-ink-500">
                    You: {m.company_value} · Industry avg: {m.industry_average} · Percentile: {m.percentile}%
                  </span>
                </div>
                <PercentileBar percentile={m.percentile} />
              </div>
            ))}
          </div>
        )}
      </div>

      <div className="card overflow-x-auto">
        <h2 className="mb-3 font-semibold text-ink-900">Monthly Financial Data</h2>
        <table className="w-full min-w-[900px] text-left text-sm">
          <thead>
            <tr className="border-b border-ink-100 text-ink-500">
              <th className="py-2 pr-4">Period</th>
              <th className="py-2 pr-4">Revenue</th>
              <th className="py-2 pr-4">Net Profit</th>
              <th className="py-2 pr-4">Profit Margin %</th>
              <th className="py-2 pr-4">Revenue Growth %</th>
              <th className="py-2 pr-4">Cash Ratio</th>
              <th className="py-2 pr-4">Current Ratio</th>
              <th className="py-2 pr-4">Debt Ratio</th>
              <th className="py-2 pr-4">Inventory Turnover</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} className="border-b border-ink-200 text-ink-700">
                <td className="py-2 pr-4">{r.period}</td>
                <td className="py-2 pr-4">{r.revenue.toLocaleString()}</td>
                <td className="py-2 pr-4">{r.net_profit.toLocaleString()}</td>
                <td className="py-2 pr-4">{r.profit_margin_pct?.toFixed(1) ?? "—"}</td>
                <td className="py-2 pr-4">{r.revenue_growth_pct?.toFixed(1) ?? "—"}</td>
                <td className="py-2 pr-4">{r.cash_ratio?.toFixed(2) ?? "—"}</td>
                <td className="py-2 pr-4">{r.current_ratio?.toFixed(2) ?? "—"}</td>
                <td className="py-2 pr-4">{r.debt_ratio?.toFixed(2) ?? "—"}</td>
                <td className="py-2 pr-4">{r.inventory_turnover?.toFixed(2) ?? "—"}</td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td colSpan={9} className="py-4 text-center text-ink-400">No data yet — upload and process files first.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </AppLayout>
  );
}
