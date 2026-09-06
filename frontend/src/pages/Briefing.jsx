import { useCallback, useEffect, useState } from "react";
import AppLayout from "../components/AppLayout";
import api from "../services/api";
import { useCompany } from "../context/CompanyContext";

const AGENT_ICON = {
  "Cash Flow Agent": "🏦",
  "Risk Agent": "🚨",
  "Growth Agent": "📈",
  "Goals Agent": "🎯",
};

const SEVERITY_STYLES = {
  high: "border-red-200 bg-red-50",
  medium: "border-amber-200 bg-amber-50",
  low: "border-ink-100 bg-white",
};

const SEVERITY_BADGE = {
  high: "bg-red-100 text-red-700",
  medium: "bg-amber-100 text-amber-700",
  low: "bg-emerald-100 text-emerald-700",
};

const VERDICT_STYLES = {
  Urgent: "bg-red-50 border-red-200 text-red-800",
  Watch: "bg-amber-50 border-amber-200 text-amber-800",
  Healthy: "bg-emerald-50 border-emerald-200 text-emerald-800",
};

export default function Briefing() {
  const { selectedCompanyId } = useCompany();
  const [briefing, setBriefing] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchBriefing = useCallback(async () => {
    if (!selectedCompanyId) return;
    setLoading(true);
    setError("");
    try {
      const { data } = await api.get(`/briefing/${selectedCompanyId}`);
      setBriefing(data);
    } catch (err) {
      setError(err.response?.data?.detail || "Could not generate a briefing — process financial data for this company first.");
      setBriefing(null);
    } finally {
      setLoading(false);
    }
  }, [selectedCompanyId]);

  useEffect(() => {
    fetchBriefing();
  }, [fetchBriefing]);

  if (!selectedCompanyId) {
    return (
      <AppLayout>
        <p className="text-ink-500">Select or create a company first from the top bar.</p>
      </AppLayout>
    );
  }

  return (
    <AppLayout>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-ink-900">AI Briefing</h1>
          <p className="text-sm text-ink-500">
            Four specialist agents each analyze one part of your business, then a chief-of-staff agent synthesizes it.
          </p>
        </div>
        <button className="btn-secondary" onClick={fetchBriefing} disabled={loading}>
          {loading ? "Refreshing…" : "Refresh Briefing"}
        </button>
      </div>

      {error && <p className="mb-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>}

      {briefing && (
        <>
          <div className={`mb-6 rounded-2xl border p-5 ${VERDICT_STYLES[briefing.overall_verdict] || ""}`}>
            <div className="mb-2 flex items-center gap-2">
              <span className="text-xs font-semibold uppercase tracking-wide">Executive Summary</span>
              <span className="rounded-full bg-white/60 px-2 py-0.5 text-[10px] font-bold uppercase">
                {briefing.overall_verdict}
              </span>
            </div>
            <p className="text-sm leading-relaxed">{briefing.executive_summary}</p>
          </div>

          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            {briefing.findings.map((f) => (
              <div key={f.agent} className={`card border ${SEVERITY_STYLES[f.severity] || ""}`}>
                <div className="mb-2 flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <span className="text-xl">{AGENT_ICON[f.agent] || "🤖"}</span>
                    <span className="font-medium text-ink-900">{f.agent}</span>
                  </div>
                  <span className={`rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase ${SEVERITY_BADGE[f.severity] || ""}`}>
                    {f.severity}
                  </span>
                </div>
                <p className="mb-2 text-sm text-ink-900">{f.summary}</p>
                <p className="text-xs text-ink-500">→ {f.recommendation}</p>
              </div>
            ))}
          </div>
        </>
      )}
    </AppLayout>
  );
}
