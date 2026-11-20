import type { RunState } from '@/lib/research/run';
import { Favicon } from './Favicon';

export const sourcesSummary = (run: RunState) => {
  const sites = new Set(run.sources.map((s) => s.domain)).size;
  if (!run.sources.length) return '';
  return `${run.sources.length} sources${sites < run.sources.length ? ` · ${sites} sites` : ''}`;
};

export default function Sources({ run, highlight, onHighlight }: { run: RunState; highlight?: number; onHighlight: (n?: number) => void }) {
  const writing = run.status === 'writing' || run.status === 'done';
  const live = run.status === 'researching';

  return (
    <section aria-label="Sources">
      {run.sources.length === 0 ? (
        <p className="py-4 text-[13.5px] leading-snug text-ink-3">Sources appear here as the researchers find them.</p>
      ) : (
        <ol>
          {run.sources.map((s) => {
            const dim = writing && !s.cited;
            const on = highlight === s.n;
            return (
              <li key={s.n} className={`gr-in border-b border-rule-soft ${live ? 'gr-flash' : ''}`}>
                <a
                  href={s.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  onMouseOver={() => onHighlight(s.n)}
                  onMouseLeave={() => onHighlight(undefined)}
                  onFocus={() => onHighlight(s.n)}
                  onBlur={() => onHighlight(undefined)}
                  className={`grid grid-cols-[20px_18px_minmax(0,1fr)_auto] items-start gap-x-2 py-2.5 transition-colors ${on ? 'bg-paper-hi' : ''}`}
                >
                  <span className={`pt-[3px] font-code text-[11px] tabular-nums ${s.cited ? 'text-rubric' : 'text-ink-3'}`}>{s.n}</span>
                  <Favicon domain={s.domain} className={`mt-px ${dim ? 'opacity-55 grayscale' : ''}`} />
                  <span className={`min-w-0 ${dim ? 'opacity-55' : ''}`}>
                    <span className="block truncate text-[13.5px] font-semibold leading-snug">{s.domain}</span>
                    <span className="block truncate font-code text-[10.5px] leading-relaxed text-ink-3">{s.path || '/'}</span>
                  </span>
                  {s.citations > 0 ? (
                    <span className="pt-[3px] font-code text-[10.5px] tabular-nums text-rubric" title={`Cited ${s.citations} times`}>
                      {s.citations}×<span className="sr-only"> cited</span>
                    </span>
                  ) : (
                    <span />
                  )}
                </a>
              </li>
            );
          })}
        </ol>
      )}
    </section>
  );
}
