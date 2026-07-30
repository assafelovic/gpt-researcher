"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";

type Milestone = {
  id: string;
  title: string;
  status: string;
  summary: string;
};

type RoadmapPayload = {
  provider: string;
  linear_configured: boolean;
  milestones: Milestone[];
  note?: string;
};

const STATUS_STYLE: Record<string, string> = {
  in_progress: "border-teal-400/40 bg-teal-400/10 text-teal-100",
  planned: "border-white/15 bg-white/[0.03] text-slate-200",
  done: "border-emerald-400/40 bg-emerald-400/10 text-emerald-100",
};

export default function RoadmapPanel() {
  const [data, setData] = useState<RoadmapPayload | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch("/api/brain/roadmap");
        if (!res.ok) throw new Error(`Failed to load roadmap (${res.status})`);
        const json = await res.json();
        if (!cancelled) setData(json);
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Load failed");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <section className="mx-auto w-full max-w-5xl px-4 pb-16 pt-6 text-white">
      <header className="mb-8 max-w-2xl">
        <p className="text-xs uppercase tracking-[0.2em] text-indigo-300/80">
          Where we are going
        </p>
        <h2 className="mt-2 font-serif text-3xl tracking-tight sm:text-4xl">
          Roadmap
        </h2>
        <p className="mt-3 text-sm leading-relaxed text-slate-300">
          Linear is the primary source. Productboard stays stubbed until API
          credentials exist.
        </p>
      </header>

      {error && (
        <p className="mb-4 rounded-lg border border-red-400/30 bg-red-500/10 px-3 py-2 text-sm text-red-200">
          {error}
        </p>
      )}

      {data && (
        <>
          <p className="mb-4 text-xs text-slate-500">
            Provider: {data.provider}
            {data.linear_configured ? " · Linear connected" : " · seed milestones"}
          </p>
          <div className="grid gap-4 md:grid-cols-3">
            {data.milestones.map((m, index) => (
              <motion.article
                key={m.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.07 }}
                className={`rounded-2xl border p-5 ${
                  STATUS_STYLE[m.status] || STATUS_STYLE.planned
                }`}
              >
                <p className="text-[10px] font-semibold uppercase tracking-wider opacity-70">
                  {m.status.replace("_", " ")}
                </p>
                <h3 className="mt-2 text-base font-semibold">{m.title}</h3>
                <p className="mt-2 text-sm leading-relaxed opacity-90">
                  {m.summary}
                </p>
              </motion.article>
            ))}
          </div>
          {data.note && (
            <p className="mt-6 text-xs leading-relaxed text-slate-500">{data.note}</p>
          )}
        </>
      )}
    </section>
  );
}
