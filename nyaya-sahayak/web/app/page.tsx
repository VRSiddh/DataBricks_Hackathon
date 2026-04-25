import Link from "next/link";
import ThemeToggle from "@/components/ThemeToggle";
import { LANGUAGES } from "@/lib/languages";
import { ThemeInit } from "@/components/ThemeInit";

const CTA_HREF = "/login/";

const features = [
  {
    icon: (
      <svg className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="1.8" viewBox="0 0 24 24">
        <path d="M12 3L2 7l10 4 10-4-10-4z" />
        <path d="M2 17l10 4 10-4" />
        <path d="M2 12l10 4 10-4" />
      </svg>
    ),
    title: "RAG-grounded answers",
    desc: "Every response is retrieved from your BNS corpus via Databricks Vector Search — not hallucinated. IPC→BNS cross-references included.",
  },
  {
    icon: (
      <svg className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="1.8" viewBox="0 0 24 24">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
      </svg>
    ),
    title: "11 Indian languages",
    desc: "Speak or type in Hindi, Tamil, Telugu, Marathi, Kannada, Bengali, Gujarati, Punjabi, Malayalam, Odia, or English.",
  },
  {
    icon: (
      <svg className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="1.8" viewBox="0 0 24 24">
        <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
        <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
        <line x1="12" y1="19" x2="12" y2="23" />
        <line x1="8" y1="23" x2="16" y2="23" />
      </svg>
    ),
    title: "Voice input",
    desc: "Speak your question directly in your language. Browser-native multilingual speech recognition — no third-party required.",
  },
  {
    icon: (
      <svg className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="1.8" viewBox="0 0 24 24">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <polyline points="14,2 14,8 20,8" />
        <line x1="16" y1="13" x2="8" y2="13" />
        <line x1="16" y1="17" x2="8" y2="17" />
        <polyline points="10,9 9,9 8,9" />
      </svg>
    ),
    title: "Document analysis",
    desc: "Upload FIRs, police notices, legal orders, or scanned documents (PDF / image). OCR extracts text; the model identifies applicable BNS sections.",
  },
  {
    icon: (
      <svg className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="1.8" viewBox="0 0 24 24">
        <circle cx="12" cy="12" r="10" />
        <polyline points="12,6 12,12 16,14" />
      </svg>
    ),
    title: "Persona-aware",
    desc: "Automatically adapts tone for a first-time complainant, a law student, or a practitioner — via an LLM persona router.",
  },
  {
    icon: (
      <svg className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="1.8" viewBox="0 0 24 24">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      </svg>
    ),
    title: "Honest by design",
    desc: "The model refuses off-topic or unreadable inputs. Responses cite BNS sections and remind users to consult a qualified advocate.",
  },
];

export default function HomePage() {
  return (
    <>
      <ThemeInit />
      <div className="flex min-h-dvh flex-col">
        {/* ── Navbar ─────────────────────────────────────────────── */}
        <nav className="glass-nav sticky top-0 z-50">
          <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-5">
            <div className="flex items-center gap-3">
              <div
                className="flex h-8 w-8 items-center justify-center rounded-lg text-white text-sm font-bold"
                style={{ background: "var(--user-grad)" }}
              >
                ⚖
              </div>
              <span className="font-bold tracking-tight">Nyaya-Sahayak</span>
              <span
                className="hidden rounded-full px-2 py-0.5 text-xs font-medium sm:inline"
                style={{ background: "var(--glow)", color: "var(--accent)" }}
              >
                Beta
              </span>
            </div>
            <div className="flex items-center gap-3">
              <a
                href="/api/health"
                className="hidden text-sm sm:block"
                style={{ color: "var(--fg2)" }}
              >
                Status
              </a>
              <ThemeToggle />
              <Link
                href="/chat/"
                className="btn-accent px-4 py-2 text-sm"
              >
                Open App
                <svg className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                  <path d="M5 12h14M12 5l7 7-7 7" />
                </svg>
              </Link>
            </div>
          </div>
        </nav>

        {/* ── Hero ────────────────────────────────────────────────── */}
        <section className="relative flex flex-1 flex-col items-center justify-center overflow-hidden px-5 py-24 text-center">
          {/* Background orbs */}
          <div
            className="orb-float pointer-events-none absolute left-1/2 top-0 h-[600px] w-[600px] -translate-x-1/2 -translate-y-1/4 rounded-full opacity-30"
            style={{
              background:
                "radial-gradient(circle, rgba(20,184,166,0.15) 0%, transparent 70%)",
            }}
          />

          <div className="relative z-10 mx-auto max-w-4xl">
            <div
              className="mb-6 inline-flex items-center gap-2 rounded-full border px-4 py-1.5 text-xs font-semibold uppercase tracking-widest"
              style={{ borderColor: "var(--border)", color: "var(--accent)" }}
            >
              <span
                className="h-1.5 w-1.5 rounded-full"
                style={{ background: "var(--accent)" }}
              />
              Bharatiya Nyaya Sanhita · BNS 2023
            </div>

            <h1 className="text-5xl font-black leading-[1.08] tracking-tight sm:text-6xl md:text-7xl">
              Legal guidance
              <br />
              <span className="gradient-text">in your language</span>
            </h1>

            <p
              className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed sm:text-xl"
              style={{ color: "var(--fg2)" }}
            >
              Upload a FIR, court notice, or scanned document and get plain-language advice
              grounded in Indian law — powered by Databricks Vector Search and large language models.
            </p>

            <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row sm:justify-center">
              <Link href="/chat/" className="btn-accent px-8 py-4 text-base">
                Start for free
                <svg className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                  <path d="M5 12h14M12 5l7 7-7 7" />
                </svg>
              </Link>
              <a
                href="/api/health"
                className="btn-ghost px-6 py-4 text-base"
              >
                Check status
              </a>
            </div>

            <p className="mt-6 text-xs" style={{ color: "var(--fg2)" }}>
              Not a substitute for professional legal advice · Hackathon prototype
            </p>
          </div>
        </section>

        {/* ── Features grid ───────────────────────────────────────── */}
        <section className="mx-auto w-full max-w-7xl px-5 pb-24">
          <div className="mb-12 text-center">
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">
              Everything you need
            </h2>
            <p className="mt-3" style={{ color: "var(--fg2)" }}>
              Built on Databricks · Sarvam AI · Llama 3
            </p>
          </div>

          <div className="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {features.map((f) => (
              <div key={f.title} className="feature-card">
                <div
                  className="mb-4 flex h-12 w-12 items-center justify-center rounded-xl"
                  style={{ background: "var(--glow)", color: "var(--accent)" }}
                >
                  {f.icon}
                </div>
                <h3 className="mb-2 text-lg font-bold">{f.title}</h3>
                <p className="text-sm leading-relaxed" style={{ color: "var(--fg2)" }}>
                  {f.desc}
                </p>
              </div>
            ))}
          </div>
        </section>

        {/* ── Language strip ──────────────────────────────────────── */}
        <section
          className="border-y py-12"
          style={{ borderColor: "var(--border)" }}
        >
          <div className="mx-auto max-w-7xl px-5">
            <p
              className="mb-6 text-center text-sm font-semibold uppercase tracking-widest"
              style={{ color: "var(--fg2)" }}
            >
              Supports {LANGUAGES.length} Indian languages
            </p>
            <div className="flex flex-wrap justify-center gap-2">
              {LANGUAGES.map((l) => (
                <span
                  key={l.code}
                  className="rounded-full border px-4 py-1.5 text-sm font-medium"
                  style={{
                    borderColor: "var(--border)",
                    color: "var(--fg)",
                    background: "var(--card2)",
                  }}
                >
                  {l.label}
                </span>
              ))}
            </div>
          </div>
        </section>

        {/* ── How it works ────────────────────────────────────────── */}
        <section className="mx-auto w-full max-w-7xl px-5 py-24">
          <div className="mb-12 text-center">
            <h2 className="text-3xl font-bold tracking-tight sm:text-4xl">How it works</h2>
          </div>
          <div className="grid gap-8 sm:grid-cols-3">
            {[
              { n: "1", t: "Upload or ask", d: "Drop in a PDF / image of your document, or just type / speak your question." },
              { n: "2", t: "RAG retrieval", d: "Databricks Vector Search finds the most relevant BNS sections from the indexed corpus." },
              { n: "3", t: "Guided answer", d: "The LLM synthesizes a plain-language response with section citations and next steps." },
            ].map((s) => (
              <div key={s.n} className="flex flex-col items-center text-center">
                <div
                  className="mb-5 flex h-14 w-14 items-center justify-center rounded-full text-xl font-black text-white"
                  style={{ background: "var(--user-grad)", boxShadow: "0 4px 20px var(--glow)" }}
                >
                  {s.n}
                </div>
                <h3 className="mb-2 text-lg font-bold">{s.t}</h3>
                <p className="text-sm leading-relaxed" style={{ color: "var(--fg2)" }}>
                  {s.d}
                </p>
              </div>
            ))}
          </div>
        </section>

        {/* ── CTA banner ──────────────────────────────────────────── */}
        <section className="mx-auto w-full max-w-7xl px-5 pb-24">
          <div
            className="glass relative overflow-hidden rounded-3xl p-10 text-center"
            style={{
              background:
                "linear-gradient(135deg, rgba(15,118,110,0.12) 0%, rgba(20,184,166,0.06) 100%)",
              borderColor: "var(--accent)",
            }}
          >
            <div
              className="pointer-events-none absolute inset-0 rounded-3xl"
              style={{
                background:
                  "radial-gradient(ellipse 60% 80% at 50% 50%, var(--glow), transparent)",
              }}
            />
            <h2 className="relative text-3xl font-black tracking-tight sm:text-4xl">
              Ready to get started?
            </h2>
            <p className="relative mt-3 text-lg" style={{ color: "var(--fg2)" }}>
              Open the assistant — no login required.
            </p>
            <Link href="/chat/" className="btn-accent relative mt-8 inline-flex px-10 py-4 text-base">
              Open Nyaya-Sahayak
              <svg className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                <path d="M5 12h14M12 5l7 7-7 7" />
              </svg>
            </Link>
          </div>
        </section>

        {/* ── Footer ──────────────────────────────────────────────── */}
        <footer
          className="border-t py-8 text-center text-xs"
          style={{ borderColor: "var(--border)", color: "var(--fg2)" }}
        >
          <p>
            Nyaya-Sahayak · Built at IIT Madras Databricks Hackathon ·{" "}
            <span>Prototype — not legal advice</span>
          </p>
        </footer>
      </div>
    </>
  );
}
