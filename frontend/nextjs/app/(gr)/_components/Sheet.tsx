'use client';

import Link from 'next/link';
import { useEffect, useMemo, useRef, useState } from 'react';
import { markdownToHtml } from '@/helpers/markdownHelper';
import { numberCitations, sourceKey } from '@/lib/research/citations';
import type { Activity, PlanReview, Question, RunState, Source } from '@/lib/research/run';
import { Favicon, FaviconStack, Thumb, domainsBySources, faviconUrl } from './Favicon';
import { useLinks } from './mode';
import { questionMark } from './Stages';
import { Eye, clock } from './ui';

const slug = (html: string) =>
  's-' +
  html
    .replace(/<[^>]+>/g, '')
    .replace(/&[^;]+;/g, '')
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');

const withHeadingIds = (html: string) =>
  html.replace(/<h([23])>([\s\S]*?)<\/h\1>/g, (_, level: string, inner: string) => `<h${level} id="${slug(inner)}">${inner}</h${level}>`);

const hostOf = (url: string) => {
  try {
    return new URL(url.replace(/&amp;/g, '&')).hostname.replace(/^www\./, '');
  } catch {
    return '';
  }
};

/** Starts each entry in the writer's reference list with its site's icon. */
const withReferenceIcons = (html: string) => {
  const at = html.indexOf('id="s-references"');
  if (at === -1) return html;
  return (
    html.slice(0, at) +
    html.slice(at).replace(/<(p|li)>([\s\S]*?)<\/\1>/g, (entry, tag: string, inner: string) => {
      const host = hostOf(inner.match(/<a href="(https?:\/\/[^"]+)"/)?.[1] ?? '');
      return host ? `<${tag}><img class="gr-ref-fav" src="${faviconUrl(host)}" alt="" loading="lazy">${inner}</${tag}>` : entry;
    })
  );
};

/** Splits the report after its first section, where the figure plate goes. */
const afterFirstSection = (html: string): [string, string] => {
  const first = html.indexOf('<h2');
  const second = first === -1 ? -1 : html.indexOf('<h2', first + 3);
  return second === -1 ? [html, ''] : [html.slice(0, second), html.slice(second)];
};

/** The source an image came from, when its host or first folder names the site (res.cloudinary.com/tikr is tikr.com). */
const figureSource = (src: string, sources: Source[]) => {
  try {
    const url = new URL(src);
    const folder = url.pathname.split('/')[1]?.toLowerCase();
    return sources.find((s) => {
      const name = s.domain.split('.').slice(-2, -1)[0]?.toLowerCase();
      return name && name.length > 1 && (url.hostname.includes(`${name}.`) || folder === name);
    });
  } catch {
    return undefined;
  }
};

function Plate({ images, sources, onOpen }: { images: string[]; sources: Source[]; onOpen: (index: number) => void }) {
  const [broken, setBroken] = useState<string[]>([]);
  const usable = images.filter((src) => !broken.includes(src));
  const shown = usable.slice(0, 3);
  const more = usable.length - shown.length;
  const drop = (src: string) => setBroken((b) => (b.includes(src) ? b : [...b, src]));
  if (!shown.length) return null;

  return (
    <figure className="gr-in mt-10" aria-label="Figures from the sources">
      <div className="flex items-baseline justify-between border-b border-ink pb-2.5">
        <p className="gr-meta">Figures from the sources</p>
        <p className="font-code text-[11px] tabular-nums text-ink-3">{usable.length}</p>
      </div>
      <ul className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-3 sm:grid-rows-2">
        {shown.map((src, i) => {
          const index = images.indexOf(src);
          const from = figureSource(src, sources);
          const last = more > 0 && i === shown.length - 1;
          return (
            <li key={src} className={i === 0 ? 'col-span-2 sm:row-span-2' : ''}>
              <button
                type="button"
                onClick={() => onOpen(index)}
                aria-label={last ? `Open figure ${index + 1}, ${more} more` : `Open figure ${index + 1}`}
                className={`group relative block w-full overflow-hidden bg-paper-deep outline-offset-2 ${i === 0 ? 'aspect-[16/10] sm:aspect-auto sm:h-full' : 'aspect-[4/3]'}`}
              >
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img
                  src={src}
                  alt=""
                  loading="lazy"
                  referrerPolicy="no-referrer"
                  onError={() => drop(src)}
                  onLoad={(e) => e.currentTarget.naturalWidth < 120 && drop(src)}
                  className="absolute inset-0 h-full w-full object-cover mix-blend-multiply transition-transform duration-500 group-hover:scale-[1.03]"
                />
                <span className="absolute bottom-0 left-0 inline-flex max-w-full items-center gap-1.5 bg-paper-hi/95 py-1 pl-1 pr-2 font-code text-[10px] uppercase tracking-[0.1em] text-ink-2">
                  {from && <Favicon domain={from.domain} />}
                  <span className="truncate">
                    Fig. {index + 1}
                    {from && <span className="normal-case tracking-normal"> · {from.domain}</span>}
                  </span>
                </span>
                {last && <span className="absolute inset-0 grid place-items-center bg-ink/55 font-code text-[13px] text-paper-hi">+{more}</span>}
              </button>
            </li>
          );
        })}
      </ul>
    </figure>
  );
}

const LAST_BLOCK_END = /(<\/(?:p|li|h[1-6]|td)>)(?![\s\S]*<\/(?:p|li|h[1-6]|td)>)/;

/** Drops a citation that is still streaming in, so `([Diaz, 20` never flashes as raw text. */
const settled = (markdown: string) => {
  const open = markdown.lastIndexOf('([');
  return open !== -1 && !markdown.slice(open).includes('))') ? markdown.slice(0, open) : markdown;
};

export const readingMinutes = (words: number) => Math.max(1, Math.round(words / 230));

export interface Heading {
  id: string;
  text: string;
}

/** Markdown from the writer, with citations numbered against the run's sources. */
export function useCitedHtml(markdown: string, sources: RunState['sources'], streaming = false) {
  const [html, setHtml] = useState('');
  const numbers = useMemo(() => new Map(sources.map((s) => [sourceKey(s.url), s.n])), [sources]);

  useEffect(() => {
    let alive = true;
    const cited = numberCitations(streaming ? settled(markdown) : markdown, (url) => numbers.get(sourceKey(url)));
    markdownToHtml(cited).then((out) => {
      if (alive) setHtml(withHeadingIds(out));
    });
    return () => {
      alive = false;
    };
  }, [markdown, streaming, numbers]);

  return html;
}

export function useReportHtml(run: RunState) {
  const streaming = run.status === 'writing';
  const html = useCitedHtml(run.report, run.sources, streaming);

  const headings = useMemo<Heading[]>(
    () =>
      Array.from(html.matchAll(/<h2 id="([^"]+)">([\s\S]*?)<\/h2>/g)).map(([, id, inner]) => ({
        id,
        text: inner.replace(/<[^>]+>/g, '').replace(/&#x26;/g, '&'),
      })),
    [html],
  );

  const decorated = useMemo(() => withReferenceIcons(html), [html]);
  return { html: streaming ? decorated.replace(LAST_BLOCK_END, '<span class="gr-caret"></span>$1') : decorated, headings };
}

const questionWord: Record<Question['status'], string> = {
  queued: 'queued',
  searching: 'searching',
  reading: 'reading',
  done: 'done',
  empty: 'nothing found',
  stopped: 'stopped',
};

function Plan({ run }: { run: RunState }) {
  return (
    <ol className="mt-5 border-t border-rule-soft">
      {run.questions.map((q, i) => {
        const busy = q.status === 'searching' || q.status === 'reading';
        return (
          <li key={q.text} className="gr-in grid grid-cols-[30px_minmax(0,1fr)_auto] items-baseline gap-2 border-b border-rule-soft py-3">
            <span className="font-code text-[11px] text-rubric">Q{i + 1}</span>
            <span className={`font-display text-[17px] leading-snug ${q.status === 'empty' ? 'text-ink-3' : ''}`}>{q.text}</span>
            <span className={`inline-flex items-center gap-2 font-code text-[10px] uppercase tracking-[0.12em] ${busy ? 'text-rubric' : 'text-ink-3'}`}>
              <i className={`h-[6px] w-[6px] flex-none ${questionMark[q.status]}`} aria-hidden="true" />
              {questionWord[q.status]}
            </span>
          </li>
        );
      })}
    </ol>
  );
}

const activityKey = (a: Activity) => `${a.t}-${a.kind}-${a.text}-${a.quote ?? ''}`;

/** The last few things the researchers did, newest first, fading as they age. */
function Feed({ run, live }: { run: RunState; live: boolean }) {
  const byNumber = useMemo(() => new Map(run.sources.map((s) => [s.n, s])), [run.sources]);
  const items = run.activity.slice(-6).reverse();
  if (!items.length) return null;
  const latest = items[0];

  return (
    <section className="mt-9" aria-labelledby="feed-h">
      <Eye>
        <span id="feed-h">Now</span>
      </Eye>
      <p role="status" className="sr-only">
        {latest.text} {latest.quote}
      </p>
      <ol className="mt-4 border-t border-ink">
        {items.map((a, i) => {
          const batch = (a.sources ?? []).map((n) => byNumber.get(n)).filter((s): s is Source => Boolean(s));
          return (
            <li
              key={activityKey(a)}
              className="gr-in grid grid-cols-[38px_minmax(0,1fr)] gap-3 border-b border-rule-soft py-2.5 transition-opacity duration-700"
              style={{ opacity: Math.max(0.32, 1 - i * 0.15) }}
            >
              <span className="pt-[3px] font-code text-[10.5px] tabular-nums text-ink-3">{clock(a.t)}</span>
              <div className="min-w-0">
                <p className="flex min-w-0 items-center gap-2 text-[14.5px] leading-snug">
                  <i
                    aria-hidden="true"
                    className={`h-[7px] w-[7px] flex-none ${
                      i > 0 ? 'bg-rule' : live ? 'animate-[gr-blink_1.2s_steps(2,jump-none)_infinite] bg-rubric' : 'bg-ink'
                    }`}
                  />
                  <span className="flex-none font-medium">{a.text}</span>
                  {a.quote && <span className="min-w-0 truncate font-display text-[15.5px] text-ink-2">“{a.quote}”</span>}
                </p>
                {batch.length > 0 && (
                  <ul className="mt-2 flex flex-wrap gap-1.5 pl-[15px]" aria-label="Pages being read">
                    {batch.slice(0, 4).map((s, j) => (
                      <li
                        key={s.n}
                        className={`h-7 max-w-[210px] items-center gap-1.5 bg-paper pl-1 pr-2.5 shadow-[inset_0_0_0_1px_rgba(29,25,21,0.14)] ${j < 2 ? 'inline-flex' : 'hidden sm:inline-flex'}`}
                      >
                        <Favicon domain={s.domain} />
                        <span className="truncate text-[12.5px] font-medium">{s.domain}</span>
                      </li>
                    ))}
                    {batch.length > 2 && (
                      <li className={`h-7 items-center px-1 font-code text-[11px] text-ink-3 ${batch.length > 4 ? 'inline-flex' : 'inline-flex sm:hidden'}`}>
                        <span className="sm:hidden">+{batch.length - 2}</span>
                        <span className="hidden sm:inline">+{batch.length - 4}</span>
                      </li>
                    )}
                  </ul>
                )}
                {a.images && a.images.length > 0 && (
                  <div className="mt-2 flex gap-1.5 pl-[15px]" aria-hidden="true">
                    {a.images.slice(0, 4).map((src) => (
                      <Thumb key={src} src={src} className="h-10 w-[54px]" />
                    ))}
                  </div>
                )}
              </div>
            </li>
          );
        })}
      </ol>
    </section>
  );
}

const Waiting = ({ children }: { children: React.ReactNode }) => (
  <p className="mt-4 max-w-[34em] text-[16px] leading-relaxed text-ink-2">
    {children}
    <span className="gr-caret" aria-hidden="true" />
  </p>
);

function failureHint(error: string) {
  if (/api_key|OPENAI_API_KEY|credentials/i.test(error))
    return 'The backend has no OpenAI API key. Add OPENAI_API_KEY to the backend .env file, restart it, and try again.';
  return 'The backend stopped before the report was written. Your question and settings are kept, so you can try again.';
}

function Stopped({ run, onRestart }: { run: RunState; onRestart?: () => void }) {
  const at = run.stages.find((s) => s.status === 'failed')?.label;
  const links = useLinks();
  return (
    <div className="mt-8 bg-paper px-6 py-5 shadow-[inset_0_0_0_1px_rgba(29,25,21,0.26)]" role="status">
      <Eye>Stopped{at ? ` at ${at}` : ''}</Eye>
      <p className="mt-4 max-w-[34em] text-[16px] leading-relaxed text-ink">
        You stopped the research at {clock(run.elapsed)}.
        {run.report && ' The draft so far is kept below, with its sources in the margin.'}
      </p>
      <div className="mt-5 flex flex-wrap items-center gap-4">
        <button type="button" className="gr-btn" onClick={onRestart}>
          Start again
        </button>
        <Link href={links.home} className="text-[14px] font-medium underline decoration-rule underline-offset-4 hover:decoration-rubric">
          New research
        </Link>
      </div>
    </div>
  );
}

function Review({ review, onReply }: { review: PlanReview; onReply?: (notes: string | null) => void }) {
  const [notes, setNotes] = useState('');
  return (
    <section className="gr-in mt-10 bg-paper px-6 py-6 shadow-[inset_0_0_0_1px_#1A1612]" aria-labelledby="review-h">
      <Eye>Your turn</Eye>
      <h2 id="review-h" className="mt-4 max-w-[26em] font-display text-[1.35rem] font-semibold leading-snug tracking-[-0.01em]">
        The editor planned {review.sections.length} sections. Change anything before the researchers start?
      </h2>
      <ol className="mt-5 border-t border-rule-soft">
        {review.sections.map((s, i) => (
          <li key={s} className="grid grid-cols-[30px_minmax(0,1fr)] items-baseline gap-2 border-b border-rule-soft py-2.5">
            <span className="font-code text-[11px] text-rubric">{String(i + 1).padStart(2, '0')}</span>
            <span className="font-display text-[17px] leading-snug">{s}</span>
          </li>
        ))}
      </ol>
      <label className="mt-5 block">
        <span className="sr-only">Notes for the editor</span>
        <textarea
          rows={3}
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Add, drop or change a section. Leave empty if the plan works."
          className="gr-input w-full resize-y bg-paper-hi px-4 py-3 text-[15px] leading-relaxed outline-none shadow-[inset_0_0_0_1px_rgba(29,25,21,0.26)] focus:shadow-[inset_0_0_0_1px_#1A1612]"
        />
      </label>
      <div className="mt-4 flex flex-wrap items-center gap-3">
        <button type="button" className="gr-btn" onClick={() => onReply?.(null)}>
          Start with this plan
        </button>
        <button type="button" className="gr-btn-line h-11" disabled={!notes.trim()} onClick={() => onReply?.(notes.trim())}>
          Send notes
        </button>
      </div>
    </section>
  );
}

/** What the report rests on: its sites, its size and the section being written. */
function Byline({ run }: { run: RunState }) {
  const now = run.status === 'writing' ? run.section : undefined;
  return (
    <>
      <details className="mt-4">
        <summary className="flex cursor-pointer list-none flex-wrap items-center gap-x-3 gap-y-1.5 font-code text-[12px] text-ink-3 hover:text-ink">
          <FaviconStack domains={domainsBySources(run.sources)} max={5} />
          <span className="underline decoration-rule underline-offset-4">
            {run.sources.length} sources, {run.questions.length} questions
          </span>
          <span className="tabular-nums">
            {run.words.toLocaleString('en-US')} words · {readingMinutes(run.words)} min read
          </span>
        </summary>
        <Plan run={run} />
      </details>
      {now && (
        <p className="mt-3 flex items-center gap-2 font-code text-[11.5px] text-rubric">
          <i className="h-[7px] w-[7px] animate-[gr-blink_1.2s_steps(2,jump-none)_infinite] bg-rubric" aria-hidden="true" />
          <span className="truncate">
            {now.action === 'writing'
              ? `Writing “${now.title}”`
              : now.titles.length > 1
                ? `Researching ${now.titles.length} sections at once`
                : `Researching “${now.titles[0]}”`}
          </span>
        </p>
      )}
    </>
  );
}

interface CardAt {
  n: number;
  label: string;
  top: number;
  left: number;
}

function CiteCard({ source, at }: { source: Source; at: CardAt }) {
  return (
    <div
      role="tooltip"
      className="gr-in pointer-events-none absolute z-20 w-[288px] bg-paper-hi px-4 py-3.5 shadow-[0_22px_44px_-26px_rgba(29,25,21,0.6),0_0_0_1px_rgba(29,25,21,0.16)]"
      style={{ top: at.top, left: at.left }}
    >
      <div className="flex items-start gap-3">
        <Favicon domain={source.domain} size="md" />
        <div className="min-w-0">
          <p className="truncate text-[14px] font-semibold leading-snug">{at.label || source.domain}</p>
          <p className="truncate font-code text-[10.5px] leading-relaxed text-ink-3">
            {source.domain}
            {source.path}
          </p>
        </div>
      </div>
      <p className="mt-2.5 border-t border-rule-soft pt-2 font-code text-[10.5px] uppercase tracking-[0.1em] text-ink-3">
        Source {source.n}
        {source.citations > 1 && ` · cited ${source.citations} times`}
      </p>
    </div>
  );
}

export default function Sheet({
  run,
  html,
  reportLabel,
  date,
  highlight,
  onHighlight,
  onOpenFigure,
  onRestart,
  onReview,
  children,
}: {
  run: RunState;
  html: string;
  reportLabel: string;
  date: string;
  highlight?: number;
  onHighlight: (n?: number) => void;
  onOpenFigure?: (index: number) => void;
  onRestart?: () => void;
  onReview?: (notes: string | null) => void;
  children?: React.ReactNode;
}) {
  const sheet = useRef<HTMLElement>(null);
  const prose = useRef<HTMLDivElement>(null);
  const [card, setCard] = useState<CardAt>();
  const hasReport = Boolean(run.report);
  const live = ['researching', 'drafting', 'writing'].includes(run.status);
  const cardSource = card && run.sources.find((s) => s.n === card.n);
  const [lead, rest] = useMemo(() => afterFirstSection(html), [html]);

  useEffect(() => {
    prose.current?.querySelectorAll<HTMLElement>('.cite').forEach((el) => {
      el.dataset.on = String(Number(el.dataset.cite) === highlight);
    });
  }, [highlight, html]);

  const onOver = (e: React.MouseEvent) => {
    const cite = (e.target as HTMLElement).closest<HTMLElement>('.cite');
    const n = cite ? Number(cite.dataset.cite) || undefined : undefined;
    onHighlight(n);
    if (!cite || !n || !sheet.current) return setCard(undefined);
    if (card?.n === n) return;
    const box = sheet.current.getBoundingClientRect();
    const mark = cite.getBoundingClientRect();
    setCard({
      n,
      label: cite.dataset.label ?? '',
      top: mark.bottom - box.top + 8,
      left: Math.max(12, Math.min(mark.left - box.left - 18, box.width - 300)),
    });
  };

  return (
    <article ref={sheet} className="gr-sheet px-6 pb-16 pt-8 sm:px-[72px] sm:pb-20 sm:pt-12" aria-label="Research report">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <p className="gr-meta">Research report · {reportLabel}</p>
        <p className="gr-meta">{date}</p>
      </header>

      {hasReport ? (
        <>
          <p className="mt-5 font-code text-[12px] leading-relaxed text-ink-3">
            <span className="text-rubric">Q</span> {run.query}
          </p>
          <Byline run={run} />
          {run.status === 'stopped' && <Stopped run={run} onRestart={onRestart} />}
          <div
            ref={prose}
            className="mt-8"
            onMouseOver={onOver}
            onMouseLeave={() => {
              onHighlight(undefined);
              setCard(undefined);
            }}
          >
            <div className="gr-prose" dangerouslySetInnerHTML={{ __html: lead }} />
            {rest && <Plate images={run.images} sources={run.sources} onOpen={(i) => onOpenFigure?.(i)} />}
            {rest && <div className="gr-prose" dangerouslySetInnerHTML={{ __html: rest }} />}
          </div>
          {card && cardSource && <CiteCard source={cardSource} at={card} />}
        </>
      ) : (
        <>
          <h1 className="mt-8 max-w-[18em] text-balance font-display text-[clamp(2rem,3vw,2.75rem)] font-semibold leading-[1.08] tracking-[-0.025em]">
            {run.query}
          </h1>

          {run.status === 'failed' ? (
            <div className="mt-10 bg-paper px-6 py-5 shadow-[inset_0_0_0_1px_#B8381C]" role="alert">
              <Eye>Stopped at {run.stages.find((s) => s.status === 'failed')?.label ?? 'start'}</Eye>
              <p className="mt-4 max-w-[34em] text-[16px] leading-relaxed text-ink">{failureHint(run.error ?? '')}</p>
              <p className="mt-3 break-words font-code text-[11.5px] leading-relaxed text-ink-3">{run.error}</p>
              <div className="mt-5 flex flex-wrap items-center gap-4">
                <button type="button" className="gr-btn" onClick={onRestart}>
                  Try again
                </button>
                <a href="https://docs.gptr.dev/docs/gpt-researcher/gptr/config" className="text-[14px] font-medium underline decoration-rule underline-offset-4 hover:decoration-rubric">
                  Backend configuration
                </a>
              </div>
            </div>
          ) : run.review ? (
            <Review key={run.review.prompt} review={run.review} onReply={onReview} />
          ) : (
            <>
              {run.status === 'stopped' && <Stopped run={run} onRestart={onRestart} />}
              <Feed run={run} live={live} />
              <section className="mt-10" aria-label="The plan">
                <Eye>{run.subqueries.length ? `The plan, ${run.subqueries.length} questions` : 'The plan'}</Eye>
                {run.subqueries.length ? (
                  <Plan run={run} />
                ) : (
                  run.status !== 'stopped' && <Waiting>Splitting your question into research questions</Waiting>
                )}
              </section>
              {run.status === 'drafting' && (
                <section className="mt-12" aria-label="Drafting">
                  <Eye>Drafting</Eye>
                  <Waiting>
                    The writer is reading {run.sources.length} sources and {run.pagesScraped} pages. The first paragraph takes a moment
                  </Waiting>
                  <div className="mt-5 flex flex-wrap items-center gap-3">
                    <FaviconStack domains={run.sources.map((s) => s.domain)} max={9} size="md" />
                    <span className="font-code text-[11px] text-ink-3">
                      {new Set(run.sources.map((s) => s.domain)).size} sites
                      {run.images.length > 0 && ` · ${run.images.length} figures`}
                    </span>
                  </div>
                  <div className="mt-8 space-y-3" aria-hidden="true">
                    {[92, 100, 84, 96, 58].map((w, i) => (
                      <i key={i} className="block h-[9px] animate-pulse bg-rule-soft" style={{ width: `${w}%`, animationDelay: `${i * 140}ms` }} />
                    ))}
                  </div>
                </section>
              )}
            </>
          )}
        </>
      )}
      {children}
    </article>
  );
}
