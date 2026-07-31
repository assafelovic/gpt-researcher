"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";

type LibraryReport = {
  id: string;
  question: string;
  date: string | null;
  snippet: string;
  score?: number;
};

type LibraryPayload = {
  reports: LibraryReport[];
  query: string | null;
  total: number;
  error?: string;
};

export default function LibraryPanel() {
  const [payload, setPayload] = useState<LibraryPayload | null>(null);
  const [query, setQuery] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const load = useCallback(async (q: string) => {
    setLoading(true);
    try {
      const url = q
        ? `/api/brain/library?q=${encodeURIComponent(q)}`
        : "/api/brain/library";
      const res = await fetch(url);
      if (!res.ok) throw new Error(`Failed to load library (${res.status})`);
      setPayload(await res.json());
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Load failed");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load("");
  }, [load]);

  const handleQueryChange = (value: string) => {
    setQuery(value);
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => void load(value.trim()), 350);
  };

  const reports = payload?.reports || [];

  return (
    <section className="mx-auto w-full max-w-4xl px-4 pb-16 pt-6 text-white">
      <header className="mb-6 max-w-2xl">
        <p className="text-xs uppercase tracking-[0.2em] text-sky-300/80">
          Research memory
        </p>
        <h2 className="mt-2 font-serif text-3xl tracking-tight sm:text-4xl">
          Library — knowledge that compounds
        </h2>
        <p className="mt-3 text-sm leading-relaxed text-slate-300">
          Every finished research run lands here. New runs automatically
          consult related past reports, so we build on what we already learned
          instead of restarting.
        </p>
      </header>

      <div className="mb-6">
        <input
          type="search"
          value={query}
          onChange={(event) => handleQueryChange(event.target.value)}
          placeholder="Search past research — e.g. recruiting channels, pay transparency…"
          className="w-full rounded-xl border border-white/10 bg-white/[0.04] px-4 py-3 text-sm text-white placeholder:text-slate-500 focus:border-sky-400/50 focus:outline-none"
        />
      </div>

      {error && (
        <p className="mb-4 rounded-lg border border-red-400/30 bg-red-500/10 px-3 py-2 text-sm text-red-200">
          {error}
        </p>
      )}

      {!error && !loading && reports.length === 0 && (
        <p className="text-sm text-slate-400">
          {payload?.query
            ? "No past research matches that search."
            : "No research runs saved yet. Finished reports appear here automatically."}
        </p>
      )}

      <div className="space-y-3">
        {reports.map((report, index) => (
          <motion.div
            key={report.id}
            initial={{ opacity: 0, y: 6 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: Math.min(index * 0.03, 0.3) }}
          >
            <Link
              href={`/research/${report.id}`}
              className="block rounded-2xl border border-white/10 bg-white/[0.03] p-4 transition hover:border-sky-400/40 hover:bg-sky-400/5"
            >
              <div className="flex items-baseline justify-between gap-3">
                <h3 className="text-sm font-semibold text-white">
                  {report.question || "Untitled research"}
                </h3>
                {report.date && (
                  <span className="shrink-0 text-xs tabular-nums text-slate-500">
                    {report.date}
                  </span>
                )}
              </div>
              {report.snippet && (
                <p className="mt-2 line-clamp-2 text-xs leading-5 text-slate-400">
                  {report.snippet}
                </p>
              )}
            </Link>
          </motion.div>
        ))}
      </div>

      {payload && payload.total > reports.length && !payload.query && (
        <p className="mt-4 text-center text-xs text-slate-500">
          Showing {reports.length} of {payload.total} saved runs — search to
          find older ones.
        </p>
      )}
    </section>
  );
}
