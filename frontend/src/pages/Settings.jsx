import AppLayout from "../components/AppLayout";
import { useAuth } from "../context/AuthContext";
import { useCompany } from "../context/CompanyContext";

export default function Settings() {
  const { user, logout } = useAuth();
  const { selectedCompany } = useCompany();

  return (
    <AppLayout>
      <h1 className="mb-6 text-2xl font-semibold text-white">Settings</h1>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <div className="card">
          <h2 className="mb-3 font-semibold text-white">Account</h2>
          <dl className="space-y-2 text-sm">
            <div className="flex justify-between"><dt className="text-slate-400">Name</dt><dd className="text-slate-100">{user?.full_name}</dd></div>
            <div className="flex justify-between"><dt className="text-slate-400">Email</dt><dd className="text-slate-100">{user?.email}</dd></div>
          </dl>
          <button className="btn-secondary mt-4 text-xs" onClick={logout}>Logout</button>
        </div>

        <div className="card">
          <h2 className="mb-3 font-semibold text-white">Active Company</h2>
          {selectedCompany ? (
            <dl className="space-y-2 text-sm">
              <div className="flex justify-between"><dt className="text-slate-400">Name</dt><dd className="text-slate-100">{selectedCompany.name}</dd></div>
              <div className="flex justify-between"><dt className="text-slate-400">Industry</dt><dd className="text-slate-100">{selectedCompany.industry}</dd></div>
              <div className="flex justify-between"><dt className="text-slate-400">Country</dt><dd className="text-slate-100">{selectedCompany.country}</dd></div>
              <div className="flex justify-between"><dt className="text-slate-400">Business Size</dt><dd className="text-slate-100">{selectedCompany.business_size}</dd></div>
              <div className="flex justify-between"><dt className="text-slate-400">Employees</dt><dd className="text-slate-100">{selectedCompany.employees}</dd></div>
            </dl>
          ) : (
            <p className="text-sm text-slate-500">No company selected. Manage companies from the Companies page.</p>
          )}
        </div>

        <div className="card md:col-span-2">
          <h2 className="mb-3 font-semibold text-white">AI Configuration</h2>
          <p className="text-sm text-slate-400">
            Recommendations and the chat assistant use the OpenAI API when <code className="rounded bg-slate-800 px-1">OPENAI_API_KEY</code> is
            configured on the backend. Without a key, the app automatically falls back to a rule-based engine so it
            keeps working out of the box.
          </p>
        </div>
      </div>
    </AppLayout>
  );
}
