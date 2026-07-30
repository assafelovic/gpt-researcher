"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";

type RepoCard = {
  slug: string;
  github: string;
  name: string;
  tagline: string;
  capabilities: string[];
  ask_examples: string[];
  codegraph_ready?: boolean;
};

type Props = {
  onAsk: (question: string) => void;
};

export default function CodebaseExplorer({ onAsk }: Props) {
  const [repos, setRepos] = useState<RepoCard[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [question, setQuestion] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const res = await fetch("/api/brain/repos");
        if (!res.ok) throw new Error(`Failed to load repos (${res.status})`);
        const data = await res.json();
        if (!cancelled) {
          setRepos(data.repos || []);
          if (data.repos?.[0]?.slug) setSelected(data.repos[0].slug);
        }
      } catch (err) {
        if (!cancelled) setError(err instanceof Error ? err.message : "Load failed");
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const active = repos.find((r) => r.slug === selected) || null;

  return (
    <section className="mx-auto w-full max-w-5xl px-4 pb-16 pt-6 text-white">
      <header className="mb-8 max-w-2xl">
        <p className="text-xs uppercase tracking-[0.2em] text-teal-300/80">
          Estate map
        </p>
        <h2 className="mt-2 font-serif text-3xl tracking-tight text-white sm:text-4xl">
          Codebases your team can ask about
        </h2>
        <p className="mt-3 text-sm leading-relaxed text-slate-300">
          Pick a repo, skim what it can do, then ask “can we do X?” — research
          routes through the code graph when it is configured.
        </p>
      </header>

      {error && (
        <p className="mb-4 rounded-lg border border-red-400/30 bg-red-500/10 px-3 py-2 text-sm text-red-200">
          {error}
        </p>
      )}

      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
        {repos.map((repo, index) => (
          <motion.button
            key={repo.slug}
            type="button"
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.05 }}
            onClick={() => setSelected(repo.slug)}
            className={`rounded-2xl border p-4 text-left transition ${
              selected === repo.slug
                ? "border-teal-400/50 bg-teal-400/10"
                : "border-white/10 bg-white/[0.03] hover:border-white/25"
            }`}
          >
            <div className="flex items-start justify-between gap-2">
              <h3 className="text-base font-semibold text-white">{repo.name}</h3>
              {repo.codegraph_ready ? (
                <span className="rounded-md bg-teal-500/20 px-1.5 py-0.5 text-[10px] font-medium text-teal-200">
                  graph
                </span>
              ) : null}
            </div>
            <p className="mt-2 text-xs leading-relaxed text-slate-400">
              {repo.tagline}
            </p>
          </motion.button>
        ))}
      </div>

      {active && (
        <motion.div
          key={active.slug}
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          className="mt-8 rounded-3xl border border-white/10 bg-gradient-to-br from-white/[0.06] to-transparent p-6"
        >
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <h3 className="text-xl font-semibold">{active.name}</h3>
            <span className="text-xs text-slate-500">{active.github}</span>
          </div>
          <ul className="mt-4 space-y-2 text-sm text-slate-300">
            {active.capabilities.map((cap) => (
              <li key={cap} className="flex gap-2">
                <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-teal-400" />
                {cap}
              </li>
            ))}
          </ul>

          <div className="mt-6 flex flex-wrap gap-2">
            {active.ask_examples.map((example) => (
              <button
                key={example}
                type="button"
                onClick={() => {
                  setQuestion(example);
                  onAsk(
                    `Regarding ${active.name} (${active.github}): ${example}`,
                  );
                }}
                className="rounded-full border border-white/15 px-3 py-1.5 text-xs text-slate-300 transition hover:border-teal-400/40 hover:text-white"
              >
                {example}
              </button>
            ))}
          </div>

          <form
            className="mt-6 flex flex-col gap-3 sm:flex-row"
            onSubmit={(e) => {
              e.preventDefault();
              const q = question.trim();
              if (!q) return;
              onAsk(`Regarding ${active.name} (${active.github}): ${q}`);
            }}
          >
            <input
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder={`Can ${active.name} … ?`}
              className="flex-1 rounded-xl border border-white/15 bg-black/30 px-4 py-3 text-sm text-white outline-none ring-teal-400/40 placeholder:text-slate-500 focus:ring-2"
            />
            <button
              type="submit"
              className="rounded-xl bg-[#155EEF] px-5 py-3 text-sm font-semibold text-white transition hover:bg-[#0E49C9]"
            >
              Ask with Code scope
            </button>
          </form>
        </motion.div>
      )}
    </section>
  );
}
