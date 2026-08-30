import { useCallback, useEffect, useState } from "react";
import AppLayout from "../components/AppLayout";
import api from "../services/api";
import { useCompany } from "../context/CompanyContext";

export default function Reports() {
  const { selectedCompanyId, selectedCompany } = useCompany();
  const [reports, setReports] = useState([]);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState("");

  const fetchReports = useCallback(async () => {
    if (!selectedCompanyId) return;
    const { data } = await api.get(`/report/${selectedCompanyId}`);
    setReports(data);
  }, [selectedCompanyId]);

  useEffect(() => {
    fetchReports();
  }, [fetchReports]);

  const generate = async () => {
    setGenerating(true);
    setError("");
    try {
      await api.post(`/report/${selectedCompanyId}`);
      await fetchReports();
    } catch (err) {
      setError(err.response?.data?.detail || "Could not generate report — run analysis first.");
    } finally {
      setGenerating(false);
    }
  };

  const download = async (reportId) => {
    const response = await api.get(`/report/${selectedCompanyId}/${reportId}/download`, { responseType: "blob" });
    const url = window.URL.createObjectURL(new Blob([response.data], { type: "application/pdf" }));
    const link = document.createElement("a");
    link.href = url;
    link.download = `${selectedCompany?.name || "company"}_health_report.pdf`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
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
      <div className="mb-6 flex items-center justify-between">
        <h1 className="text-2xl font-semibold text-ink-900">Reports</h1>
        <button className="btn-primary" onClick={generate} disabled={generating}>
          {generating ? "Generating…" : "Generate PDF Report"}
        </button>
      </div>

      {error && <p className="mb-4 rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>}

      <div className="card">
        <p className="mb-3 text-sm text-ink-500">
          Each report includes an executive summary, financial summary, health score breakdown, risk analysis,
          revenue forecast, and AI recommendations.
        </p>
        <div className="space-y-2">
          {reports.length === 0 && <p className="text-sm text-ink-400">No reports generated yet.</p>}
          {reports.map((r) => (
            <div key={r.id} className="flex items-center justify-between rounded-lg border border-ink-100 px-4 py-3">
              <div>
                <p className="text-sm font-medium text-ink-900">Full Health Report</p>
                <p className="text-xs text-ink-500">{new Date(r.created_at).toLocaleString()}</p>
              </div>
              <button className="btn-secondary text-xs" onClick={() => download(r.id)}>
                Download PDF
              </button>
            </div>
          ))}
        </div>
      </div>
    </AppLayout>
  );
}
