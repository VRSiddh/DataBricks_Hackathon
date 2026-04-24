import Link from "next/link";

export default function HomePage() {
  return (
    <main className="mx-auto min-h-dvh max-w-3xl px-5 py-10">
      <header className="mb-10 text-center sm:text-left">
        <h1 className="text-3xl font-extrabold tracking-tight sm:text-4xl">Nyaya-Sahayak</h1>
        <p className="mt-2 text-lg text-teal-800 dark:text-teal-200">न्याय सहायक · BNS-aware legal assistant</p>
        <p className="mt-4 text-balance text-slate-600 dark:text-slate-300">
          One interface for everyone — from a first-time complainant to a busy practitioner. Upload a document, pick
          your language, and get guidance grounded in the Bharatiya Nyaya Sanhita (BNS) corpus (via Databricks Vector
          Search when configured).
        </p>
      </header>

      <div className="space-y-4">
        {[
          {
            t: "Grounded answers",
            d: "RAG over your BNS chunks with similarity search, plus IPC→BNS hints where available.",
          },
          { t: "Indic-first", d: "Sarvam Mayura + Bulbul (when API keys are set) for translation and TTS." },
          {
            t: "Honest by design",
            d: "The model is instructed to refuse when the text is unusable or off-topic for Indian criminal law.",
          },
        ].map((x) => (
          <section key={x.t} className="glass p-5">
            <h2 className="text-lg font-bold">{x.t}</h2>
            <p className="mt-1 text-slate-600 dark:text-slate-400">{x.d}</p>
          </section>
        ))}
      </div>

      <div className="mt-10 flex flex-col items-stretch gap-3 sm:flex-row sm:items-center">
        <Link
          className="inline-flex items-center justify-center rounded-xl bg-teal-700 px-5 py-3.5 text-center text-sm font-bold text-white shadow-md transition hover:bg-teal-800 dark:bg-teal-500 dark:hover:bg-teal-400"
          href="/chat/"
        >
          Open assistant
        </Link>
        <a
          className="text-center text-sm text-teal-800 underline-offset-2 hover:underline dark:text-teal-200"
          href="/docs"
        >
          API docs
        </a>
        <a
          className="text-center text-sm text-slate-500 dark:text-slate-400"
          href="/api/health"
        >
          /api/health
        </a>
      </div>

      <p className="mt-8 text-xs text-slate-500 dark:text-slate-500">
        Prototype for hackathon / education — not a substitute for professional legal advice.
      </p>
    </main>
  );
}
