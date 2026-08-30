import { useState } from "react";
import AppLayout from "../components/AppLayout";
import api from "../services/api";
import { useCompany } from "../context/CompanyContext";

const EMPTY_FORM = { name: "", industry: "", country: "", financial_year: "2026", business_size: "small", employees: 0 };

export default function Companies() {
  const { companies, refreshCompanies, selectCompany, selectedCompanyId } = useCompany();
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);

  const onChange = (e) => setForm((f) => ({ ...f, [e.target.name]: e.target.value }));

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSaving(true);
    try {
      const { data } = await api.post("/company", { ...form, employees: Number(form.employees) });
      await refreshCompanies();
      selectCompany(data.id);
      setForm(EMPTY_FORM);
    } catch (err) {
      setError(err.response?.data?.detail || "Could not create company");
    } finally {
      setSaving(false);
    }
  };

  const onDelete = async (id) => {
    if (!confirm("Delete this company and all its data? This cannot be undone.")) return;
    await api.delete(`/company/${id}`);
    await refreshCompanies();
  };

  return (
    <AppLayout>
      <h1 className="mb-6 text-2xl font-semibold text-white">Company Management</h1>
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2 space-y-3">
          {companies.length === 0 && <p className="text-sm text-slate-500">No companies yet — add your first one.</p>}
          {companies.map((c) => (
            <div
              key={c.id}
              className={`card flex items-center justify-between ${c.id === selectedCompanyId ? "border-brand-600" : ""}`}
            >
              <div>
                <p className="font-medium text-white">{c.name}</p>
                <p className="text-xs text-slate-400">
                  {c.industry} · {c.country} · {c.business_size} · {c.employees} employees · FY {c.financial_year}
                </p>
              </div>
              <div className="flex gap-2">
                <button className="btn-secondary text-xs" onClick={() => selectCompany(c.id)}>
                  {c.id === selectedCompanyId ? "Selected" : "Select"}
                </button>
                <button className="btn-secondary text-xs text-red-400" onClick={() => onDelete(c.id)}>
                  Delete
                </button>
              </div>
            </div>
          ))}
        </div>

        <form onSubmit={onSubmit} className="card h-fit space-y-3">
          <h2 className="font-semibold text-white">Add Company</h2>
          {error && <p className="rounded-lg bg-red-950 px-3 py-2 text-sm text-red-400">{error}</p>}
          <div>
            <label className="label">Company Name</label>
            <input className="input" name="name" required value={form.name} onChange={onChange} />
          </div>
          <div>
            <label className="label">Industry</label>
            <input className="input" name="industry" required placeholder="Retail, Technology…" value={form.industry} onChange={onChange} />
          </div>
          <div>
            <label className="label">Country</label>
            <input className="input" name="country" required value={form.country} onChange={onChange} />
          </div>
          <div>
            <label className="label">Financial Year</label>
            <input className="input" name="financial_year" required value={form.financial_year} onChange={onChange} />
          </div>
          <div>
            <label className="label">Business Size</label>
            <select className="input" name="business_size" value={form.business_size} onChange={onChange}>
              <option value="micro">Micro</option>
              <option value="small">Small</option>
              <option value="medium">Medium</option>
            </select>
          </div>
          <div>
            <label className="label">Employees</label>
            <input className="input" type="number" min="0" name="employees" value={form.employees} onChange={onChange} />
          </div>
          <button className="btn-primary w-full" type="submit" disabled={saving}>
            {saving ? "Saving…" : "Add Company"}
          </button>
        </form>
      </div>
    </AppLayout>
  );
}
