import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function Register() {
  const { register, loading } = useAuth();
  const navigate = useNavigate();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const onSubmit = async (e) => {
    e.preventDefault();
    setError("");
    try {
      await register(fullName, email, password);
      navigate("/dashboard");
    } catch (err) {
      setError(err.response?.data?.detail || "Registration failed");
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-cream-100 px-4">
      <div className="w-full max-w-sm">
        <div className="mb-6 text-center">
          <span className="font-display text-lg font-semibold text-ink-900">AIBHA</span>
          <h1 className="mt-2 font-display text-xl font-semibold text-ink-900">Create your account</h1>
          <p className="text-sm text-ink-500">Start analyzing your business health for free</p>
        </div>
        <form onSubmit={onSubmit} className="card space-y-4">
          {error && <p className="rounded-2xl bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p>}
          <div>
            <label className="label">Full Name</label>
            <input className="input" required value={fullName} onChange={(e) => setFullName(e.target.value)} />
          </div>
          <div>
            <label className="label">Email</label>
            <input className="input" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <div>
            <label className="label">Password</label>
            <input
              className="input"
              type="password"
              required
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
            <p className="mt-1 text-xs text-ink-400">At least 8 characters</p>
          </div>
          <button className="btn-primary w-full" type="submit" disabled={loading}>
            {loading ? "Creating account…" : "Create Account"}
          </button>
        </form>
        <p className="mt-4 text-center text-sm text-ink-500">
          Already have an account? <Link to="/login" className="text-brand-500 hover:underline">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
