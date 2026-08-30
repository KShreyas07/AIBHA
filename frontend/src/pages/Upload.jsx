import { useCallback, useEffect, useState } from "react";
import AppLayout from "../components/AppLayout";
import api from "../services/api";
import { useCompany } from "../context/CompanyContext";

const CATEGORIES = [
  { value: "income_statement", label: "Income Statement" },
  { value: "balance_sheet", label: "Balance Sheet" },
  { value: "cash_flow_statement", label: "Cash Flow Statement" },
  { value: "sales_report", label: "Sales Report" },
  { value: "expense_report", label: "Expense Report" },
  { value: "inventory_report", label: "Inventory Report" },
  { value: "customer_data", label: "Customer Data" },
];

// Every file needs a date/period column. These are the fields the parser looks for
// per category (column names are case-insensitive and match common synonyms too).
const FORMAT_GUIDE = {
  income_statement: {
    columns: ["revenue", "cogs", "operating_expenses", "net_profit", "currency (optional)"],
    example: "date, revenue, cogs, operating_expenses, net_profit, currency",
    note: "One row per month with your top-line revenue and profit figures.",
  },
  balance_sheet: {
    columns: ["current_assets", "current_liabilities", "total_debt", "total_equity", "cash_balance"],
    example: "date, current_assets, current_liabilities, total_debt, total_equity, cash_balance",
    note: "Snapshot values as of the end of each month.",
  },
  cash_flow_statement: {
    columns: ["cash_balance"],
    example: "date, cash_balance",
    note: "Ending/closing cash balance for each month.",
  },
  sales_report: {
    columns: ["revenue", "customers_count"],
    example: "date, revenue, customers_count",
    note: "Monthly sales totals, optionally with customer counts for growth tracking.",
  },
  expense_report: {
    columns: ["operating_expenses", "cogs"],
    example: "date, operating_expenses, cogs",
    note: "Monthly operating costs and cost of goods sold.",
  },
  inventory_report: {
    columns: ["inventory_value", "inventory_sold"],
    example: "date, inventory_value, inventory_sold",
    note: "Inventory on hand vs. units/value sold, used to compute turnover.",
  },
  customer_data: {
    columns: ["customers_count"],
    example: "date, customers_count",
    note: "Total or active customer count per month, used for growth rate.",
  },
};

const STATUS_STYLES = {
  uploaded: "bg-cream-200 text-ink-700",
  processing: "bg-amber-50 text-amber-700",
  processed: "bg-emerald-50 text-emerald-700",
  failed: "bg-red-50 text-red-600",
};

export default function Upload() {
  const { selectedCompanyId } = useCompany();
  const [category, setCategory] = useState(CATEGORIES[0].value);
  const [file, setFile] = useState(null);
  const [uploads, setUploads] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState("");

  const fetchUploads = useCallback(async () => {
    if (!selectedCompanyId) return;
    const { data } = await api.get("/upload", { params: { company_id: selectedCompanyId } });
    setUploads(data);
  }, [selectedCompanyId]);

  useEffect(() => {
    fetchUploads();
    const interval = setInterval(fetchUploads, 4000);
    return () => clearInterval(interval);
  }, [fetchUploads]);

  const onSubmit = async (e) => {
    e.preventDefault();
    if (!file || !selectedCompanyId) return;
    setError("");
    setUploading(true);
    try {
      const form = new FormData();
      form.append("company_id", selectedCompanyId);
      form.append("data_category", category);
      form.append("file", file);
      await api.post("/upload", form, { headers: { "Content-Type": "multipart/form-data" } });
      setFile(null);
      await fetchUploads();
    } catch (err) {
      setError(err.response?.data?.detail || "Upload failed");
    } finally {
      setUploading(false);
    }
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
      <h1 className="mb-6 text-2xl font-semibold text-ink-900">Upload Data</h1>
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="space-y-6">
          <form onSubmit={onSubmit} className="card h-fit space-y-4">
            <h2 className="font-semibold text-ink-900">New Upload</h2>
            {error && <p className="rounded-lg bg-red-50 px-3 py-2 text-sm text-red-600">{error}</p>}
            <div>
              <label className="label">Data Category</label>
              <select className="input" value={category} onChange={(e) => setCategory(e.target.value)}>
                {CATEGORIES.map((c) => (
                  <option key={c.value} value={c.value}>{c.label}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">File (CSV, Excel, or PDF)</label>
              <input
                className="input"
                type="file"
                accept=".csv,.xlsx,.xls,.pdf"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
                required
              />
            </div>
            <button className="btn-primary w-full" type="submit" disabled={uploading}>
              {uploading ? "Uploading…" : "Upload & Process"}
            </button>
          </form>

          <div className="card h-fit space-y-3">
            <h2 className="font-semibold text-ink-900">
              Accepted Format — {CATEGORIES.find((c) => c.value === category)?.label}
            </h2>
            <p className="text-sm text-ink-500">{FORMAT_GUIDE[category].note}</p>
            <div>
              <p className="label mb-1">Required</p>
              <p className="text-sm text-ink-700">A date/period column (e.g. <code className="rounded bg-cream-100 px-1">date</code>)</p>
            </div>
            <div>
              <p className="label mb-1">Recommended columns</p>
              <ul className="list-inside list-disc space-y-0.5 text-sm text-ink-700">
                {FORMAT_GUIDE[category].columns.map((col) => (
                  <li key={col}><code className="rounded bg-cream-100 px-1">{col}</code></li>
                ))}
              </ul>
            </div>
            <div>
              <p className="label mb-1">Example header row</p>
              <code className="block overflow-x-auto rounded-lg bg-cream-100 px-3 py-2 text-xs text-brand-500">
                {FORMAT_GUIDE[category].example}
              </code>
            </div>
            <p className="text-xs text-ink-400">
              One row per month. Column names are case-insensitive and common synonyms are
              recognized automatically (e.g. "Total Revenue", "Net Income"). Files: CSV, Excel
              (.xlsx/.xls), or text-based PDF tables.
            </p>
          </div>
        </div>

        <div className="lg:col-span-2 space-y-3">
          <h2 className="font-semibold text-ink-900">Upload History</h2>
          {uploads.length === 0 && <p className="text-sm text-ink-400">No uploads yet.</p>}
          {uploads.map((u) => (
            <div key={u.id} className="card flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-ink-900">{u.filename}</p>
                <p className="text-xs text-ink-500">
                  {CATEGORIES.find((c) => c.value === u.data_category)?.label || u.data_category} ·{" "}
                  {new Date(u.created_at).toLocaleString()}
                </p>
                {u.error_message && <p className="mt-1 text-xs text-red-600">{u.error_message}</p>}
              </div>
              <span className={`rounded-full px-2 py-1 text-xs ${STATUS_STYLES[u.status] || ""}`}>{u.status}</span>
            </div>
          ))}
        </div>
      </div>
    </AppLayout>
  );
}
