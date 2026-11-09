'use client';

import { useEffect, useId, useRef, useState, useSyncExternalStore } from 'react';
import type { RunState } from '@/lib/research/run';
import { ChatComposer, ChatThread, useChat, type Chat, type ChatMessage } from './Chat';
import { copyText } from './clipboard';
import { FaviconStack, domainsBySources } from './Favicon';
import Lightbox from './Lightbox';
import { popoverPanel, usePopover } from './popover';
import Sheet, { readingMinutes, useCitedHtml, useReportHtml, type Heading } from './Sheet';
import Sources, { sourcesSummary } from './Sources';
import { StageList, StageStrip, stageTime, statusWord } from './Stages';
import { clock } from './ui';

export type Tab = 'sources' | 'chat';

const WIDE = '(min-width: 1200px)';

function useWide() {
  return useSyncExternalStore(
    (onChange) => {
      const query = window.matchMedia(WIDE);
      query.addEventListener('change', onChange);
      return () => query.removeEventListener('change', onChange);
    },
    () => window.matchMedia(WIDE).matches,
    () => true,
  );
}

const Chevron = ({ open }: { open: boolean }) => (
  <svg viewBox="0 0 12 12" width="10" height="10" fill="none" stroke="currentColor" strokeWidth="1.5" aria-hidden="true" className={`transition-transform ${open ? 'rotate-180' : ''}`}>
    <path d="M2.5 4.5 6 8l3.5-3.5" />
  </svg>
);

function Receipt({ run }: { run: RunState }) {
  const sites = new Set(run.sources.map((s) => s.domain)).size;
  const rows: [string, string][] = [
    ['Reading time', `${readingMinutes(run.words)} min`],
    ['Questions', String(run.subqueries.length)],
    ['Pages read', String(run.pagesScraped)],
    ...(run.images.length ? ([['Figures', String(run.images.length)]] as [string, string][]) : []),
    ...(run.cost ? ([['Cost', `$${run.cost.toFixed(3)}`]] as [string, string][]) : []),
    ...(run.agent ? ([['Agent', run.agent]] as [string, string][]) : []),
  ];
  const timed = run.stages.flatMap((s) => (s.startedAt !== undefined && s.endedAt !== undefined && s.endedAt > s.startedAt ? [{ ...s, took: s.endedAt - s.startedAt }] : []));
  const longest = Math.max(...timed.map((s) => s.took));
  return (
    <div>
      <div className="grid grid-cols-2 gap-3 border-b border-rule-soft pb-4">
        <p>
          <span className="block font-code text-[26px] font-medium leading-none tabular-nums tracking-[-0.03em]">{run.words.toLocaleString('en-US')}</span>
          <span className="mt-2 block font-code text-[10.5px] uppercase tracking-[0.14em] text-ink-3">Words</span>
        </p>
        <p>
          <span className="block font-code text-[26px] font-medium leading-none tabular-nums tracking-[-0.03em]">{run.elapsed > 0 ? clock(run.elapsed) : '–'}</span>
          <span className="mt-2 block font-code text-[10.5px] uppercase tracking-[0.14em] text-ink-3">Run time</span>
        </p>
      </div>
      <div className="flex items-center gap-3 border-b border-rule-soft py-3">
        <FaviconStack domains={domainsBySources(run.sources)} max={4} />
        <span className="text-[13px] leading-snug text-ink-2">
          {run.sources.length} sources from {sites} sites
        </span>
      </div>
      <dl>
        {rows.map(([k, v]) => (
          <div key={k} className="flex items-baseline justify-between gap-3 border-b border-rule-soft py-2">
            <dt className="font-code text-[10.5px] uppercase tracking-[0.14em] text-ink-3">{k}</dt>
            <dd className="truncate text-right text-[13.5px] font-medium tabular-nums">{v}</dd>
          </div>
        ))}
      </dl>
      {timed.length > 0 && (
        <div className="mt-4">
          <p className="font-code text-[10.5px] uppercase tracking-[0.14em] text-ink-3">Time per stage</p>
          <ol className="mt-2.5 space-y-1.5" aria-label="Time per stage">
            {timed.map((s) => (
              <li key={s.id} className="grid grid-cols-[52px_minmax(0,1fr)_34px] items-center gap-2.5 font-code text-[10.5px] uppercase tracking-[0.08em]">
                <span className="text-ink-2">{s.label}</span>
                <i className="block h-[5px] bg-rule-soft" aria-hidden="true">
                  <i className="block h-full bg-ink" style={{ width: `${Math.max(3, (s.took / longest) * 100)}%` }} />
                </i>
                <span className="text-right tabular-nums text-ink-3">{stageTime(s, run.elapsed)}</span>
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  );
}

/** Keeps the browser tab honest about the run, so it can be watched from another tab. */
function useTabTitle(run: RunState) {
  useEffect(() => {
    const before = document.title;
    return () => {
      document.title = before;
    };
  }, []);

  const title = run.report.match(/^#\s+(.+)$/m)?.[1]?.trim();
  useEffect(() => {
    document.title = run.status === 'done' && title ? `${title} · GPT Researcher` : `${statusWord[run.status]} · ${run.query}`;
  }, [run.status, run.query, title]);
}

function Contents({ headings, addenda, onNavigate }: { headings: Heading[]; addenda: number; onNavigate?: () => void }) {
  const items = headings.filter((h) => h.id !== 's-references' && !/^table of contents$/i.test(h.text));
  const link = 'group grid grid-cols-[24px_minmax(0,1fr)] gap-1 py-[7px] text-[13.5px] leading-snug text-ink-2 transition-colors hover:text-ink';
  return (
    <nav aria-label="Report contents">
      <p className="gr-meta border-b border-ink pb-3">Contents</p>
      <ol className="mt-1">
        {items.map((h, i) => (
          <li key={h.id}>
            <a href={`#${h.id}`} onClick={onNavigate} className={link}>
              <span className="pt-px font-code text-[10.5px] text-ink-3 group-hover:text-rubric">{String(i + 1).padStart(2, '0')}</span>
              <span>{h.text}</span>
            </a>
          </li>
        ))}
        {addenda > 0 && (
          <li>
            <a href="#follow-ups" onClick={onNavigate} className={link}>
              <span className="pt-px font-code text-[10.5px] text-rubric">+</span>
              <span>
                {addenda} follow up{addenda === 1 ? '' : 's'}
              </span>
            </a>
          </li>
        )}
      </ol>
    </nav>
  );
}

const SidebarIcon = () => (
  <svg viewBox="0 0 16 16" width="15" height="15" fill="none" stroke="currentColor" strokeWidth="1.4" aria-hidden="true">
    <rect x="1.75" y="2.75" width="12.5" height="10.5" />
    <path d="M6 2.75v10.5" />
  </svg>
);

/** While the research runs, progress is one line; the stage by stage view opens from it. */
function Progress({ run }: { run: RunState }) {
  const { open, setOpen, root } = usePopover<HTMLDivElement>();
  const id = useId();
  return (
    <div ref={root} className="relative min-w-0 flex-1">
      <button
        type="button"
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-controls={id}
        onClick={() => setOpen(!open)}
        className="flex w-full items-center gap-3 px-2 py-1 text-left transition-colors hover:bg-paper-deep/60"
      >
        <span className="min-w-0 flex-1">
          <StageStrip run={run} />
        </span>
        <Chevron open={open} />
      </button>
      {open && (
        <div
          id={id}
          role="dialog"
          aria-label="Progress"
          data-popover
          className={`${popoverPanel} gr-scroll left-0 max-h-[calc(100vh-150px)] w-[min(360px,calc(100vw-24px))] overflow-auto p-5`}
        >
          <StageList run={run} />
        </div>
      )}
    </div>
  );
}

function ThisRun({ run }: { run: RunState }) {
  const { open, setOpen, root } = usePopover<HTMLDivElement>();
  const id = useId();
  return (
    <div ref={root} className="relative">
      <button type="button" aria-haspopup="dialog" aria-expanded={open} aria-controls={id} onClick={() => setOpen(!open)} className="gr-btn-line gap-2.5">
        This run
        <span className="hidden font-code normal-case tracking-normal text-ink-3 sm:inline">
          {run.words.toLocaleString('en-US')} words{run.elapsed > 0 && ` · ${clock(run.elapsed)}`}
        </span>
        <Chevron open={open} />
      </button>
      {open && (
        <div id={id} role="dialog" aria-label="This run" data-popover className={`${popoverPanel} left-0 w-[min(340px,calc(100vw-24px))] p-5`}>
          <Receipt run={run} />
        </div>
      )}
    </div>
  );
}

const FILES = [
  { key: 'pdf', label: 'PDF' },
  { key: 'docx', label: 'Word' },
  { key: 'md', label: 'Markdown' },
  { key: 'json', label: 'Logs' },
] as const;

function Download({ run, sharePath }: { run: RunState; sharePath: string }) {
  const { open, setOpen, root } = usePopover<HTMLDivElement>();
  const [copied, setCopied] = useState<'report' | 'link'>();
  const id = useId();
  const copy = async (what: 'report' | 'link') => {
    if (await copyText(what === 'report' ? run.report : `${window.location.origin}${sharePath}`)) setCopied(what);
    window.setTimeout(() => setCopied(undefined), 1600);
  };
  const files = FILES.filter((f) => run.files[f.key]);
  const item = 'flex w-full items-baseline justify-between gap-4 px-4 py-2.5 text-left text-[14px] font-medium transition-colors hover:bg-paper';
  return (
    <div ref={root} className="relative">
      <button type="button" aria-haspopup="menu" aria-expanded={open} aria-controls={id} onClick={() => setOpen(!open)} className="gr-btn-line gap-2.5">
        Download <Chevron open={open} />
      </button>
      {open && (
        <div id={id} role="menu" aria-label="Download" data-popover className={`${popoverPanel} right-0 w-[240px] py-2`}>
          {files.map((f) => (
            <a key={f.key} role="menuitem" href={`/${run.files[f.key]}`} target="_blank" rel="noopener noreferrer" className={item} onClick={() => setOpen(false)}>
              {f.label}
              <span className="font-code text-[10.5px] uppercase tracking-[0.1em] text-ink-3">.{run.files[f.key]!.split('.').pop()}</span>
            </a>
          ))}
          {files.length > 0 && <div className="my-1.5 h-px bg-rule-soft" />}
          <button type="button" role="menuitem" className={item} onClick={() => void copy('report')}>
            {copied === 'report' ? 'Copied' : 'Copy as Markdown'}
          </button>
          <button type="button" role="menuitem" className={`${item} sm:hidden`} onClick={() => void copy('link')}>
            {copied === 'link' ? 'Link copied' : 'Copy link'}
          </button>
          <span role="status" className="sr-only">
            {copied === 'report' ? 'Report copied' : copied === 'link' ? 'Link copied' : ''}
          </span>
        </div>
      )}
    </div>
  );
}

function Share({ path }: { path: string }) {
  const [copied, setCopied] = useState(false);
  return (
    <button
      type="button"
      className="gr-btn-line max-sm:!hidden"
      onClick={async () => {
        setCopied(await copyText(`${window.location.origin}${path}`));
        window.setTimeout(() => setCopied(false), 1800);
      }}
    >
      {copied ? 'Link copied' : 'Share'}
      <span role="status" className="sr-only">
        {copied ? 'Link copied' : ''}
      </span>
    </button>
  );
}

function Addendum({ n, q, a, run, onRemove }: { n: number; q: string; a: string; run: RunState; onRemove: () => void }) {
  const html = useCitedHtml(a, run.sources);
  return (
    <section className="gr-in mt-12 border-t border-rule pt-8">
      <div className="flex items-baseline justify-between gap-4">
        <p className="gr-meta">Follow up {n} · from the chat</p>
        <button type="button" onClick={onRemove} className="font-code text-[10.5px] uppercase tracking-[0.1em] text-ink-3 hover:text-rubric">
          Remove
        </button>
      </div>
      <h3 className="mt-3 font-display text-[1.45rem] font-semibold leading-tight tracking-[-0.015em]">{q}</h3>
      <div className="gr-prose mt-4" dangerouslySetInnerHTML={{ __html: html }} />
    </section>
  );
}

function Addenda({ run, chat }: { run: RunState; chat: Chat }) {
  const pinned = chat.messages.flatMap((m, i) => {
    const q = chat.messages[i - 1];
    return m.role === 'assistant' && m.pinned && q?.role === 'user' ? [{ id: m.id, q: q.content, a: m.content }] : [];
  });
  if (!pinned.length) return null;
  return (
    <div id="follow-ups" className="mt-16 scroll-mt-36">
      <div className="h-px bg-ink" />
      {pinned.map((p, i) => (
        <Addendum key={p.id} n={i + 1} q={p.q} a={p.a} run={run} onRemove={() => chat.togglePin(p.id)} />
      ))}
    </div>
  );
}

function Margin({
  run,
  tab,
  onTab,
  chat,
  highlight,
  onHighlight,
}: {
  run: RunState;
  tab: Tab;
  onTab: (tab: Tab) => void;
  chat: Chat;
  highlight?: number;
  onHighlight: (n?: number) => void;
}) {
  const asked = chat.messages.filter((m) => m.role === 'user').length;
  const tabs: { id: Tab; label: string }[] = [
    { id: 'sources', label: 'Sources' },
    { id: 'chat', label: asked ? `Chat ${asked}` : 'Chat' },
  ];

  return (
    <div id="margin" className="flex scroll-mt-20 flex-col min-[768px]:sticky min-[768px]:top-[136px] min-[768px]:max-h-[calc(100vh-152px)]">
      <div role="tablist" aria-label="Sources and chat" className="flex items-end gap-5 border-b border-ink">
        {tabs.map((t) => (
          <button
            key={t.id}
            id={`tab-${t.id}`}
            type="button"
            role="tab"
            aria-selected={tab === t.id}
            aria-controls="margin-panel"
            tabIndex={tab === t.id ? 0 : -1}
            onClick={() => onTab(t.id)}
            onKeyDown={(e) => {
              if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
              const next = tab === 'sources' ? 'chat' : 'sources';
              onTab(next);
              document.getElementById(`tab-${next}`)?.focus();
            }}
            className={`gr-meta -mb-px border-b-2 pb-3 transition-colors ${tab === t.id ? 'border-rubric text-ink' : 'border-transparent hover:text-ink'}`}
          >
            {t.label}
          </button>
        ))}
      </div>
      {tab === 'sources' && run.sources.length > 0 && (
        <p className="border-b border-rule-soft py-2 font-code text-[11px] tabular-nums text-ink-2">{sourcesSummary(run)}</p>
      )}
      <div id="margin-panel" role="tabpanel" aria-labelledby={`tab-${tab}`} data-scroll-box className="gr-scroll min-h-0 flex-1 overflow-auto">
        {tab === 'sources' ? <Sources run={run} highlight={highlight} onHighlight={onHighlight} /> : <ChatThread run={run} chat={chat} />}
      </div>
      {tab === 'chat' && <ChatComposer run={run} chat={chat} />}
    </div>
  );
}

function Drawer({ title, onClose, children }: { title: string; onClose: () => void; children: React.ReactNode }) {
  const close = useRef<HTMLButtonElement>(null);
  useEffect(() => {
    const opener = document.activeElement as HTMLElement | null;
    close.current?.focus();
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && onClose();
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('keydown', onKey);
      opener?.focus();
    };
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-[60] min-[1200px]:hidden" role="dialog" aria-modal="true" aria-label={title}>
      <button type="button" tabIndex={-1} aria-hidden="true" className="absolute inset-0 bg-ink/30" onClick={onClose} />
      <div id="sidebar-drawer" className="gr-in gr-scroll absolute inset-y-0 left-0 w-[min(320px,86vw)] overflow-auto bg-paper px-5 pb-10 pt-5 shadow-[0_0_60px_-20px_rgba(26,22,18,0.6)]">
        <div className="mb-6 flex items-center justify-between">
          <p className="gr-meta">{title}</p>
          <button ref={close} type="button" onClick={onClose} aria-label={`Close ${title.toLowerCase()}`} className="grid h-8 w-8 place-items-center text-[18px] text-ink-2 hover:text-rubric">
            ×
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

export interface RunScreenProps {
  run: RunState;
  /** The report type, as the header names it. */
  label: string;
  date: string;
  /** Path of this report's page, for Share. */
  sharePath: string;
  chatInitial?: ChatMessage[];
  onChatChange?: (messages: ChatMessage[]) => void;
  onStop?: () => void;
  onRestart?: () => void;
  onReview?: (notes: string | null) => void;
  initialTab?: Tab;
  initialFigure?: number;
}

export default function RunScreen({ run, label, date, sharePath, chatInitial = [], onChatChange, onStop, onRestart, onReview, initialTab, initialFigure }: RunScreenProps) {
  const [highlight, setHighlight] = useState<number>();
  const [tab, setTab] = useState<Tab>(initialTab ?? (chatInitial.length ? 'chat' : 'sources'));
  const [figure, setFigure] = useState(initialFigure);
  const chat = useChat(run.report, chatInitial);
  const { html, headings } = useReportHtml(run);
  useTabTitle(run);
  const done = run.status === 'done';
  const running = ['researching', 'review', 'drafting', 'writing'].includes(run.status);
  const addenda = chat.messages.filter((m) => m.pinned).length;

  const wide = useWide();
  const [pinned, setPinned] = useState(false);
  const [drawer, setDrawer] = useState(false);
  const contentsOpen = done && (wide ? pinned : drawer);
  /** The margin arrives with the first written paragraph, when citations start pointing at it. */
  const showMargin = done || Boolean(run.report);

  const saved = useRef(chat.messages);
  useEffect(() => {
    if (chat.busy || chat.messages === saved.current) return;
    saved.current = chat.messages;
    onChatChange?.(chat.messages);
  }, [chat.messages, chat.busy, onChatChange]);

  const openChat = () => {
    setTab('chat');
    document.getElementById('margin')?.scrollIntoView({ behavior: 'smooth' });
  };

  const contents = <Contents headings={headings} addenda={addenda} onNavigate={() => setDrawer(false)} />;
  const pinnedContents = done && pinned;

  return (
    <>
      <div
        style={{ '--m': showMargin ? 1 : 0 } as React.CSSProperties}
        className={`mx-auto grid max-w-[1440px] gap-y-8 px-3 pb-40 pt-3 transition-[grid-template-columns,column-gap] duration-500 ease-out motion-reduce:transition-none sm:px-7 ${
          pinnedContents
            ? 'min-[768px]:grid-cols-[minmax(0,1fr)_252px] min-[768px]:gap-x-8 min-[1200px]:grid-cols-[224px_minmax(0,1fr)_268px] min-[1200px]:gap-x-10'
            : 'min-[768px]:grid-cols-[minmax(0,1fr)_calc(var(--m)*252px)] min-[768px]:gap-x-[calc(var(--m)*32px)] min-[1200px]:grid-cols-[minmax(0,1fr)_calc(var(--m)*268px)] min-[1200px]:gap-x-[calc(var(--m)*40px)]'
        }`}
      >
        {pinnedContents && (
          <aside id="sidebar" aria-label="Contents" className="hidden min-[1200px]:block">
            <div className="gr-scroll sticky top-[136px] max-h-[calc(100vh-152px)] overflow-auto pb-6">{contents}</div>
          </aside>
        )}

        <main className={`min-w-0 ${pinnedContents ? '' : 'min-[768px]:mx-auto min-[768px]:w-full min-[768px]:max-w-[920px]'}`}>
          <div className="sticky top-16 z-30 -mx-1 flex min-h-[60px] items-center gap-2 bg-paper/90 px-1 py-2.5 backdrop-blur-sm">
            {done ? (
              <>
                <button
                  type="button"
                  onClick={() => (wide ? setPinned(!pinned) : setDrawer(!drawer))}
                  aria-expanded={contentsOpen}
                  aria-controls={wide ? 'sidebar' : 'sidebar-drawer'}
                  aria-label={`${contentsOpen ? 'Hide' : 'Show'} contents`}
                  title={`${contentsOpen ? 'Hide' : 'Show'} contents`}
                  className={`grid h-9 w-9 flex-none place-items-center transition-colors hover:text-ink ${contentsOpen ? 'bg-paper-deep text-ink' : 'text-ink-2'} shadow-[inset_0_0_0_1px_rgba(29,25,21,0.2)]`}
                >
                  <SidebarIcon />
                </button>
                <ThisRun run={run} />
              </>
            ) : (
              <Progress run={run} />
            )}
            <div className="ml-auto flex flex-none items-center gap-2">
              {done ? (
                <>
                  <Share path={sharePath} />
                  <Download run={run} sharePath={sharePath} />
                  <button type="button" className="gr-btn-line min-[768px]:!hidden" onClick={openChat}>
                    Chat
                  </button>
                </>
              ) : (
                running &&
                onStop && (
                  <button type="button" className="gr-btn-line" onClick={onStop}>
                    Stop<span className="hidden sm:inline">&nbsp;research</span>
                  </button>
                )
              )}
            </div>
          </div>
          <Sheet
            run={run}
            html={html}
            reportLabel={label}
            date={date}
            highlight={highlight}
            onHighlight={setHighlight}
            onOpenFigure={setFigure}
            onRestart={onRestart}
            onReview={onReview}
          >
            {done && <Addenda run={run} chat={chat} />}
          </Sheet>
        </main>

        {showMargin && (
          <aside className="min-w-0 min-[768px]:overflow-x-clip min-[768px]:pt-[60px]">
            <div className="gr-in h-full min-[768px]:w-[252px] min-[1200px]:w-[268px]">
              <Margin run={run} tab={tab} onTab={setTab} chat={chat} highlight={highlight} onHighlight={setHighlight} />
            </div>
          </aside>
        )}
      </div>
      {done && drawer && !wide && (
        <Drawer title="Contents" onClose={() => setDrawer(false)}>
          {contents}
        </Drawer>
      )}
      {figure !== undefined && run.images.length > 0 && (
        <Lightbox images={run.images} index={Math.min(figure, run.images.length - 1)} onIndex={setFigure} onClose={() => setFigure(undefined)} />
      )}
    </>
  );
}
