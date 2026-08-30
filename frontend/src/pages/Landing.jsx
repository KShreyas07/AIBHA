import { Link } from "react-router-dom";

const FEATURES = [
  { icon: "📊", title: "Business Health Score", desc: "A 0-100 score across revenue, profit, cash, inventory, debt, and customer growth." },
  { icon: "🔮", title: "AI Forecasting", desc: "6 and 12-month projections for revenue, profit, expenses, and cash flow." },
  { icon: "⚠️", title: "Risk Detection", desc: "Automatic detection of cash flow issues, debt risk, and revenue decline." },
  { icon: "💡", title: "AI Recommendations", desc: "GPT-powered, data-grounded suggestions to improve your business." },
  { icon: "📈", title: "Industry Benchmarking", desc: "See how you stack up against industry-average margins and ratios." },
  { icon: "💬", title: "Chat Assistant", desc: "Ask questions about your business in plain English." },
];

export default function Landing() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-100">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-6 py-6">
        <div className="flex items-center gap-2">
          <span className="text-2xl">🧠</span>
          <span className="font-semibold">AI Business Health Analyzer</span>
        </div>
        <div className="flex gap-3">
          <Link to="/login" className="btn-secondary">Login</Link>
          <Link to="/register" className="btn-primary">Get Started</Link>
        </div>
      </header>

      <section className="mx-auto max-w-4xl px-6 py-20 text-center">
        <h1 className="text-4xl font-bold leading-tight md:text-5xl">
          Know your business's health <span className="text-brand-400">before it's a problem.</span>
        </h1>
        <p className="mx-auto mt-4 max-w-2xl text-slate-400">
          Upload your financials, and let machine learning and AI predict performance, score your business health,
          detect risks, and recommend what to do next.
        </p>
        <div className="mt-8 flex justify-center gap-3">
          <Link to="/register" className="btn-primary px-6 py-3 text-base">Start Free Analysis</Link>
          <Link to="/login" className="btn-secondary px-6 py-3 text-base">I have an account</Link>
        </div>
      </section>

      <section className="mx-auto grid max-w-6xl grid-cols-1 gap-4 px-6 pb-24 md:grid-cols-3">
        {FEATURES.map((f) => (
          <div key={f.title} className="card">
            <div className="text-3xl">{f.icon}</div>
            <h3 className="mt-3 font-semibold text-white">{f.title}</h3>
            <p className="mt-1 text-sm text-slate-400">{f.desc}</p>
          </div>
        ))}
      </section>
    </div>
  );
}
