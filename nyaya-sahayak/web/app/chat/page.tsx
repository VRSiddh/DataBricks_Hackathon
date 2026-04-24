"use client";

import Link from "next/link";
import { useCallback, useRef, useState } from "react";
import { getApiBase } from "@/lib/apiBase";
import { LANGUAGES } from "@/lib/languages";
import { setTheme } from "@/components/ThemeInit";

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

export default function ChatPage() {
  const base = getApiBase();
  const [lang, setLang] = useState("hi-IN");
  const [busy, setBusy] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [docPreview, setDocPreview] = useState<string | null>(null);
  const [messages, setMessages] = useState<Msg[]>([]);
  const [followUp, setFollowUp] = useState("");
  const [error, setError] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);
  const endRef = useRef<HTMLDivElement>(null);

  const scrollEnd = useCallback(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  const analyze = async (file: File) => {
    setError(null);
    setBusy(true);
    setMessages((m) => [...m, { role: "user", text: "Uploaded document for analysis.", file: file.name }]);
    try {
      const fd = new FormData();
      fd.append("file", file);
      fd.append("language", lang);
      const r = await fetch(`${base}/api/analyze_upload`, {
        method: "POST",
        body: fd,
      });
      const text = await r.text();
      if (!r.ok) throw new Error(text || r.statusText);
      const data = JSON.parse(text) as {
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
      setError("File too large (max 5MB images, 8MB PDF).");
      return;
    }
    void analyze(f);
  };

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
      const text = await r.text();
      if (!r.ok) throw new Error(text);
      const data = JSON.parse(text) as { reply: string };
      setMessages((m) => [...m, { role: "assistant", text: data.reply }]);
    } catch (e) {
      setError(String(e));
      setMessages((m) => [...m, { role: "assistant", text: `Error: ${e}` }]);
    } finally {
      setBusy(false);
      scrollEnd();
    }
  };

  return (
    <div className="mx-auto flex min-h-dvh max-w-3xl flex-col px-4 pb-4 pt-4 sm:px-5">
      <header className="mb-3 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <Link href="/" className="text-sm font-semibold text-teal-800 underline-offset-2 hover:underline dark:text-teal-200">
            ← Home
          </Link>
        </div>
        <div className="flex items-center gap-1">
          <button
            type="button"
            className="rounded-lg border border-slate-300 px-2 py-1.5 text-xs font-medium dark:border-slate-600"
            onClick={() => {
              const d = !document.documentElement.classList.contains("dark");
              setTheme(d);
            }}
          >
            Theme
          </button>
        </div>
      </header>

      <div className="mb-3">
        <label className="text-xs font-medium text-slate-500 dark:text-slate-400">Response language</label>
        <select
          className="mt-1 w-full rounded-xl border border-slate-200 bg-white/80 px-3 py-2.5 text-sm dark:border-slate-700 dark:bg-slate-900/80"
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

      <input ref={fileRef} type="file" accept=".pdf,image/*" className="hidden" onChange={onFile} />

      <button
        type="button"
        disabled={busy}
        onClick={() => fileRef.current?.click()}
        className="glass mb-3 flex w-full items-center justify-between gap-3 p-4 text-left transition active:scale-[0.99] disabled:opacity-60"
      >
        <div>
          <p className="font-bold">{busy ? "Processing…" : "Upload FIR / notice / scan / PDF"}</p>
          <p className="text-xs text-slate-500 dark:text-slate-400">PDF (≤10 pages) or clear image · 5MB image / 8MB PDF</p>
        </div>
        <span className="text-xl">⬆</span>
      </button>

      {error && <p className="mb-2 rounded-lg bg-red-100 px-3 py-2 text-sm text-red-900 dark:bg-red-950/50 dark:text-red-200">{error}</p>}

      <div className="min-h-0 flex-1 space-y-2 overflow-y-auto rounded-2xl border border-slate-200/80 p-3 dark:border-slate-700/80">
        {messages.length === 0 && !busy && (
          <p className="text-center text-sm text-slate-500">Upload a document to begin, or add a follow-up after the first reply.</p>
        )}
        {messages.map((m, i) => (
          <div
            key={i}
            className={`max-w-[95%] rounded-2xl border px-3 py-2 text-sm leading-relaxed ${
              m.role === "user"
                ? "ml-auto border-teal-200 bg-teal-50/80 dark:border-teal-800 dark:bg-teal-950/40"
                : "mr-auto border-slate-200 bg-white/70 dark:border-slate-700 dark:bg-slate-900/60"
            }`}
          >
            {m.file && <p className="mb-1 text-xs font-semibold text-slate-500">📎 {m.file}</p>}
            <p className="whitespace-pre-wrap">{m.text}</p>
          </div>
        ))}
        {busy && (
          <div className="animate-pulse space-y-2 p-2">
            <div className="h-3 rounded bg-slate-200/80 dark:bg-slate-700" />
            <div className="h-3 rounded bg-slate-200/60 dark:bg-slate-800" />
            <div className="h-3 w-2/3 rounded bg-slate-200/50 dark:bg-slate-800" />
          </div>
        )}
        <div ref={endRef} />
      </div>

      <div className="mt-3 flex gap-2">
        <input
          className="flex-1 rounded-2xl border border-slate-200 bg-white/90 px-3 py-2.5 text-sm dark:border-slate-700 dark:bg-slate-900/90"
          placeholder="Follow-up (after first analysis)…"
          value={followUp}
          onChange={(e) => setFollowUp(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && !e.shiftKey && (e.preventDefault(), void sendChat())}
          disabled={!sessionId || busy}
        />
        <button
          type="button"
          onClick={() => void sendChat()}
          disabled={!sessionId || busy}
          className="rounded-2xl bg-teal-700 px-4 py-2.5 text-sm font-bold text-white disabled:opacity-50 dark:bg-teal-500"
        >
          Send
        </button>
      </div>
    </div>
  );
}
