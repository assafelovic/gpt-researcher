import { citationCounts, citedUrls, sourceKey } from './citations';
import type { ReportFiles, ResearchEvent } from './events';

export type StageId = 'plan' | 'search' | 'read' | 'filter' | 'write';
export type StageStatus = 'waiting' | 'active' | 'done' | 'failed';

export interface Stage {
  id: StageId;
  label: string;
  status: StageStatus;
  startedAt?: number;
  endedAt?: number;
  detail: string;
}

export interface Source {
  n: number;
  url: string;
  domain: string;
  path: string;
  addedAt: number;
  cited: boolean;
  /** Inline citations of this source in the report so far. */
  citations: number;
}

export type QuestionStatus = 'queued' | 'searching' | 'reading' | 'done' | 'empty' | 'stopped';

export interface Question {
  text: string;
  status: QuestionStatus;
}

export type ActivityKind = 'plan' | 'search' | 'read' | 'pick' | 'empty' | 'write' | 'done';

/** One line of what the researchers are doing, in words a reader understands. */
export interface Activity {
  t: number;
  kind: ActivityKind;
  text: string;
  /** A research question or report section the line is about. */
  quote?: string;
  /** Source numbers in the batch being read. */
  sources?: number[];
  images?: string[];
}

export interface LogLine {
  t: number;
  key: string;
  text: string;
}

export type RunStatus = 'idle' | 'researching' | 'review' | 'drafting' | 'writing' | 'done' | 'stopped' | 'failed';

/** The multi agent editor pauses after planning and asks for notes on its outline. */
export interface PlanReview {
  prompt: string;
  sections: string[];
}

export interface RunState {
  query: string;
  status: RunStatus;
  elapsed: number;
  review?: PlanReview;
  /** The part of the report in hand: a detailed report researches its sections at once, then writes them in turn. */
  section?: { action: 'researching'; titles: string[] } | { action: 'writing'; title: string };
  agent?: string;
  subqueries: string[];
  questions: Question[];
  sources: Source[];
  pagesScraped: number;
  /** Figures the writer was handed. */
  images: string[];
  /** Every figure the scraper kept along the way, as it found them. */
  foundImages: string[];
  report: string;
  words: number;
  sections: number;
  cost?: number;
  files: ReportFiles;
  error?: string;
  stages: Stage[];
  activity: Activity[];
  log: LogLine[];
}

const STAGE_LABELS: Record<StageId, string> = {
  plan: 'Plan',
  search: 'Search',
  read: 'Read',
  filter: 'Filter',
  write: 'Write',
};

const LEADING_EMOJI = /^[\p{Extended_Pictographic}\uFE0F\u200D\s]+/u;
const cleanLine = (text: string) => text.replace(LEADING_EMOJI, '').trim();

const asList = (value: unknown): string[] => {
  if (Array.isArray(value)) return value.filter((v): v is string => typeof v === 'string');
  if (typeof value === 'string') {
    try {
      return asList(JSON.parse(value));
    } catch {
      return [];
    }
  }
  return [];
};

/** The scraper keeps some site chrome (logos, buttons, spacers, headshots) that is never a figure. */
const CHROME_FILE = /icon|logo|spacer|sprite|badge|avatar|headshot|button|close|refresh|loading|pixel/i;
const isFigure = (url: string) => {
  const path = url.split(/[?#]/)[0];
  const file = path.slice(path.lastIndexOf('/') + 1);
  return !/\.(svg|gif)$/i.test(file) && !CHROME_FILE.test(file) && !/\/(icons?|logos?|avatars?|tiny)\//i.test(path);
};

const plural = (n: number, word: string) => `${n.toLocaleString('en-US')} ${word}${n === 1 ? '' : 's'}`;

const countWords = (markdown: string) => (markdown.trim() ? markdown.trim().split(/\s+/).length : 0);

/** Finished `## ` headings; one still streaming has no line break yet. */
const SECTION = /^## (?!#)(.+)\n/gm;

/** The question a log line is about: after `query:`, or quoted in `'...'`. */
const questionIn = (text: string) =>
  (text.match(/query:\s*([\s\S]+?)(?:\.{3})?$/)?.[1] ?? text.match(/'([\s\S]+)'/)?.[1] ?? text).trim();

function describeUrl(url: string) {
  try {
    const u = new URL(url);
    return { domain: u.hostname.replace(/^www\./, ''), path: decodeURIComponent(u.pathname + u.search).replace(/\/$/, '') };
  } catch {
    return { domain: url, path: '' };
  }
}

/** The backend sends the outline as a Python list repr inside a sentence. */
function parseReview(output: string): PlanReview {
  const list = output.match(/\[([\s\S]*)\]/)?.[1] ?? '';
  const sections = Array.from(list.matchAll(/'((?:[^'\\]|\\.)+)'|"((?:[^"\\]|\\.)+)"/g), (m) => m[1] ?? m[2]);
  return { prompt: cleanLine(output), sections };
}

export interface ReduceOptions {
  /** Seconds since start, for a live clock between events. */
  now?: number;
  /** Set when the user stopped the run; the stream simply ends there. */
  stoppedAt?: number;
  /** A run read back from the report store is finished, and its saved answer is the report. */
  saved?: { report: string };
}

/** Folds the backend event stream into everything the UI renders. Pure, so a recorded run replays exactly. */
export function reduceRun(query: string, events: ResearchEvent[], { now, stoppedAt, saved }: ReduceOptions = {}): RunState {
  const firstAt: Partial<Record<string, number>> = {};
  const count: Record<string, number> = {};
  /** Counts for the plan's own questions, before a detailed run starts on its sections. */
  const planCount: Record<string, number> = {};
  const sources: Source[] = [];
  const byKey = new Map<string, Source>();
  const log: LogLine[] = [];
  const activity: Activity[] = [];
  const foundImages: string[] = [];
  const searched = new Set<string>();
  const picked = new Set<string>();
  const empty = new Set<string>();
  let batch: number[] = [];
  let lastPages = 0;
  let streamedSections = 0;
  let agent: string | undefined;
  let subqueries: string[] = [];
  let pagesScraped = 0;
  let images: string[] = [];
  let report = '';
  let cost: number | undefined;
  let files: ReportFiles = {};
  let error: string | undefined;
  let review: PlanReview | undefined;
  let last = 0;
  /** Multi agent runs stream each researcher's draft as `report`; the published report comes at the end. */
  let multi = false;
  /** Detailed runs stream an introduction, then research and stream each subtopic, then a conclusion. */
  let detailed = false;
  let section: RunState['section'];
  let writeAt: number | undefined;
  let writtenAt: number | undefined;
  const writing = (title: string) => {
    section = { action: 'writing', title };
    if (report && !report.endsWith('\n')) report += '\n\n';
  };

  const addSource = (url: string, t: number) => {
    const key = sourceKey(url);
    if (byKey.has(key)) return byKey.get(key)!;
    const source: Source = { n: sources.length + 1, url, ...describeUrl(url), addedAt: t, cited: false, citations: 0 };
    sources.push(source);
    byKey.set(key, source);
    return source;
  };

  const say = (t: number, kind: ActivityKind, text: string, extra: Partial<Activity> = {}) => {
    activity.push({ t, kind, text, ...extra });
  };

  for (const event of events) {
    const t = event.t;
    last = Math.max(last, t);
    const key = 'content' in event ? event.content : event.type;
    firstAt[key] ??= t;
    count[key] = (count[key] ?? 0) + 1;
    if (!detailed) planCount[key] = (planCount[key] ?? 0) + 1;
    review = event.type === 'human_feedback' && event.content === 'request' ? parseReview(event.output) : undefined;
    if (review) say(t, 'plan', 'Waiting for your notes on the outline');

    switch (event.type) {
      case 'report': {
        if (multi) break;
        report += event.output;
        const titles = Array.from(report.matchAll(SECTION), (m) => m[1].trim());
        for (const title of titles.slice(streamedSections)) {
          say(t, 'write', 'Writing', { quote: title });
          section = { action: 'writing', title };
        }
        streamedSections = titles.length;
        break;
      }
      case 'report_complete':
        report = event.output;
        break;
      case 'path':
        files = event.output;
        break;
      case 'error':
        error = event.output;
        break;
      case 'images':
        if (event.content === 'selected_images') images = asList(event.metadata ?? event.output).filter(isFigure);
        break;
      case 'logs': {
        const text = cleanLine(event.output);
        log.push({ t, key: event.content, text });
        switch (event.content) {
          case 'agent_generated':
            if (text !== agent) say(t, 'plan', `Working as the ${text}`);
            agent = text;
            break;
          case 'planning_research':
            say(t, 'plan', /browsing/i.test(text) ? 'Browsing the web to understand the question' : 'Planning the research');
            break;
          case 'subqueries': {
            const list = asList(event.metadata);
            if (detailed) {
              if (list.length) say(t, 'plan', `Split the section into ${plural(list.length, 'question')}`);
              break;
            }
            subqueries = list;
            if (subqueries.length) say(t, 'plan', `Split it into ${plural(subqueries.length, 'question')}`);
            break;
          }
          case 'generating_subtopics':
            detailed = true;
            say(t, 'plan', 'Outlining the sections');
            break;
          case 'starting_research': {
            if (!detailed) break;
            const title = questionIn(text);
            section = { action: 'researching', titles: section?.action === 'researching' ? [...section.titles, title] : [title] };
            say(t, 'search', 'Researching the section', { quote: title });
            break;
          }
          case 'writing_introduction':
            writeAt ??= t;
            writing('Introduction');
            say(t, 'write', 'Writing the introduction');
            break;
          case 'writing_conclusion':
            writing('Conclusion');
            say(t, 'write', 'Writing the conclusion');
            break;
          case 'conclusion_written':
            writtenAt ??= t;
            say(t, 'done', `Report written, ${plural(countWords(report), 'word')}`);
            break;
          case 'added_source_url':
            if (typeof event.metadata === 'string') batch.push(addSource(event.metadata, t).n);
            break;
          case 'scraping_urls': {
            const n = Number(text.match(/\d+/)?.[0] ?? 0);
            if (n > 0) say(t, 'read', `Reading ${plural(n, 'page')}`, { sources: Array.from(new Set(batch)) });
            batch = [];
            break;
          }
          case 'scraping_content':
            lastPages = Number(text.match(/\d+/)?.[0] ?? 0);
            pagesScraped += lastPages;
            break;
          case 'scraping_images': {
            const fresh = asList(event.metadata).filter((url) => isFigure(url) && !foundImages.includes(url));
            foundImages.push(...fresh);
            if (lastPages > 0) {
              say(t, 'read', `Read ${plural(lastPages, 'page')}${fresh.length ? `, kept ${plural(fresh.length, 'figure')}` : ''}`, { images: fresh });
            }
            lastPages = 0;
            break;
          }
          case 'running_subquery_research': {
            const q = questionIn(text);
            searched.add(q);
            say(t, 'search', 'Searching', { quote: q });
            break;
          }
          case 'fetching_query_content': {
            const q = questionIn(text);
            picked.add(q);
            say(t, 'pick', 'Picking passages for', { quote: q });
            break;
          }
          case 'subquery_context_not_found': {
            const q = questionIn(text);
            empty.add(q);
            say(t, 'empty', 'Nothing usable for', { quote: q });
            break;
          }
          case 'research_step_finalized': {
            const spent = Number(text.match(/\$([\d.]+)/)?.[1]) || undefined;
            cost = detailed && spent ? (cost ?? 0) + spent : spent;
            say(t, 'done', `Research done: ${plural(sources.length, 'source')}, ${plural(pagesScraped, 'page')}`);
            break;
          }
          case 'writing_report':
            if (multi && !/final/i.test(text)) break;
            writeAt ??= t;
            if (detailed) {
              const title = questionIn(text);
              writing(title);
              say(t, 'write', 'Writing', { quote: title });
            } else say(t, 'write', 'Writing the report');
            break;
          case 'report_written':
            if (multi || detailed) break;
            writtenAt ??= t;
            say(t, 'done', `Report written, ${plural(countWords(report), 'word')}`);
            break;
          case 'human_feedback_sent':
            say(t, 'plan', text);
            break;
          case 'initial_research':
            multi = true;
            say(t, 'plan', 'Reading the web for a first brief');
            break;
          case 'parallel_research':
            say(t, 'search', 'Researching the sections in parallel');
            break;
          case 'depth_research':
            multi = true;
            say(t, 'search', 'Researching the section', { quote: text.replace(/^.*report topic:\s*/i, '') });
            break;
          case 'review_feedback':
            say(t, 'pick', 'The reviewer sent notes on a section');
            break;
          case 'revision_notes':
            say(t, 'pick', 'Revising a section with the reviewer notes');
            break;
          case 'fact_checking':
            say(t, 'pick', text.length > 90 ? `${text.slice(0, 90)}…` : text);
            break;
          case 'publishing':
            say(t, 'write', 'Publishing the report');
            break;
          case 'research_report':
            if (event.output.trim()) report = event.output;
            break;
          default:
            if (event.content === 'error' || text.startsWith('Error')) error = text.replace(/^Error:\s*/, '');
        }
        break;
      }
    }
  }

  if (saved?.report) report = saved.report;
  for (const url of citedUrls(report)) addSource(url, last).cited = true;
  const citations = citationCounts(report);
  for (const source of sources) source.citations = citations.get(sourceKey(source.url)) ?? 0;

  const words = countWords(report);
  const sections = Array.from(report.matchAll(SECTION)).filter((m) => !/^references$/i.test(m[1].trim())).length;
  const researchDone = multi ? writeAt : firstAt.research_step_finalized;
  const writeDone = writtenAt ?? (files.md || files.docx ? last : undefined);
  const n = subqueries.length;
  const stopped = stoppedAt !== undefined;
  if (stopped) say(stoppedAt, 'empty', 'You stopped the research');

  const spans: Record<StageId, [number | undefined, number | undefined]> = {
    plan: [firstAt.starting_research ?? firstAt.planning_research, multi ? firstAt.parallel_research : firstAt.subqueries],
    search: [firstAt.subqueries, researchDone],
    read: [firstAt.added_source_url ?? firstAt.scraping_urls, researchDone],
    filter: [firstAt.fetching_query_content, researchDone],
    write: [writeAt, writeDone],
  };

  const details: Record<StageId, string> = {
    plan: review ? 'Waiting for your notes' : n ? `${agent ? `${agent}, ` : ''}${plural(n, 'question')}` : 'Splitting the question',
    search: count.depth_research
      ? `${plural(count.depth_research, 'section')} researched in depth`
      : n
        ? `${planCount.running_subquery_research ?? 0} of ${n} questions searched`
        : '',
    read: sources.length ? `${plural(sources.length, 'source')} · ${plural(pagesScraped, 'page')}` : '',
    filter: planCount.context_combined ? `Context for ${planCount.context_combined} of ${n} questions` : '',
    write: words ? `${plural(words, 'word')}${sections ? ` · ${plural(sections, 'section')}` : ''}` : spans.write[0] !== undefined ? 'Drafting' : '',
  };

  const stages: Stage[] = (Object.keys(spans) as StageId[]).map((id) => {
    const [startedAt, endedAt] = spans[id];
    const status: StageStatus =
      startedAt === undefined ? 'waiting' : endedAt !== undefined ? 'done' : error || stopped ? 'failed' : 'active';
    return { id, label: STAGE_LABELS[id], status, startedAt, endedAt, detail: details[id] };
  });

  const seen = (set: Set<string>, q: string) => set.has(q) || Array.from(set).some((s) => s.includes(q));
  const questions: Question[] = subqueries.map((text) => ({
    text,
    status: seen(empty, text)
      ? 'empty'
      : researchDone !== undefined
        ? 'done'
        : stopped
          ? 'stopped'
          : seen(picked, text)
            ? 'reading'
            : seen(searched, text)
              ? 'searching'
              : 'queued',
  }));

  const finished = saved || files.md || files.docx || files.json;
  const status: RunStatus = saved
    ? 'done'
    : error
      ? 'failed'
      : finished
        ? 'done'
        : stopped
          ? 'stopped'
          : review
            ? 'review'
            : report
              ? 'writing'
              : writeAt !== undefined
                ? 'drafting'
                : events.length
                  ? 'researching'
                  : 'idle';

  return {
    query,
    status,
    elapsed: status === 'stopped' ? stoppedAt! : status === 'done' || status === 'failed' ? last : Math.max(last, now ?? last),
    review,
    section,
    agent,
    subqueries,
    questions,
    sources,
    pagesScraped,
    images,
    foundImages,
    report,
    words,
    sections,
    cost,
    files,
    error,
    stages,
    activity,
    log,
  };
}
