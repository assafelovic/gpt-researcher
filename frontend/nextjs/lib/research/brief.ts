import { mcpServers } from './mcp';

/** What the user asks the backend to write, as chosen on the home screen or in Settings. */
export interface BriefValue {
  report_type: string;
  report_source: string;
  tone: string;
  domains: string[];
  mcp_enabled: boolean;
  mcp_strategy: string;
  /** The MCP server list as typed, a JSON array. */
  mcp_configs: string;
}

export const DEFAULT_BRIEF: BriefValue = {
  report_type: 'research_report',
  report_source: 'web',
  tone: 'Objective',
  domains: [],
  mcp_enabled: false,
  mcp_strategy: 'fast',
  mcp_configs: '',
};

export const REPORT_TYPE_VALUES = ['research_report', 'detailed_report', 'deep', 'multi_agents'];
export const SOURCE_VALUES = ['web', 'local', 'hybrid'];
/** The tones in `gpt_researcher/utils/enum.py`. */
export const TONE_VALUES = [
  'Objective',
  'Formal',
  'Analytical',
  'Persuasive',
  'Informative',
  'Explanatory',
  'Descriptive',
  'Critical',
  'Comparative',
  'Speculative',
  'Reflective',
  'Narrative',
  'Humorous',
  'Optimistic',
  'Pessimistic',
  'Simple',
  'Casual',
];
export const MCP_STRATEGY_VALUES = ['fast', 'deep'];

const REPORT_LABELS: Record<string, string> = {
  research_report: 'Summary',
  detailed_report: 'Detailed',
  deep: 'Deep',
  multi_agents: 'Multi agent',
};

export const reportLabel = (reportType?: string) => (reportType && REPORT_LABELS[reportType]) || 'Summary';

const oneOf = (value: unknown, allowed: string[], fallback: string) => (typeof value === 'string' && allowed.includes(value) ? value : fallback);

/** A brief read back from storage, with anything unknown or malformed replaced by the default. */
export function parseBrief(raw: unknown): BriefValue {
  const r = (raw && typeof raw === 'object' ? raw : {}) as Record<string, unknown>;
  return {
    report_type: oneOf(r.report_type, REPORT_TYPE_VALUES, DEFAULT_BRIEF.report_type),
    report_source: oneOf(r.report_source, SOURCE_VALUES, DEFAULT_BRIEF.report_source),
    tone: oneOf(r.tone, TONE_VALUES, DEFAULT_BRIEF.tone),
    domains: Array.isArray(r.domains) ? r.domains.filter((d): d is string => typeof d === 'string' && d.length > 0) : [],
    mcp_enabled: r.mcp_enabled === true,
    mcp_strategy: oneOf(r.mcp_strategy, MCP_STRATEGY_VALUES, DEFAULT_BRIEF.mcp_strategy),
    mcp_configs: typeof r.mcp_configs === 'string' ? r.mcp_configs : '',
  };
}

/** The JSON the backend's `start` command reads, see `extract_command_data` in `backend/server/server_utils.py`. */
export const startPayload = (task: string, brief: BriefValue) => ({
  task,
  report_type: brief.report_type,
  report_source: brief.report_source,
  tone: brief.tone,
  query_domains: brief.domains,
  source_urls: [],
  document_urls: [],
  mcp_enabled: brief.mcp_enabled,
  mcp_strategy: brief.mcp_strategy,
  mcp_configs: brief.mcp_enabled ? mcpServers(brief.mcp_configs) : [],
});
