import { useCallback, useEffect, useState } from "react";
import AppLayout from "../components/AppLayout";
import api from "../services/api";
import { useCompany } from "../context/CompanyContext";

const PRIORITY_STYLES = {
  high: "border-red-800 bg-red-950/50",
  medium: "border-amber-800 bg-amber-950/40",
  low: "border-slate-800 bg-slate-900/60",
};

const CATEGORY_ICON = {
  expenses: "💸", inventory: "📦", customer: "🤝", cash: "🏦", marketing: "📣", debt: "🏛️", revenue: "📈",
};

export default function Recommendations() {
  const { selectedCompanyId } = useCompany();
  const [recs, setRecs] = useState([]);
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");

  const fetchRecs = useCallback(async () => {
    if (!selectedCompanyId) return;
    setLoading(true);
    try {
      const { data } = await api.get(`/recommendations/${selectedCompanyId}`);
      setRecs(data);
    } finally {
      setLoading(false);
    }
  }, [selectedCompanyId]);

  useEffect(() => {
    fetchRecs();
  }, [fetchRecs]);

  const generate = async () => {
    setGenerating(true);
    setError("");
    try {
      const { data } = await api.post(`/recommendations/${selectedCompanyId}`);
      setRecs(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Could not generate recommendations — run analysis first.");
    } finally {
      setGenerating(false);
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
        <h1 className="text-2xl font-semibold text-white">AI Recommendations</h1>
        <button className="btn-primary" onClick={generate} disabled={generating}>
          {generating ? "Generating…" : "Generate Recommendations"}
        </button>
      </div>

      {error && <p className="mb-4 rounded-lg bg-red-950 px-3 py-2 text-sm text-red-400">{error}</p>}
      {!loading && recs.length === 0 && (
        <p className="text-slate-400">No recommendations yet — click Generate Recommendations.</p>
      )}

      <div className="space-y-3">
        {recs.map((r) => (
          <div key={r.id} className={`card border ${PRIORITY_STYLES[r.priority] || ""}`}>
            <div className="flex items-start gap-3">
              <span className="text-xl">{CATEGORY_ICON[r.category] || "💡"}</span>
              <div className="flex-1">
                <div className="mb-1 flex items-center gap-2">
                  <span className="rounded-full bg-slate-800 px-2 py-0.5 text-[10px] uppercase text-slate-400">{r.category}</span>
                  <span className="rounded-full bg-slate-800 px-2 py-0.5 text-[10px] uppercase text-slate-400">{r.priority} priority</span>
                </div>
                <p className="text-sm text-slate-100">{r.text}</p>
                {r.based_on && <p className="mt-1 text-xs text-slate-500">Based on: {r.based_on}</p>}
              </div>
            </div>
          </div>
        ))}
      </div>
    </AppLayout>
  );
}
