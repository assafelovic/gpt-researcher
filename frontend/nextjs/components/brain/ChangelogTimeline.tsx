"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";

type Entry = {
  id: string;
  date: string;
  title: string;
  summary: string;
  repos: string[];
  kind: string;
};

const KIND_COLOR: Record<string, string> = {
  platform: "bg-sky-500/20 text-sky-200 border-sky-400/30",
  product: "bg-teal-500/20 text-teal-200 border-teal-400/30",
  infrastructure: "bg-violet-500/20 text-violet-200 border-violet-400/30",
};

/**
 * Interactive changelog timeline.
 * Inspired by public 21st changelog patterns (carousel / sticky scroll) —
 * inlined for Mastery Brain theming.
 */
export default function ChangelogTimeline() {
  const [entries, setEntries] = useState<Entry[]>([]);
  const [active, setActive] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch("/api/brain/changelog");
        if (!res.ok) throw new Error(`Failed to load changelog (${res.status})`);
        const data = await res.json();
        if (!cancelled) {
          setEntries(data.entries || []);
          if (data.entries?.[0]?.id) setActive(data.entries[0].id);
        }
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Load failed");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const selected = entries.find((e) => e.id === active) || null;

  return (
    <section className="mx-auto w-full max-w-5xl px-4 pb-16 pt-6 text-white">
      <header className="mb-8 max-w-2xl">
        <p className="text-xs uppercase tracking-[0.2em] text-sky-300/80">
          What shipped
        </p>
        <h2 className="mt-2 font-serif text-3xl tracking-tight sm:text-4xl">
          Interactive changelog
        </h2>
        <p className="mt-3 text-sm leading-relaxed text-slate-300">
          Plain-English releases across the estate. Select an entry to expand
          details — Hermes and Linear can enrich this feed over time.
        </p>
      </header>

      {error && (
        <p className="mb-4 rounded-lg border border-red-400/30 bg-red-500/10 px-3 py-2 text-sm text-red-200">
          {error}
        </p>
      )}

      <div className="relative">
        <div className="absolute bottom-0 left-[11px] top-2 w-px bg-gradient-to-b from-teal-400/50 via-white/10 to-transparent" />
        <ul className="space-y-4">
          {entries.map((entry, index) => {
            const isOpen = entry.id === active;
            return (
              <motion.li
                key={entry.id}
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.06 }}
                className="relative pl-10"
              >
                <button
                  type="button"
                  onClick={() => setActive(isOpen ? null : entry.id)}
                  className="absolute left-0 top-2 flex h-6 w-6 items-center justify-center rounded-full border border-teal-400/40 bg-[#06101C]"
                  aria-expanded={isOpen}
                >
                  <span className="h-2 w-2 rounded-full bg-teal-400" />
                </button>
                <button
                  type="button"
                  onClick={() => setActive(isOpen ? null : entry.id)}
                  className={`w-full rounded-2xl border p-4 text-left transition ${
                    isOpen
                      ? "border-white/20 bg-white/[0.06]"
                      : "border-white/10 bg-white/[0.02] hover:border-white/20"
                  }`}
                >
                  <div className="flex flex-wrap items-center gap-2">
                    <time className="text-xs text-slate-500">{entry.date}</time>
                    <span
                      className={`rounded-md border px-1.5 py-0.5 text-[10px] font-medium uppercase tracking-wide ${
                        KIND_COLOR[entry.kind] || KIND_COLOR.product
                      }`}
                    >
                      {entry.kind}
                    </span>
                  </div>
                  <h3 className="mt-2 text-base font-semibold">{entry.title}</h3>
                  {isOpen && (
                    <motion.div
                      initial={{ opacity: 0, height: 0 }}
                      animate={{ opacity: 1, height: "auto" }}
                      className="mt-3"
                    >
                      <p className="text-sm leading-relaxed text-slate-300">
                        {entry.summary}
                      </p>
                      <div className="mt-3 flex flex-wrap gap-1.5">
                        {entry.repos.map((repo) => (
                          <span
                            key={repo}
                            className="rounded-full border border-white/10 px-2 py-0.5 text-[11px] text-slate-400"
                          >
                            {repo}
                          </span>
                        ))}
                      </div>
                    </motion.div>
                  )}
                </button>
              </motion.li>
            );
          })}
        </ul>
      </div>

      {selected && (
        <p className="mt-6 text-xs text-slate-500">
          Showing detail for {selected.title}
        </p>
      )}
    </section>
  );
}
