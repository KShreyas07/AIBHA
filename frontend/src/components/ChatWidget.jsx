import { useState, useRef, useEffect, useCallback } from "react";
import api from "../services/api";
import { useCompany } from "../context/CompanyContext";

const WELCOME = {
  role: "assistant",
  text: "I'm your AI CFO — ask me about profit, revenue, risks, forecasts, cash runway, or your goals.",
};

const SUGGESTIONS = [
  "What's my cash runway?",
  "Am I on track with my goals?",
  "Why is my health score low?",
  "How can I increase profit?",
  "What risks do I have?",
];

export default function ChatWidget() {
  const { selectedCompanyId } = useCompany();
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([WELCOME]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(false);
  const endRef = useRef(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, open]);

  const fetchHistory = useCallback(async () => {
    if (!selectedCompanyId) return;
    setLoadingHistory(true);
    try {
      const { data } = await api.get(`/chat/${selectedCompanyId}/history`);
      setMessages(data.length > 0 ? data.map((m) => ({ role: m.role, text: m.content })) : [WELCOME]);
    } catch {
      setMessages([WELCOME]);
    } finally {
      setLoadingHistory(false);
    }
  }, [selectedCompanyId]);

  useEffect(() => {
    if (open) fetchHistory();
  }, [open, selectedCompanyId, fetchHistory]);

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

  const clearConversation = async () => {
    if (!selectedCompanyId) return;
    await api.delete(`/chat/${selectedCompanyId}/history`);
    setMessages([WELCOME]);
  };

  if (!open) {
    return (
      <button
        onClick={() => setOpen(true)}
        className="fixed bottom-6 right-6 flex h-14 w-14 items-center justify-center rounded-full bg-brand-600 text-2xl shadow-lg shadow-brand-900/50 transition hover:bg-brand-700"
        aria-label="Open AI CFO"
      >
        💬
      </button>
    );
  }

  return (
    <div className="fixed bottom-6 right-6 flex h-[32rem] w-96 flex-col overflow-hidden rounded-3xl border border-ink-100 bg-white shadow-2xl shadow-ink-900/10">
      <div className="flex items-center justify-between border-b border-ink-100 bg-cream-50 px-4 py-3">
        <div>
          <p className="font-display text-sm font-semibold text-ink-900">AI CFO</p>
          <p className="text-[10px] text-ink-400">Grounded in your live financial data</p>
        </div>
        <div className="flex items-center gap-3">
          <button onClick={clearConversation} className="text-xs text-ink-400 hover:text-red-600" title="Clear conversation">
            Clear
          </button>
          <button onClick={() => setOpen(false)} className="text-ink-400 hover:text-ink-900">
            ✕
          </button>
        </div>
      </div>
      <div className="flex-1 space-y-3 overflow-y-auto p-4">
        {loadingHistory && <div className="text-xs text-ink-400">Loading conversation…</div>}
        {messages.map((m, i) => (
          <div
            key={i}
            className={`max-w-[85%] whitespace-pre-wrap rounded-2xl px-3 py-2 text-sm ${
              m.role === "user" ? "ml-auto bg-ink-900 text-cream-50" : "bg-cream-100 text-ink-900"
            }`}
          >
            {m.text}
          </div>
        ))}
        {sending && <div className="text-xs text-ink-400">Thinking…</div>}
        <div ref={endRef} />
      </div>
      {messages.length <= 1 && (
        <div className="flex flex-wrap gap-1 border-t border-ink-100 p-2">
          {SUGGESTIONS.map((s) => (
            <button
              key={s}
              onClick={() => send(s)}
              className="rounded-full border border-ink-200 px-2 py-1 text-[11px] text-ink-500 hover:bg-cream-100"
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
        className="flex gap-2 border-t border-ink-100 p-3"
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
