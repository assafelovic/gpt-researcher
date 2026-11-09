'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';
import { startResearch } from '@/lib/research/live';
import { checkMcp } from '@/lib/research/mcp';
import { useBackend } from './backend';
import Brief, { type BriefField } from './Brief';
import { FaviconStack } from './Favicon';
import { useLinks, useMock } from './mode';
import { openSettings, useBrief, type SettingsTab } from './preferences';
import { Arrow, Connection } from './ui';
import { useReports } from './useReports';

const suggestions = [
  'Why is Nvidia stock going up?',
  'How close are solid state batteries to mass production?',
  'What does the EU AI Act require from a small startup?',
];

const size = (bytes: number) => (bytes < 1e6 ? `${Math.max(1, Math.round(bytes / 1e3))} KB` : `${(bytes / 1e6).toFixed(1)} MB`);

export default function HomeScreen({
  openField,
  settingsTab,
  initialQuestion = '',
}: {
  openField?: BriefField;
  settingsTab?: SettingsTab;
  initialQuestion?: string;
}) {
  const router = useRouter();
  const mock = useMock();
  const links = useLinks();
  const backend = useBackend();
  const { rows: recent } = useReports();
  const picker = useRef<HTMLInputElement>(null);
  const [question, setQuestion] = useState(initialQuestion);
  const [brief, setBrief] = useBrief();
  const [files, setFiles] = useState<File[]>([]);
  const [dragging, setDragging] = useState(false);
  const [note, setNote] = useState('');
  const [starting, setStarting] = useState(false);
  const [problem, setProblem] = useState('');

  const offline = backend.status === 'offline';
  const mcpBroken = brief.mcp_enabled && checkMcp(brief.mcp_configs).state === 'invalid';
  const canStart = Boolean(question.trim()) && !offline && !starting && !mcpBroken;

  useEffect(() => {
    if (settingsTab) openSettings(settingsTab);
  }, [settingsTab]);

  const addFiles = (list: FileList | null) => {
    const incoming = Array.from(list ?? []);
    if (!incoming.length) return;
    setFiles((current) => [...current, ...incoming.filter((f) => !current.some((c) => c.name === f.name))]);
    if (brief.report_source === 'web') {
      setBrief({ ...brief, report_source: 'hybrid' });
      setNote('Now reading the web and your documents.');
    }
  };

  const start = async () => {
    if (!canStart) return;
    if (mock) return router.push('/mocks/run');
    setStarting(true);
    setProblem('');
    try {
      await Promise.all(files.map(backend.upload));
    } catch (e) {
      setStarting(false);
      return setProblem(e instanceof Error ? e.message : String(e));
    }
    router.push(`/research/${startResearch(question.trim(), brief)}`);
  };

  return (
    <>
      <main className="mx-auto w-full max-w-[860px] px-5 pb-6 pt-[9vh] sm:px-8 sm:pt-[12vh]">
        <h1 className="font-display text-[clamp(2.4rem,4.6vw,4.2rem)] font-semibold leading-[1.04] tracking-[-0.03em]">
          What should we research?
        </h1>

        <form
          className="mt-9"
          onSubmit={(e) => {
            e.preventDefault();
            void start();
          }}
        >
          <div
            onDragOver={(e) => {
              e.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={(e) => {
              e.preventDefault();
              setDragging(false);
              addFiles(e.dataTransfer.files);
            }}
            className={`bg-paper-hi px-5 pb-4 pt-5 transition-shadow focus-within:shadow-[inset_0_0_0_1px_#1A1612] sm:px-6 ${
              dragging ? 'shadow-[inset_0_0_0_1px_#B8381C]' : 'shadow-[inset_0_0_0_1px_rgba(29,25,21,0.26)]'
            }`}
          >
            <label htmlFor="question" className="sr-only">
              Research question
            </label>
            <textarea
              id="question"
              rows={3}
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                  e.preventDefault();
                  void start();
                }
              }}
              placeholder={dragging ? 'Drop files to add them' : 'Ask a question, name a topic, or paste a link'}
              className="gr-input w-full resize-none bg-transparent font-display text-[21px] leading-snug outline-none sm:text-[23px]"
            />
            {files.length > 0 && (
              <ul className="mb-1 mt-2 flex flex-wrap gap-1.5" aria-label="Files to research">
                {files.map((f) => (
                  <li key={f.name} className="inline-flex h-8 max-w-full items-center gap-2 bg-paper pl-3 pr-1 shadow-[inset_0_0_0_1px_rgba(29,25,21,0.14)]">
                    <span className="truncate text-[13px] font-medium">{f.name}</span>
                    <span className="font-code text-[10.5px] text-ink-3">{size(f.size)}</span>
                    <button
                      type="button"
                      onClick={() => setFiles(files.filter((x) => x !== f))}
                      aria-label={`Remove ${f.name}`}
                      className="grid h-6 w-6 place-items-center text-ink-3 hover:text-rubric"
                    >
                      ×
                    </button>
                  </li>
                ))}
              </ul>
            )}
            <div className="mt-3 flex items-center justify-between gap-4">
              <button type="button" className="gr-btn-line" onClick={() => picker.current?.click()}>
                + Add files
              </button>
              <input
                ref={picker}
                type="file"
                multiple
                accept=".pdf,.docx,.doc,.txt,.md,.csv,.xlsx,.pptx,.html"
                className="sr-only"
                tabIndex={-1}
                aria-hidden="true"
                onChange={(e) => {
                  addFiles(e.target.files);
                  e.target.value = '';
                }}
              />
              <div className="flex items-center gap-4">
                <kbd className="hidden font-code text-[11px] text-ink-3 sm:inline">
                  <span className="font-body">⌘</span> Enter
                </kbd>
                <button type="submit" className="gr-btn" disabled={!canStart}>
                  {starting ? (files.length ? 'Uploading' : 'Starting') : 'Research'} <Arrow />
                </button>
              </div>
            </div>
          </div>
          {problem && (
            <p role="alert" className="mt-3 text-[14px] leading-snug text-rubric">
              {problem}
            </p>
          )}
          {offline && (
            <p role="alert" className="mt-3 text-[14px] leading-snug text-rubric">
              Cannot reach the backend at {backend.host || 'localhost:8000'}. Start it with <code className="font-code text-[12.5px]">python main.py</code>, or{' '}
              <button type="button" className="font-medium underline underline-offset-4" onClick={() => openSettings('backend')}>
                change the address in Settings
              </button>
              .
            </p>
          )}
          <div className="mt-5">
            <Brief value={brief} onChange={setBrief} openField={openField} documents={backend.status === 'online' ? backend.documents.length : undefined} />
            <p className="sr-only" role="status">
              {note}
            </p>
          </div>
        </form>

        <section className="mt-16" aria-labelledby="try-h">
          <h2 id="try-h" className="gr-meta border-b border-rule pb-3">
            Try
          </h2>
          <ul>
            {suggestions.map((s) => (
              <li key={s} className="border-b border-rule-soft">
                <button
                  type="button"
                  onClick={() => {
                    setQuestion(s);
                    document.getElementById('question')?.focus();
                  }}
                  className="group flex w-full items-center justify-between gap-4 py-3.5 text-left font-display text-[18px] leading-snug transition-colors hover:text-rubric"
                >
                  {s}
                  <Arrow className="flex-none -translate-x-1 opacity-0 transition-all group-hover:translate-x-0 group-hover:opacity-100" />
                </button>
              </li>
            ))}
          </ul>
        </section>

        {recent.length > 0 && (
        <section className="mt-16" aria-labelledby="recent-h">
          <div className="flex items-baseline justify-between border-b border-ink pb-3">
            <h2 id="recent-h" className="gr-meta">
              Recent reports
            </h2>
            <Link href={links.archive} className="inline-flex items-center gap-2 text-[13.5px] font-medium hover:text-rubric">
              Archive <Arrow />
            </Link>
          </div>
          <ul>
            {recent.slice(0, 3).map((r) => (
              <li key={r.id} className="border-b border-rule-soft">
                <Link href={links.report(r.id)} className="grid grid-cols-[64px_minmax(0,1fr)] items-baseline gap-3 py-3.5 sm:grid-cols-[72px_minmax(0,1fr)_auto] sm:gap-5">
                  <span className="font-code text-[11px] uppercase tracking-[0.1em] text-ink-3">{r.date}</span>
                  <span className="font-display text-[17.5px] font-semibold leading-snug">{r.title}</span>
                  <span className="col-start-2 inline-flex items-center gap-2.5 font-code text-[11px] tabular-nums text-ink-3 sm:col-start-auto sm:self-center">
                    <FaviconStack domains={r.domains} max={3} />
                    {r.type} · {r.words.toLocaleString('en-US')} words
                  </span>
                </Link>
              </li>
            ))}
          </ul>
        </section>
        )}

        <footer className="mt-16 flex flex-wrap items-center justify-between gap-x-6 gap-y-2 border-t border-rule-soft pt-4">
          <p className="text-[12.5px] text-ink-3">GPT Researcher can make mistakes. Check the sources before you rely on a report.</p>
          <Connection />
        </footer>
      </main>
    </>
  );
}
