'use client';

import { useEffect, useId, useState } from 'react';
import { DEFAULT_BRIEF, type BriefValue } from '@/lib/research/brief';
import { MCP_PRESETS, checkMcp } from '@/lib/research/mcp';
import { popoverPanel, usePopover } from './popover';
import { openSettings } from './preferences';

export interface Option {
  value: string;
  label: string;
  hint?: string;
}

export const REPORT_TYPES: Option[] = [
  { value: 'research_report', label: 'a summary', hint: 'About 2 minutes, around 1,500 words' },
  { value: 'detailed_report', label: 'a detailed report', hint: 'About 5 minutes, section by section' },
  { value: 'deep', label: 'a deep research report', hint: 'Follows new questions two levels down' },
  { value: 'multi_agents', label: 'a multi agent report', hint: 'About 7 minutes. Editor, reviewer and writer agents' },
];

export const SOURCES: Option[] = [
  { value: 'web', label: 'the web' },
  { value: 'local', label: 'my documents', hint: 'Only the files on the backend' },
  { value: 'hybrid', label: 'the web and my documents' },
];

export const TONES: Option[] = (
  [
    ['Objective', 'Impartial, sticks to the facts'],
    ['Formal', 'Academic language and structure'],
    ['Analytical', 'Examines data and theories closely'],
    ['Persuasive', 'Argues for one point of view'],
    ['Informative', 'Clear and complete coverage'],
    ['Explanatory', 'Makes complex ideas easy to follow'],
    ['Descriptive', 'Detailed accounts of cases and examples'],
    ['Critical', 'Judges how strong the evidence is'],
    ['Comparative', 'Sets options side by side'],
    ['Speculative', 'Explores what could happen next'],
    ['Reflective', 'Considers the process and its limits'],
    ['Narrative', 'Tells the findings as a story'],
    ['Humorous', 'Light and engaging'],
    ['Optimistic', 'Leads with benefits and upside'],
    ['Pessimistic', 'Leads with limits and risks'],
    ['Simple', 'Plain words for young readers'],
    ['Casual', 'Relaxed, everyday language'],
  ] as const
).map(([value, hint]) => ({ value, label: value.toLowerCase(), hint }));

export const MCP_STRATEGIES: Option[] = [
  { value: 'fast', label: 'Once per research', hint: 'Fastest. One call with your question' },
  { value: 'deep', label: 'For every question', hint: 'Slower and more thorough' },
];

export { DEFAULT_BRIEF, type BriefValue };

export type BriefField = 'report_type' | 'report_source' | 'tone' | 'domains';

function Choice({
  label,
  options,
  value,
  onChange,
  defaultOpen = false,
}: {
  label: string;
  options: Option[];
  value: string;
  onChange: (value: string) => void;
  defaultOpen?: boolean;
}) {
  const { open, setOpen, root } = usePopover<HTMLSpanElement>(defaultOpen);
  const id = useId();
  const current = options.find((o) => o.value === value) ?? options[0];

  useEffect(() => {
    if (open) root.current?.querySelector<HTMLElement>('[aria-selected="true"] button')?.focus({ preventScroll: true });
  }, [open, root]);

  return (
    <span ref={root} className="relative inline-block">
      <button
        type="button"
        className="gr-select"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-controls={id}
        aria-label={`${label}: ${current.label}`}
        onClick={() => setOpen((o) => !o)}
      >
        {current.label}
      </button>
      {open && (
        <ul
          id={id}
          role="listbox"
          aria-label={label}
          data-popover
          className={`${popoverPanel} gr-scroll left-[-14px] max-h-[min(360px,60vh)] w-[min(300px,calc(100vw-24px))] overflow-auto py-2`}
        >
          {options.map((o) => (
            <li key={o.value} role="option" aria-selected={o.value === value}>
              <button
                type="button"
                onClick={() => {
                  onChange(o.value);
                  setOpen(false);
                }}
                className="flex w-full items-start gap-3 px-4 py-2.5 text-left outline-none transition-colors hover:bg-paper focus-visible:bg-paper"
              >
                <i
                  className={`mt-[7px] h-[7px] w-[7px] flex-none ${o.value === value ? 'bg-rubric' : 'shadow-[inset_0_0_0_1px_#5F574B]'}`}
                  aria-hidden="true"
                />
                <span>
                  <span className="block text-[15px] font-medium leading-snug text-ink">{o.label}</span>
                  {o.hint && <span className="mt-0.5 block text-[13px] leading-snug text-ink-3">{o.hint}</span>}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </span>
  );
}

const toSite = (raw: string) =>
  raw
    .trim()
    .toLowerCase()
    .replace(/^https?:\/\//, '')
    .replace(/^www\./, '')
    .split(/[/?#\s]/)[0];

const isSite = (site: string) => /^[a-z0-9-]+(\.[a-z0-9-]+)+$/.test(site);

/** The site list with a field to add more, used by the sentence popover and by Settings. */
export function SitesEditor({ value, onChange, autoFocus = false }: { value: string[]; onChange: (sites: string[]) => void; autoFocus?: boolean }) {
  const [draft, setDraft] = useState('');
  const [invalid, setInvalid] = useState(false);

  const add = () => {
    const site = toSite(draft);
    if (!site) return;
    if (!isSite(site)) {
      setInvalid(true);
      return;
    }
    if (!value.includes(site)) onChange([...value, site]);
    setDraft('');
    setInvalid(false);
  };

  return (
    <>
      {value.length > 0 && (
        <ul className="mt-3 flex flex-wrap gap-1.5">
          {value.map((site) => (
            <li key={site}>
              <button
                type="button"
                onClick={() => onChange(value.filter((s) => s !== site))}
                aria-label={`Remove ${site}`}
                className="inline-flex h-7 items-center gap-2 bg-paper px-2.5 font-code text-[11.5px] shadow-[inset_0_0_0_1px_rgba(29,25,21,0.26)] transition-colors hover:text-rubric"
              >
                {site}
                <span aria-hidden="true">×</span>
              </button>
            </li>
          ))}
        </ul>
      )}
      <div className="mt-3 flex gap-2">
        <label className="min-w-0 flex-1">
          <span className="sr-only">Add a site</span>
          <input
            autoFocus={autoFocus}
            value={draft}
            onChange={(e) => {
              setDraft(e.target.value);
              setInvalid(false);
            }}
            onKeyDown={(e) => {
              if (e.key === 'Enter') {
                e.preventDefault();
                add();
              }
            }}
            placeholder="Add a site, like reuters.com"
            aria-invalid={invalid}
            className="gr-input h-9 w-full bg-paper px-3 text-[14px] outline-none shadow-[inset_0_0_0_1px_rgba(29,25,21,0.26)] focus:shadow-[inset_0_0_0_1px_#1A1612] aria-[invalid=true]:shadow-[inset_0_0_0_1px_#B8381C]"
          />
        </label>
        <button type="button" onClick={add} className="gr-btn-line h-9">
          Add
        </button>
      </div>
      {invalid && <p className="mt-2 text-[12.5px] text-rubric">That does not look like a site. Try reuters.com</p>}
    </>
  );
}

const sitesLabel = (sites: string[]) =>
  sites.length === 0
    ? 'any site'
    : sites.length === 1
      ? `only ${sites[0]}`
      : sites.length === 2
        ? `only ${sites[0]} and ${sites[1]}`
        : `only ${sites[0]} and ${sites.length - 1} more`;

function Sites({ value, onChange, defaultOpen = false }: { value: string[]; onChange: (sites: string[]) => void; defaultOpen?: boolean }) {
  const { open, setOpen, root } = usePopover<HTMLSpanElement>(defaultOpen);
  const id = useId();

  return (
    <span ref={root} className="relative inline-block">
      <button
        type="button"
        className="gr-select"
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-controls={id}
        aria-label={`Sites to read: ${sitesLabel(value)}`}
        onClick={() => setOpen((o) => !o)}
      >
        {sitesLabel(value)}
      </button>
      {open && (
        <div
          id={id}
          role="dialog"
          aria-label="Sites to read"
          data-popover
          className={`${popoverPanel} left-[-14px] w-[min(330px,calc(100vw-24px))] p-4 sm:left-auto sm:right-[-14px]`}
        >
          <p className="gr-meta">Only read these sites</p>
          <SitesEditor value={value} onChange={onChange} autoFocus />
          <div className="mt-4 flex items-center justify-between border-t border-rule-soft pt-3 text-[13.5px]">
            <button type="button" onClick={() => onChange([])} disabled={!value.length} className="text-ink-2 hover:text-ink disabled:opacity-40">
              Read any site
            </button>
            <button type="button" onClick={() => setOpen(false)} className="font-medium hover:text-rubric">
              Done
            </button>
          </div>
        </div>
      )}
    </span>
  );
}

export default function Brief({
  value,
  onChange,
  openField,
  documents,
}: {
  value: BriefValue;
  onChange: (value: BriefValue) => void;
  openField?: BriefField;
  documents?: number;
}) {
  const set = (key: 'report_type' | 'report_source' | 'tone') => (v: string) => onChange({ ...value, [key]: v });
  const article = /^[aeiou]/i.test(value.tone) ? 'an' : 'a';
  const readsWeb = value.report_source !== 'local';
  const readsDocs = value.report_source !== 'web';

  return (
    <div>
      <div className="text-[16px] leading-[1.9] text-ink-2">
        Write{' '}
        <Choice label="Report type" options={REPORT_TYPES} value={value.report_type} onChange={set('report_type')} defaultOpen={openField === 'report_type'} />{' '}
        from <Choice label="Sources" options={SOURCES} value={value.report_source} onChange={set('report_source')} defaultOpen={openField === 'report_source'} />{' '}
        in {article} <Choice label="Tone" options={TONES} value={value.tone} onChange={set('tone')} defaultOpen={openField === 'tone'} /> tone
        {readsWeb ? (
          <>
            , reading <Sites value={value.domains} onChange={(domains) => onChange({ ...value, domains })} defaultOpen={openField === 'domains'} />.
          </>
        ) : (
          '.'
        )}
        <McpClause value={value} />
      </div>
      {readsDocs && documents !== undefined && (
        <p className="mt-1 text-[13.5px] text-ink-3">
          {documents
            ? `Reads the ${documents} document${documents === 1 ? '' : 's'} already on the backend, plus any you add.`
            : 'No documents on the backend yet. Add files above.'}
        </p>
      )}
    </div>
  );
}

const names = (list: string[]) => (list.length <= 2 ? list.join(' and ') : `${list[0]} and ${list.length - 1} more`);

/** MCP is set up in Settings; the sentence says it is on, and opens it. */
function McpClause({ value }: { value: BriefValue }) {
  if (!value.mcp_enabled) return null;
  const check = checkMcp(value.mcp_configs);
  const open = () => openSettings('mcp');
  if (check.state === 'invalid') {
    return (
      <>
        {' '}
        <button type="button" className="gr-select !text-rubric" onClick={open}>
          The MCP config needs fixing
        </button>
        .
      </>
    );
  }
  return (
    <>
      {' '}
      {check.state === 'empty' ? 'MCP is on, ' : 'Also asks '}
      <button type="button" className="gr-select" onClick={open}>
        {check.state === 'empty'
          ? 'with no servers yet'
          : `${names(check.servers.map((s) => MCP_PRESETS.find((p) => p.server.name === s.name)?.label ?? s.name))} over MCP`}
      </button>
      .
    </>
  );
}
