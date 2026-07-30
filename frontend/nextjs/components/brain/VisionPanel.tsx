"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";

type VisionDoc = {
  id: string;
  filename: string;
  title: string;
  content: string;
  path: string;
};

export default function VisionPanel() {
  const [docs, setDocs] = useState<VisionDoc[]>([]);
  const [activeId, setActiveId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch("/api/brain/vision");
        if (!res.ok) throw new Error(`Failed to load vision (${res.status})`);
        const data = await res.json();
        if (!cancelled) {
          setDocs(data.documents || []);
          if (data.documents?.[0]?.id) setActiveId(data.documents[0].id);
        }
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Load failed");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const active = docs.find((d) => d.id === activeId) || null;

  return (
    <section className="mx-auto w-full max-w-5xl px-4 pb-16 pt-6 text-white">
      <header className="mb-8 max-w-2xl">
        <p className="text-xs uppercase tracking-[0.2em] text-amber-300/80">
          Product brain
        </p>
        <h2 className="mt-2 font-serif text-3xl tracking-tight sm:text-4xl">
          Vision the researcher can cite
        </h2>
        <p className="mt-3 text-sm leading-relaxed text-slate-300">
          These markdown docs live in <code className="text-teal-200">my-docs/vision/</code>{" "}
          and are available to hybrid research. Edit them in the repo to steer answers.
        </p>
      </header>

      {error && (
        <p className="mb-4 rounded-lg border border-red-400/30 bg-red-500/10 px-3 py-2 text-sm text-red-200">
          {error}
        </p>
      )}

      {!error && docs.length === 0 && (
        <p className="text-sm text-slate-400">
          No vision docs found yet. Add markdown under <code>my-docs/vision/</code>.
        </p>
      )}

      <div className="grid gap-6 lg:grid-cols-[220px_1fr]">
        <nav className="flex flex-row gap-2 overflow-x-auto lg:flex-col">
          {docs.map((doc) => (
            <button
              key={doc.id}
              type="button"
              onClick={() => setActiveId(doc.id)}
              className={`whitespace-nowrap rounded-xl border px-3 py-2 text-left text-sm transition ${
                activeId === doc.id
                  ? "border-amber-400/40 bg-amber-400/10 text-white"
                  : "border-white/10 text-slate-400 hover:text-white"
              }`}
            >
              {doc.title}
            </button>
          ))}
        </nav>

        {active && (
          <motion.article
            key={active.id}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="rounded-3xl border border-white/10 bg-white/[0.03] p-6"
          >
            <p className="text-xs text-slate-500">{active.path}</p>
            <pre className="mt-4 whitespace-pre-wrap font-sans text-sm leading-relaxed text-slate-200">
              {active.content}
            </pre>
          </motion.article>
        )}
      </div>
    </section>
  );
}
