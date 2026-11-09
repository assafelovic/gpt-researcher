import { reportLabel, type BriefValue } from './brief';
import { parseEvent, type ResearchEvent } from './events';
import { reduceRun, type RunState, type Source } from './run';

/** A chat turn as the backend keeps it. The extra fields are this UI's and older clients ignore them. */
export interface StoredChatMessage {
  role: 'user' | 'assistant';
  content: string;
  timestamp?: number;
  pinned?: boolean;
  seconds?: number;
  usedWeb?: boolean;
}

/** A report in the backend's store (`/api/reports`). `orderedData` holds the raw `/ws` events of the run. */
export interface StoredReport {
  id: string;
  question: string;
  answer: string;
  orderedData?: unknown[];
  chatMessages?: StoredChatMessage[];
  timestamp?: number;
  brief?: Partial<BriefValue>;
}

export interface ReportRow {
  id: string;
  title: string;
  question: string;
  type: string;
  date: string;
  month: string;
  timestamp: number;
  sources: number;
  words: number;
  /** Most cited sites first. */
  domains: string[];
  time: string;
}

/** Older reports were saved without receive times, so their events all sit at zero. */
export const storedEvents = (orderedData: unknown[] = []): ResearchEvent[] =>
  orderedData.flatMap((raw) => {
    const t = raw && typeof raw === 'object' && typeof (raw as { t?: unknown }).t === 'number' ? (raw as { t: number }).t : 0;
    const event = parseEvent(raw, t);
    return event ? [event] : [];
  });

export const storedRun = (report: StoredReport): RunState =>
  reduceRun(report.question ?? '', storedEvents(report.orderedData), { saved: { report: report.answer ?? '' } });

export const reportTitle = (run: RunState) => run.report.match(/^#\s+(.+)$/m)?.[1]?.trim() || run.query;

export const domainsByCitations = (sources: Source[]) => {
  const weight = new Map<string, number>();
  for (const s of sources) weight.set(s.domain, (weight.get(s.domain) ?? 0) + s.citations + (s.cited ? 1 : 0));
  return Array.from(weight.entries())
    .sort((a, b) => b[1] - a[1])
    .map(([domain]) => domain);
};

const clock = (seconds: number) => `${Math.floor(seconds / 60)}:${String(Math.floor(seconds % 60)).padStart(2, '0')}`;

export function summarize(report: StoredReport): ReportRow {
  const run = storedRun(report);
  const when = new Date(report.timestamp ?? Date.now());
  return {
    id: report.id,
    title: reportTitle(run),
    question: report.question ?? '',
    type: reportLabel(report.brief?.report_type),
    date: when.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
    month: when.toLocaleDateString('en-US', { month: 'long', year: 'numeric' }),
    timestamp: when.getTime(),
    sources: run.sources.length,
    words: run.words,
    domains: domainsByCitations(run.sources),
    time: run.elapsed > 0 ? clock(run.elapsed) : '',
  };
}

const json = async <T>(res: Response): Promise<T> => {
  if (!res.ok) throw new Error(`The backend answered with ${res.status}.`);
  return (await res.json()) as T;
};

export const listReports = async () => (await json<{ reports?: StoredReport[] }>(await fetch('/api/reports', { cache: 'no-store' }))).reports ?? [];

export async function getReport(id: string): Promise<StoredReport | null> {
  const res = await fetch(`/api/reports/${encodeURIComponent(id)}`, { cache: 'no-store' });
  if (res.status === 404) return null;
  return (await json<{ report?: StoredReport }>(res)).report ?? null;
}

export const saveReport = async (report: StoredReport) =>
  json(await fetch('/api/reports', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(report) }));

export const updateReport = async (id: string, patch: Partial<StoredReport>) =>
  json(await fetch(`/api/reports/${encodeURIComponent(id)}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(patch) }));

export const deleteReport = async (id: string, keepalive = false) => {
  const res = await fetch(`/api/reports/${encodeURIComponent(id)}`, { method: 'DELETE', keepalive });
  if (!res.ok && res.status !== 404) throw new Error(`The backend answered with ${res.status}.`);
};

interface ReportsState {
  status: 'idle' | 'loading' | 'ready' | 'error';
  reports: StoredReport[];
}

let state: ReportsState = { status: 'idle', reports: [] };
const listeners = new Set<() => void>();
const set = (next: ReportsState) => {
  state = next;
  listeners.forEach((l) => l());
};

/** Every report on the backend, shared by the home screen and the archive so moving between them doesn't flash. */
export const reportsStore = {
  get: () => state,
  subscribe(listener: () => void) {
    listeners.add(listener);
    return () => {
      listeners.delete(listener);
    };
  },
  async refresh() {
    set({ ...state, status: state.status === 'ready' ? 'ready' : 'loading' });
    try {
      set({ status: 'ready', reports: await listReports() });
    } catch {
      set({ ...state, status: 'error' });
    }
  },
  upsert(report: StoredReport) {
    set({ ...state, reports: [report, ...state.reports.filter((r) => r.id !== report.id)] });
  },
  drop(id: string) {
    set({ ...state, reports: state.reports.filter((r) => r.id !== id) });
  },
};
