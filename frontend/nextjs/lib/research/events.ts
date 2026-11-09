/**
 * Messages the Python backend streams over `/ws` while a research runs.
 * `t` is seconds since the run started, stamped by the client on receipt.
 */
export type ReportFiles = Partial<Record<'pdf' | 'docx' | 'md' | 'json', string>>;

export type ResearchEvent =
  | { type: 'logs'; content: string; output: string; metadata?: unknown; t: number }
  | { type: 'images'; content: string; output: string; metadata?: unknown; t: number }
  | { type: 'report'; output: string; t: number }
  | { type: 'report_complete'; output: string; t: number }
  | { type: 'path'; output: ReportFiles; t: number }
  | { type: 'human_feedback'; content: string; output: string; t: number }
  | { type: 'error'; output: string; t: number };

const KNOWN_TYPES = new Set(['logs', 'images', 'report', 'report_complete', 'path', 'human_feedback', 'error']);

export function parseEvent(raw: unknown, t: number): ResearchEvent | null {
  if (!raw || typeof raw !== 'object') return null;
  const data = raw as Record<string, unknown>;
  if (typeof data.type !== 'string' || !KNOWN_TYPES.has(data.type)) return null;
  if (data.type === 'logs' && typeof data.output !== 'string') {
    // The multi agent runner logs its whole final state as `research_report`; only the report is worth keeping.
    const report = (data.output as { report?: unknown } | null)?.report;
    return { ...data, output: typeof report === 'string' ? report : '', t } as ResearchEvent;
  }
  return { ...data, t } as ResearchEvent;
}
