"use client";

import Link from "next/link";
import { useCallback, useRef, useState } from "react";
import { getApiBase } from "@/lib/apiBase";
import { LANGUAGES } from "@/lib/languages";
import { setTheme } from "@/components/ThemeInit";
import VoiceInput from "@/components/VoiceInput";
import ThemeToggle from "@/components/ThemeToggle";
import { ThemeInit } from "@/components/ThemeInit";

type Msg = { role: "user" | "assistant"; text: string; file?: string };

type Analysis = {
  document_summary: string;
  advice: string;
  action_steps: string[];
  relevant_sections: { section: unknown; name?: string; relevance?: number }[];
  ipc_mapping: { ipc_section: number; bns_section: number; note: string }[];
  ocr_method?: string;
  document_text_preview?: string;
};

/* ── small helpers ─────────────────────────────────────────────── */
function TypingIndicator() {
  return (
    <div className="bubble-ai flex items-center gap-1.5 py-4">
      <span className="dot-1 h-2 w-2 rounded-full" style={{ background: "var(--fg2)" }} />
      <span className="dot-2 h-2 w-2 rounded-full" style={{ background: "var(--fg2)" }} />
      <span className="dot-3 h-2 w-2 rounded-full" style={{ background: "var(--fg2)" }} />
    </div>
  );
}

/* ── Main component ────────────────────────────────────────────── */
export default function ChatPage() {
  const base = getApiBase();
  const [lang, setLang] = useState("hi-IN");
  const [busy, setBusy] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [docPreview, setDocPreview] = useState<string | null>(null);
  const [messages, setMessages] = useState<Msg[]>([]);
  const [followUp, setFollowUp] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const fileRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const endRef = useRef<HTMLDivElement>(null);

  const scrollEnd = useCallback(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  /* ── file upload & analysis ───────────────────────────────── */
  const analyze = async (file: File) => {
    setError(null);
    setBusy(true);
    setMessages((m) => [
      ...m,
      { role: "user", text: "Uploaded document for analysis.", file: file.name },
    ]);
    try {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("language", lang);
      const r = await fetch(`${base}/api/analyze_upload`, { method: "POST", body: fd });
      const txt = await r.text();
      if (!r.ok) throw new Error(txt || r.statusText);
      const data = JSON.parse(txt) as {
        analysis: Analysis;
        session_id: string;
        audio_base64?: string;
        latency_sec?: number;
      };
      setSessionId(data.session_id);
      setDocPreview(data.analysis.document_text_preview ?? null);
      const a = data.analysis;
      let body = `${a.document_summary}\n\n${a.advice}`;
      if (a.action_steps?.length) {
        body += "\n\nNext steps:\n" + a.action_steps.map((s, i) => `${i + 1}. ${s}`).join("\n");
      }
      setMessages((m) => [...m, { role: "assistant", text: body }]);
    } catch (e) {
      setError(String(e));
      setMessages((m) => [...m, { role: "assistant", text: `Error: ${e}` }]);
    } finally {
      setBusy(false);
      scrollEnd();
    }
  };

  const onFile = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0];
    e.target.value = "";
    if (!f) return;
    const max = f.type === "application/pdf" ? 8 * 1024 * 1024 : 5 * 1024 * 1024;
    if (f.size > max) {
      setError("File too large (max 5 MB images, 8 MB PDF).");
      return;
    }
    void analyze(f);
  };

  /* ── follow-up chat ───────────────────────────────────────── */
  const sendChat = async () => {
    const t = followUp.trim();
    if (!t || !sessionId) return;
    setError(null);
    setBusy(true);
    setFollowUp("");
    setMessages((m) => [...m, { role: "user", text: t }]);
    try {
      const r = await fetch(`${base}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          message: t,
          language: lang,
          document_context: docPreview,
        }),
      });
      const txt = await r.text();
      if (!r.ok) throw new Error(txt);
      const data = JSON.parse(txt) as { reply: string };
      setMessages((m) => [...m, { role: "assistant", text: data.reply }]);
    } catch (e) {
      setError(String(e));
      setMessages((m) => [...m, { role: "assistant", text: `Error: ${e}` }]);
    } finally {
      setBusy(false);
      scrollEnd();
    }
  };

  /* ── textarea auto-resize ─────────────────────────────────── */
  const handleTextareaInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setFollowUp(e.target.value);
    const el = e.target;
    el.style.height = "auto";
    el.style.height = `${Math.min(el.scrollHeight, 160)}px`;
  };

  /* ── voice transcript ─────────────────────────────────────── */
  const onTranscript = useCallback((text: string) => {
    setFollowUp((prev) => (prev ? `${prev} ${text}` : text));
    textareaRef.current?.focus();
  }, []);

  const currentLangLabel = LANGUAGES.find((l) => l.code === lang)?.label ?? lang;

  /* ────────────────────────────────────────────────────────── */
  return (
    <>
      <ThemeInit />
      <div className="flex h-dvh w-full overflow-hidden">
        {/* ── Sidebar ────────────────────────────────────────── */}
        {/* Mobile overlay */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 z-30 md:hidden"
            style={{ background: "rgba(0,0,0,0.5)" }}
            onClick={() => setSidebarOpen(false)}
          />
        )}

        <aside
          className={`
            glass-sidebar fixed inset-y-0 left-0 z-40 flex w-72 flex-col p-5 gap-5
            transition-transform duration-300
            ${sidebarOpen ? "translate-x-0" : "-translate-x-full"}
            md:relative md:translate-x-0
          `}
        >
          {/* Logo */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div
                className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl text-white text-base font-black"
                style={{ background: "var(--user-grad)" }}
              >
                ⚖
              </div>
              <div>
                <p className="text-sm font-bold leading-tight">Nyaya-Sahayak</p>
                <p className="text-xs" style={{ color: "var(--fg2)" }}>न्याय सहायक</p>
              </div>
            </div>
            <button
              className="btn-icon h-8 w-8 md:hidden"
              onClick={() => setSidebarOpen(false)}
              aria-label="Close sidebar"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path d="M18 6 6 18M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Nav links */}
          <nav className="space-y-1">
            <Link
              href="/"
              className="btn-ghost flex w-full items-center gap-3 px-3 py-2.5 text-sm"
            >
              <svg className="h-4 w-4 shrink-0" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
                <polyline points="9,22 9,12 15,12 15,22" />
              </svg>
              Home
            </Link>
            <a
              href="/api/health"
              target="_blank"
              rel="noopener"
              className="btn-ghost flex w-full items-center gap-3 px-3 py-2.5 text-sm"
            >
              <svg className="h-4 w-4 shrink-0" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <polyline points="22,12 18,12 15,21 9,3 6,12 2,12" />
              </svg>
              API health
            </a>
            <a
              href="/docs"
              target="_blank"
              rel="noopener"
              className="btn-ghost flex w-full items-center gap-3 px-3 py-2.5 text-sm"
            >
              <svg className="h-4 w-4 shrink-0" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14,2 14,8 20,8" />
              </svg>
              API docs
            </a>
          </nav>

          <hr style={{ borderColor: "var(--border)" }} />

          {/* Language selector */}
          <div>
            <label className="mb-1.5 block text-xs font-semibold uppercase tracking-widest" style={{ color: "var(--fg2)" }}>
              Response language
            </label>
            <select
              className="ns-input"
              value={lang}
              onChange={(e) => setLang(e.target.value)}
            >
              {LANGUAGES.map((l) => (
                <option key={l.code} value={l.code}>
                  {l.label}
                </option>
              ))}
            </select>
          </div>

          {/* Upload */}
          <div>
            <label className="mb-1.5 block text-xs font-semibold uppercase tracking-widest" style={{ color: "var(--fg2)" }}>
              Upload document
            </label>
            <input ref={fileRef} type="file" accept=".pdf,image/*" className="hidden" onChange={onFile} />
            <button
              type="button"
              disabled={busy}
              onClick={() => fileRef.current?.click()}
              className="btn-accent w-full gap-3 px-4 py-3 text-sm"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="17,8 12,3 7,8" />
                <line x1="12" y1="3" x2="12" y2="15" />
              </svg>
              {busy ? "Processing…" : "Upload FIR / Notice"}
            </button>
            <p className="mt-1.5 text-xs" style={{ color: "var(--fg2)" }}>
              PDF ≤ 8 MB · Image ≤ 5 MB
            </p>
          </div>

          {sessionId && (
            <div
              className="rounded-xl border p-3 text-xs"
              style={{ borderColor: "var(--accent)", background: "var(--glow)", color: "var(--accent)" }}
            >
              <p className="font-semibold">Session active</p>
              <p className="mt-0.5 opacity-70 truncate">{sessionId}</p>
            </div>
          )}

          {/* Spacer */}
          <div className="flex-1" />

          <hr style={{ borderColor: "var(--border)" }} />

          {/* Theme toggle */}
          <div className="flex items-center justify-between">
            <span className="text-xs" style={{ color: "var(--fg2)" }}>Appearance</span>
            <ThemeToggle />
          </div>

          <p className="text-xs" style={{ color: "var(--fg2)" }}>
            Prototype · not legal advice
          </p>
        </aside>

        {/* ── Main chat area ─────────────────────────────────── */}
        <main className="flex flex-1 flex-col overflow-hidden">
          {/* Mobile header */}
          <header
            className="glass-nav flex shrink-0 items-center justify-between px-4 py-3 md:hidden"
          >
            <button
              className="btn-icon h-9 w-9"
              onClick={() => setSidebarOpen(true)}
              aria-label="Open sidebar"
            >
              <svg className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <line x1="3" y1="12" x2="21" y2="12" />
                <line x1="3" y1="6" x2="21" y2="6" />
                <line x1="3" y1="18" x2="21" y2="18" />
              </svg>
            </button>
            <div className="flex items-center gap-2">
              <div
                className="flex h-7 w-7 items-center justify-center rounded-lg text-white text-xs font-black"
                style={{ background: "var(--user-grad)" }}
              >
                ⚖
              </div>
              <span className="text-sm font-bold">Nyaya-Sahayak</span>
            </div>
            <ThemeToggle />
          </header>

          {/* Desktop header strip */}
          <div
            className="hidden shrink-0 items-center justify-between border-b px-6 py-3 md:flex"
            style={{ borderColor: "var(--border)" }}
          >
            <div>
              <h2 className="text-sm font-bold">Legal Assistant</h2>
              <p className="text-xs" style={{ color: "var(--fg2)" }}>
                BNS · {currentLangLabel} · {sessionId ? "Session active" : "No session"}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span
                className="rounded-full px-3 py-1 text-xs font-medium"
                style={{ background: "var(--glow)", color: "var(--accent)" }}
              >
                {currentLangLabel}
              </span>
              <ThemeToggle />
            </div>
          </div>

          {/* Messages */}
          <div className="flex-1 overflow-y-auto px-4 py-6 md:px-8">
            <div className="mx-auto max-w-3xl space-y-4">

              {/* Welcome state */}
              {messages.length === 0 && !busy && (
                <div className="fade-in flex flex-col items-center justify-center py-16 text-center">
                  <div
                    className="mb-5 flex h-16 w-16 items-center justify-center rounded-2xl text-2xl text-white"
                    style={{ background: "var(--user-grad)", boxShadow: "0 8px 32px var(--glow)" }}
                  >
                    ⚖
                  </div>
                  <h3 className="text-xl font-bold">How can I help?</h3>
                  <p className="mt-2 max-w-sm text-sm" style={{ color: "var(--fg2)" }}>
                    Upload a document from the sidebar, or type / speak your legal question below.
                  </p>
                  <div className="mt-6 grid gap-2 sm:grid-cols-2">
                    {[
                      "What are my rights under BNS Section 115?",
                      "Explain IPC Section 420 in simple Hindi",
                      "What to do after receiving a police notice?",
                      "Difference between cognizable and non-cognizable offences",
                    ].map((s) => (
                      <button
                        key={s}
                        type="button"
                        onClick={() => setFollowUp(s)}
                        className="glass rounded-xl px-4 py-3 text-left text-xs transition-all hover:border-[var(--accent)]"
                        style={{ color: "var(--fg2)" }}
                      >
                        {s}
                      </button>
                    ))}
                  </div>
                  <p
                    className="mt-4 text-xs"
                    style={{ color: "var(--fg2)" }}
                  >
                    Voice input available — click the mic button below after uploading a document or typing a question.
                  </p>
                </div>
              )}

              {/* Message list */}
              {messages.map((m, i) => (
                <div
                  key={i}
                  className={`fade-up flex gap-2 ${m.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  {m.role === "assistant" && (
                    <div
                      className="mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-bold text-white"
                      style={{ background: "var(--user-grad)" }}
                    >
                      ⚖
                    </div>
                  )}
                  <div className={m.role === "user" ? "bubble-user" : "bubble-ai"}>
                    {m.file && (
                      <p
                        className="mb-1.5 flex items-center gap-1.5 text-xs font-semibold opacity-70"
                      >
                        <svg className="h-3 w-3" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                          <polyline points="14,2 14,8 20,8" />
                        </svg>
                        {m.file}
                      </p>
                    )}
                    <p className="whitespace-pre-wrap">{m.text}</p>
                  </div>
                  {m.role === "user" && (
                    <div
                      className="mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-bold"
                      style={{ background: "var(--card2)", border: "1px solid var(--border)", color: "var(--fg)" }}
                    >
                      U
                    </div>
                  )}
                </div>
              ))}

              {/* Typing */}
              {busy && (
                <div className="flex gap-2 justify-start">
                  <div
                    className="mt-1 flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-bold text-white"
                    style={{ background: "var(--user-grad)" }}
                  >
                    ⚖
                  </div>
                  <TypingIndicator />
                </div>
              )}

              <div ref={endRef} />
            </div>
          </div>

          {/* Error bar */}
          {error && (
            <div
              className="mx-4 mb-2 flex items-center gap-3 rounded-xl border px-4 py-3 text-sm md:mx-8"
              style={{
                background: "rgba(239,68,68,0.08)",
                borderColor: "rgba(239,68,68,0.3)",
                color: "#fca5a5",
              }}
            >
              <svg className="h-4 w-4 shrink-0" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="12" />
                <line x1="12" y1="16" x2="12.01" y2="16" />
              </svg>
              <span className="flex-1">{error}</span>
              <button onClick={() => setError(null)} className="shrink-0 opacity-60 hover:opacity-100">
                <svg className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
                  <path d="M18 6 6 18M6 6l12 12" />
                </svg>
              </button>
            </div>
          )}

          {/* Input bar */}
          <div
            className="shrink-0 border-t px-4 py-4 md:px-8"
            style={{ borderColor: "var(--border)", background: "var(--sidebar)" }}
          >
            <div className="mx-auto max-w-3xl">
              {!sessionId && messages.length === 0 && (
                <p className="mb-2 text-center text-xs" style={{ color: "var(--fg2)" }}>
                  Upload a document first, or ask a general BNS question below
                </p>
              )}
              <div className="flex items-end gap-2">
                <div className="relative flex-1">
                  <textarea
                    ref={textareaRef}
                    className="ns-input resize-none pr-4"
                    rows={1}
                    placeholder={
                      sessionId
                        ? "Ask a follow-up question…"
                        : "Ask a question about Indian law (BNS)…"
                    }
                    value={followUp}
                    onChange={handleTextareaInput}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" && !e.shiftKey) {
                        e.preventDefault();
                        void sendChat();
                      }
                    }}
                    disabled={busy}
                    style={{ minHeight: "44px", maxHeight: "160px" }}
                  />
                </div>

                {/* Voice input */}
                <VoiceInput
                  language={lang}
                  onTranscript={onTranscript}
                  disabled={busy}
                />

                {/* Send */}
                <button
                  type="button"
                  onClick={() => void sendChat()}
                  disabled={busy || !followUp.trim()}
                  className="btn-accent h-11 w-11 shrink-0 rounded-2xl"
                  aria-label="Send message"
                >
                  <svg className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                    <path d="M5 12h14M12 5l7 7-7 7" />
                  </svg>
                </button>
              </div>
              <p className="mt-2 text-center text-xs" style={{ color: "var(--fg2)" }}>
                Press Enter to send · Shift+Enter for new line · Mic button for voice ({currentLangLabel})
              </p>
            </div>
          </div>
        </main>
      </div>
    </>
  );
}
