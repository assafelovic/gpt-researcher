"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";

type CorpusDoc = {
  id: string;
  filename: string;
  title: string;
  content: string;
  path: string;
};

type AudiencePayload = {
  documents: CorpusDoc[];
  recruiting_documents: CorpusDoc[];
  note?: string;
  error?: string;
};

export default function AudiencePanel() {
  const [payload, setPayload] = useState<AudiencePayload | null>(null);
  const [activePath, setActivePath] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch("/api/brain/audience");
        if (!res.ok) throw new Error(`Failed to load audience (${res.status})`);
        const data: AudiencePayload = await res.json();
        if (!cancelled) {
          setPayload(data);
          const first = data.documents?.[0] || data.recruiting_documents?.[0];
          if (first) setActivePath(first.path);
        }
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Load failed");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const allDocs = [
    ...(payload?.documents || []),
    ...(payload?.recruiting_documents || []),
  ];
  const active = allDocs.find((d) => d.path === activePath) || null;

  const groups: { heading: string; docs: CorpusDoc[] }[] = [
    { heading: "Voice of nurses", docs: payload?.documents || [] },
    { heading: "Recruiting inventory", docs: payload?.recruiting_documents || [] },
  ];

  return (
    <section className="mx-auto w-full max-w-5xl px-4 pb-16 pt-6 text-white">
      <header className="mb-8 max-w-2xl">
        <p className="text-xs uppercase tracking-[0.2em] text-rose-300/80">
          Customer discovery
        </p>
        <h2 className="mt-2 font-serif text-3xl tracking-tight sm:text-4xl">
          What nurses actually say
        </h2>
        <p className="mt-3 text-sm leading-relaxed text-slate-300">
          Pain points, verbatim quotes with receipts, and the{" "}
          <code className="text-teal-200">nursingmastery.com</code> content
          inventory. Every Audience- or Recruiting-scoped research run reads
          this corpus; the weekly sweep keeps it fresh.
        </p>
      </header>

      {error && (
        <p className="mb-4 rounded-lg border border-red-400/30 bg-red-500/10 px-3 py-2 text-sm text-red-200">
          {error}
        </p>
      )}

      {!error && allDocs.length === 0 && (
        <p className="text-sm text-slate-400">
          No audience docs yet. Add markdown under <code>my-docs/audience/</code>{" "}
          or run the weekly sweep.
        </p>
      )}

      <div className="grid gap-6 lg:grid-cols-[240px_1fr]">
        <nav className="flex flex-row gap-4 overflow-x-auto lg:flex-col">
          {groups.map(
            (group) =>
              group.docs.length > 0 && (
                <div key={group.heading} className="min-w-[180px]">
                  <p className="mb-2 text-[11px] font-semibold uppercase tracking-[0.14em] text-slate-500">
                    {group.heading}
                  </p>
                  <div className="flex flex-row gap-2 lg:flex-col">
                    {group.docs.map((doc) => (
                      <button
                        key={doc.path}
                        type="button"
                        onClick={() => setActivePath(doc.path)}
                        className={`whitespace-nowrap rounded-xl border px-3 py-2 text-left text-sm transition ${
                          activePath === doc.path
                            ? "border-rose-400/40 bg-rose-400/10 text-white"
                            : "border-white/10 text-slate-400 hover:text-white"
                        }`}
                      >
                        {doc.title}
                      </button>
                    ))}
                  </div>
                </div>
              ),
          )}
        </nav>

        {active && (
          <motion.article
            key={active.path}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="max-h-[70vh] overflow-y-auto rounded-3xl border border-white/10 bg-white/[0.03] p-6"
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
