import { parseEvent, type ResearchEvent } from '@/lib/research/events';
import type { ChatMessage } from '../../_components/Chat';
import recorded from './nvidia-run.json';

export interface Scenario {
  query: string;
  label: string;
  events: ResearchEvent[];
}

/** A real run recorded from the backend over `/ws`, with receive times. */
const nvidia: Scenario = {
  query: recorded.task,
  label: 'Summary',
  events: (recorded.events as unknown as Array<Record<string, unknown> & { t: number }>)
    .map((e) => parseEvent(e, e.t))
    .filter((e): e is ResearchEvent => e !== null),
};

const failedQuery = 'How close are solid state batteries to mass production?';

/** The error the backend really sends when it starts without an OpenAI key. */
const failed: Scenario = {
  query: failedQuery,
  label: 'Summary',
  events: [
    { type: 'logs', content: 'starting_research', output: `Starting the research task for '${failedQuery}'...`, t: 0.4 },
    { type: 'logs', content: 'agent_generated', output: 'Default Agent', t: 0.4 },
    { type: 'logs', content: 'planning_research', output: 'Planning the research strategy and subtasks...', t: 1.9 },
    {
      type: 'logs',
      content: 'error',
      output:
        'Error: Missing credentials. Please pass an `api_key`, `workload_identity`, `admin_api_key`, or set the `OPENAI_API_KEY` or `OPENAI_ADMIN_KEY` environment variable.',
      t: 2.3,
    },
  ],
};

const reviewQuery = 'How should a coastal city prepare for extreme heat?';
export const reviewSections = [
  'How hot coastal cities are getting',
  'Who is most at risk',
  'Cooling streets and buildings',
  'Early warning and emergency response',
  'Paying for adaptation',
];

/** Sample multi agent run up to the editor's plan review, shaped like the backend's `human_feedback` request. */
const review: Scenario = {
  query: reviewQuery,
  label: 'Multi agent',
  events: [
    { type: 'logs', content: 'starting_research', output: `Starting the research task for '${reviewQuery}'...`, t: 0.3 },
    { type: 'logs', content: 'agent_generated', output: 'Editor Agent', t: 0.4 },
    { type: 'logs', content: 'planning_research', output: 'Running a first pass of research to plan the outline...', t: 1.2 },
    ...[
      'https://www.who.int/news-room/fact-sheets/detail/climate-change-heat-and-health',
      'https://www.epa.gov/heatislands',
      'https://www.ipcc.ch/report/ar6/wg2/',
      'https://www.weather.gov/safety/heat',
      'https://www.heat.gov/',
    ].map((url, i): ResearchEvent => ({ type: 'logs', content: 'added_source_url', output: `Added source url to research: ${url}`, metadata: url, t: 3 + i * 1.6 })),
    { type: 'logs', content: 'scraping_urls', output: '🌐 Scraping content from 5 URLs...', metadata: null, t: 10 },
    { type: 'logs', content: 'scraping_content', output: '📄 Scraped 5 pages of content', metadata: null, t: 12.4 },
    {
      type: 'human_feedback',
      content: 'request',
      output: `Any feedback on this plan of topics to research? [${reviewSections.map((s) => `'${s}'`).join(', ')}]? If not, please reply with 'no'.`,
      t: 14.5,
    },
  ],
};

export const scenarios = { nvidia, failed, review };
export type ScenarioName = keyof typeof scenarios;

/** A follow up written from the report's own findings and sources, for the deterministic screenshot. */
export const sampleChat: ChatMessage[] = [
  { id: 1, role: 'user', content: 'What could stop the rally?' },
  {
    id: 2,
    role: 'assistant',
    seconds: 11,
    pinned: true,
    content:
      'The report names five risks: China export restrictions, hyperscalers building their own chips, a few customers buying most of the GPUs, margin pressure and weaker cash conversion ([FXOpen Market Pulse, n.d.](https://fxopen.com/blog/en/analytical-nvidia-stock-price-targets); [Yahoo Finance, 2026](https://finance.yahoo.com/sectors/technology/article/why-nvidia-stock-looks-cheap-ahead-of-its-high-stakes-earnings-report-this-month-114822826.html)). As of late 2026 the sources see the bull case confirmed more often than challenged, so these read as things to watch rather than reasons the stock is falling ([Heesoon, 2026](https://heesoontusa.tistory.com/entry/Nvidia-Earnings-2026-Record-Revenue-but-One-Number-Worries-Me)).',
  },
];
