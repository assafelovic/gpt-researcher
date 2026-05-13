export const TEST_QUERIES = {
  short: {
    query: 'KI in der Medizin',
    reportType: 'research_report',
  },
  withReport: {
    query: 'Vorteile von erneuerbaren Energien',
    reportType: 'research_report',
  },
};

export const REPORT_TYPES = [
  'research_report',
  'detailed_report',
  'quick_report',
  'resource_report',
  'outline_report',
] as const;

export const CHAT_MESSAGE = 'Fasse die wichtigsten Punkte zusammen.';

export const API_BASE = 'http://localhost:8002';
