export interface BaseData {
  type: string;
  content?: string;
  metadata?: any;
  output?: any;
  link?: string;
  items?: any[];
  contentAndType?: string;
}

export interface AccordionGroup {
  type: 'accordionBlock';
  items: {
    content: string;
    output: string;
    metadata: any;
    type: string;
  }[];
}

export interface SourceGroup {
  type: 'sourceBlock';
  items: { name: string; url: string }[];
}

export interface ReportGroup {
  type: 'reportBlock';
  content: string;
}

export interface AccordionData extends BaseData {
  type: 'accordionBlock';
  items: {
    header: string;
    text: string;
    metadata: any;
    key: string;
  }[];
}

export interface SourceBlockData extends BaseData {
  type: 'sourceBlock';
  items: { name: string; url: string }[];
}

export interface ReportBlockData extends BaseData {
  type: 'reportBlock';
  content: string;
}

export interface LanggraphButtonData extends BaseData {
  type: 'langgraphButton';
  link: string;
}

export interface QuestionData extends BaseData {
  type: 'question';
  content: string;
}

export interface ChatData extends BaseData {
  type: 'chat';
  content: string;
}

export interface LogData extends BaseData {
  type: 'logs';
  content: string;
  output: {
    report?: string;
    [key: string]: any;
  };
  metadata: any;
}

export type Data = BaseData | AccordionData | SourceBlockData | ReportBlockData | LanggraphButtonData | QuestionData | ChatData | LogData;

export interface ChatBoxSettings {
  report_source: string;
  report_type: string;
  tone: string;
  task?: string;
}

export interface WebSocketMessage {
  type: string;
  content: string;
  metadata?: any;
  output?: any;
} 