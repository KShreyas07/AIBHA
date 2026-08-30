import { Link } from "react-router-dom";

const FEATURES = [
  { icon: "📊", title: "Business Health Score", desc: "A 0-100 score across revenue, profit, cash, inventory, debt, and customer growth." },
  { icon: "🔮", title: "AI Forecasting", desc: "6 and 12-month projections for revenue, profit, expenses, and cash flow." },
  { icon: "⚠️", title: "Risk Detection", desc: "Automatic detection of cash flow issues, debt risk, and revenue decline." },
  { icon: "💡", title: "AI Recommendations", desc: "GPT-powered, data-grounded suggestions to improve your business." },
  { icon: "📈", title: "Industry Benchmarking", desc: "See how you stack up against industry-average margins and ratios." },
  { icon: "💬", title: "Chat Assistant", desc: "Ask questions about your business in plain English." },
];

const STATS = [
  { value: "12", label: "financial ratios engineered automatically from your uploads" },
  { value: "0–100", label: "weighted Business Health Score, validated against real outcomes" },
  { value: "6 & 12mo", label: "AI-selected revenue, profit, expense & cash flow forecasts" },
];

export default function Landing() {
  return (
    <div className="min-h-screen bg-cream-100 text-ink-900">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-6 py-6">
        <div className="flex items-center gap-2">
          <span className="text-2xl">🧠</span>
          <span className="font-display font-semibold">AI Business Health Analyzer</span>
        </div>
        <div className="flex gap-3">
          <Link to="/login" className="btn-secondary">Login</Link>
          <Link to="/register" className="btn-primary">Get Started</Link>
        </div>
      </header>

      <section className="mx-auto max-w-4xl px-6 py-24 text-center">
        <h1 className="font-display text-5xl font-semibold leading-[1.05] tracking-tight md:text-7xl">
          Know your business's health
          <span className="block text-brand-500">before it's a problem.</span>
        </h1>
        <p className="mx-auto mt-6 max-w-2xl text-lg text-ink-500">
          Upload your financials, and let machine learning and AI predict performance, score your business health,
          detect risks, and recommend what to do next.
        </p>
        <div className="mt-10 flex justify-center gap-3">
          <Link to="/register" className="btn-primary px-6 py-3 text-base">Start Free Analysis</Link>
          <Link to="/login" className="btn-secondary px-6 py-3 text-base">I have an account</Link>
        </div>
      </section>

      <section className="mx-auto max-w-6xl px-6 pb-20">
        <div className="grid grid-cols-1 gap-6 rounded-4xl border border-ink-100 bg-white p-10 sm:grid-cols-3">
          {STATS.map((s) => (
            <div key={s.label} className="text-center sm:text-left">
              <p className="font-display text-4xl font-semibold text-ink-900">{s.value}</p>
              <p className="mt-2 text-sm text-ink-500">{s.label}</p>
            </div>
          ))}
        </div>
      </section>

      <section className="mx-auto grid max-w-6xl grid-cols-1 gap-4 px-6 pb-24 md:grid-cols-3">
        {FEATURES.map((f) => (
          <div key={f.title} className="card">
            <div className="text-3xl">{f.icon}</div>
            <h3 className="mt-3 font-display font-semibold text-ink-900">{f.title}</h3>
            <p className="mt-1 text-sm text-ink-500">{f.desc}</p>
          </div>
        ))}
      </section>
    </div>
  );
}
