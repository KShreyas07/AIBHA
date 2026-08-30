import { useState, useRef, useEffect } from "react";
import api from "../services/api";
import { useCompany } from "../context/CompanyContext";

const SUGGESTIONS = [
  "Why is my health score low?",
  "How can I increase profit?",
  "Predict my revenue.",
  "Why are expenses increasing?",
  "What risks do I have?",
];

export default function ChatWidget() {
  const { selectedCompanyId } = useCompany();
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([
    { role: "assistant", text: "Ask me anything about your business data — profit, revenue, risks, or forecasts." },
  ]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, open]);

  const send = async (text) => {
    const message = (text ?? input).trim();
    if (!message || !selectedCompanyId || sending) return;

    setMessages((m) => [...m, { role: "user", text: message }]);
    setInput("");
    setSending(true);
    try {
      const { data } = await api.post("/chat", { company_id: selectedCompanyId, message });
      setMessages((m) => [...m, { role: "assistant", text: data.answer }]);
    } catch (err) {
      setMessages((m) => [
        ...m,
        { role: "assistant", text: err.response?.data?.detail || "Something went wrong answering that." },
      ]);
    } finally {
      setSending(false);
    }
  };

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="fixed bottom-6 right-6 flex h-14 w-14 items-center justify-center rounded-full bg-brand-600 text-2xl shadow-lg shadow-brand-900/50 transition hover:bg-brand-700"
        aria-label="Open chat assistant"
      >
        💬
      </button>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 flex h-[32rem] w-96 flex-col overflow-hidden rounded-xl border border-slate-800 bg-slate-900 shadow-2xl">
      <div className="flex items-center justify-between border-b border-slate-800 bg-slate-950 px-4 py-3">
        <p className="text-sm font-semibold text-white">AI Chat Assistant</p>
        <button onClick={() => setOpen(false)} className="text-slate-400 hover:text-white">
          ✕
        </button>
      </div>
      <div className="flex-1 space-y-3 overflow-y-auto p-4">
        {messages.map((m, i) => (
          <div
            key={i}
            className={`max-w-[85%] rounded-lg px-3 py-2 text-sm ${
              m.role === "user" ? "ml-auto bg-brand-600 text-white" : "bg-slate-800 text-slate-100"
            }`}
          >
            {m.text}
          </div>
        ))}
        {sending && <div className="text-xs text-slate-500">Thinking…</div>}
        <div ref={endRef} />
      </div>
      {messages.length <= 1 && (
        <div className="flex flex-wrap gap-1 border-t border-slate-800 p-2">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              onClick={() => send(s)}
              className="rounded-full border border-slate-700 px-2 py-1 text-[11px] text-slate-400 hover:bg-slate-800"
            >
              {s}
            </button>
          ))}
        </div>
      )}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          send();
        }}
        className="flex gap-2 border-t border-slate-800 p-3"
      >
        <input
          className="input"
          placeholder={selectedCompanyId ? "Ask about your business…" : "Select a company first"}
          value={input}
          disabled={!selectedCompanyId}
          onChange={(e) => setInput(e.target.value)}
        />
        <button className="btn-primary" type="submit" disabled={!selectedCompanyId || sending}>
          Send
        </button>
      </form>
    </div>
  );
}
