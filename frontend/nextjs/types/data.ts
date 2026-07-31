export interface BaseData {
  type: string;
}

export interface BasicData extends BaseData {
  type: "basic";
  content: string;
}

export interface LanggraphButtonData extends BaseData {
  type: "langgraphButton";
  link: string;
}

export interface DifferencesData extends BaseData {
  type: "differences";
  content: string;
  output: string;
}

export interface QuestionData extends BaseData {
  type: "question";
  content: string;
}

export interface ChatData extends BaseData {
  type: "chat";
  content: string;
  metadata?: any; // For storing search results and other contextual information
}

export interface ReportData extends BaseData {
  type: "report" | "report_complete";
  content?: string;
  output: string;
  metadata?: any;
}

export interface PathData extends BaseData {
  type: "path";
  output: {
    md?: string;
    pdf?: string;
    docx?: string;
    json?: string;
    research_id?: string;
    run_id?: string;
  };
  research_id?: string;
  run_id?: string;
}

export type Data =
  | BasicData
  | LanggraphButtonData
  | DifferencesData
  | QuestionData
  | ChatData
  | ReportData
  | PathData;

export interface MCPConfig {
  name: string;
  command?: string;
  args?: string[];
  env?: Record<string, string>;
  connection_url?: string;
  connection_type?: string;
  preset?: string;
}

export type HLTResearchDepth = "fast" | "balanced" | "deep";

export type HLTResearchMode = "standard" | "top1";

export interface HLTResearchScope {
  codebase: boolean;
  cms: boolean;
  qbank: boolean;
  metrics: boolean;
  firecrawl: boolean;
  media: boolean;
  audience: boolean;
  recruiting: boolean;
  depth: HLTResearchDepth;
  mode: HLTResearchMode;
}

export interface ChatBoxSettings {
  report_type: string;
  report_source: string;
  tone: string;
  domains: string[];
  defaultReportType: string;
  layoutType: string;
  mcp_enabled: boolean;
  mcp_configs: MCPConfig[];
  mcp_strategy?: string;
  hlt_research_scope?: HLTResearchScope;
}

export interface Domain {
  value: string;
}

export interface ChatMessage {
  role: "user" | "assistant" | "system";
  content: string;
  timestamp?: number;
  metadata?: any; // For storing search results and other contextual information
}

export interface ResearchHistoryItem {
  id: string;
  question: string;
  answer: string;
  timestamp: number;
  orderedData: Data[];
  chatMessages?: ChatMessage[];
}
