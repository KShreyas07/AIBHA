import { createContext, useContext, useEffect, useState, useCallback } from "react";
import api from "../services/api";
import { useAuth } from "./AuthContext";

const CompanyContext = createContext(null);

export function CompanyProvider({ children }) {
  const { isAuthenticated } = useAuth();
  const [companies, setCompanies] = useState([]);
  const [selectedCompanyId, setSelectedCompanyId] = useState(() => localStorage.getItem("bha_company_id") || null);
  const [loading, setLoading] = useState(false);

  const refreshCompanies = useCallback(async () => {
    if (!isAuthenticated) return;
    setLoading(true);
    try {
      const { data } = await api.get("/company");
      setCompanies(data);
      // The stored selectedCompanyId may be stale — e.g. left over in localStorage
      // from a different backend/database (same origin, different environment).
      // Validate it against the freshly-fetched list rather than trusting it blindly.
      const stillExists = data.some((c) => c.id === selectedCompanyId);
      if (!stillExists) {
        if (data.length > 0) {
          selectCompany(data[0].id);
        } else {
          setSelectedCompanyId(null);
          localStorage.removeItem("bha_company_id");
        }
      }
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isAuthenticated]);

  useEffect(() => {
    refreshCompanies();
  }, [refreshCompanies]);

  const selectCompany = (id) => {
    setSelectedCompanyId(id);
    localStorage.setItem("bha_company_id", id);
  };

  const selectedCompany = companies.find((c) => c.id === selectedCompanyId) || null;

  return (
    <CompanyContext.Provider
      value={{ companies, selectedCompany, selectedCompanyId, selectCompany, refreshCompanies, loading }}
    >
      {children}
    </CompanyContext.Provider>
  );
}

export function useCompany() {
  const ctx = useContext(CompanyContext);
  if (!ctx) throw new Error("useCompany must be used within CompanyProvider");
  return ctx;
}
