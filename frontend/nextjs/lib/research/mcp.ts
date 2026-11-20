/** MCP server configs as the backend's `mcp_configs` takes them: a JSON list, typed by the user. */

export interface McpServer {
  name: string;
  command?: string;
  args?: string[];
  env?: Record<string, string>;
  connection_url?: string;
}

export interface McpPreset {
  id: string;
  label: string;
  hint: string;
  server: McpServer;
}

export const MCP_PRESETS: McpPreset[] = [
  {
    id: 'github',
    label: 'GitHub',
    hint: 'Repositories, issues and code',
    server: { name: 'github', command: 'npx', args: ['-y', '@modelcontextprotocol/server-github'], env: { GITHUB_PERSONAL_ACCESS_TOKEN: 'your_github_token_here' } },
  },
  {
    id: 'tavily',
    label: 'Tavily search',
    hint: 'Web search through Tavily',
    server: { name: 'tavily', command: 'npx', args: ['-y', 'tavily-mcp@0.1.2'], env: { TAVILY_API_KEY: 'your_tavily_api_key_here' } },
  },
  {
    id: 'filesystem',
    label: 'Local files',
    hint: 'A folder on the backend machine',
    server: { name: 'filesystem', command: 'npx', args: ['-y', '@modelcontextprotocol/server-filesystem', '/path/to/allowed/directory'], env: {} },
  },
];

export type McpCheck =
  | { state: 'empty'; servers: McpServer[]; message: string }
  | { state: 'ready'; servers: McpServer[]; message: string }
  | { state: 'invalid'; servers: McpServer[]; message: string };

const isEmpty = (text: string) => !text.trim() || text.trim() === '[]';

export function checkMcp(text: string): McpCheck {
  if (isEmpty(text)) return { state: 'empty', servers: [], message: 'No servers yet. Add a preset or paste a JSON list.' };
  let parsed: unknown;
  try {
    parsed = JSON.parse(text);
  } catch (e) {
    return { state: 'invalid', servers: [], message: `Not valid JSON. ${(e as Error).message}` };
  }
  if (!Array.isArray(parsed)) return { state: 'invalid', servers: [], message: 'The config must be a list of servers, in [ ].' };
  const problems = parsed.flatMap((server: Record<string, unknown> | null, i) => [
    ...(server?.name ? [] : [`server ${i + 1} has no name`]),
    ...(server?.command || server?.connection_url ? [] : [`server ${i + 1} needs a command or a connection_url`]),
  ]);
  if (problems.length) return { state: 'invalid', servers: [], message: `${problems.join(', ')}.`.replace(/^./, (c) => c.toUpperCase()) };
  const servers = parsed as McpServer[];
  return { state: 'ready', servers, message: `${servers.length} server${servers.length === 1 ? '' : 's'} ready.` };
}

export const mcpServers = (text: string): McpServer[] => checkMcp(text).servers;

const PLACEHOLDER = /^your_.+_here$|^\.\.\.$|^\/path\/to\//;

/** Values the presets ship with that still need the user's own keys or paths. */
export function mcpPlaceholders(servers: McpServer[]): string[] {
  return servers.flatMap((s) => [
    ...Object.entries(s.env ?? {})
      .filter(([, v]) => typeof v === 'string' && PLACEHOLDER.test(v))
      .map(([k]) => `${s.name}: ${k}`),
    ...(s.args ?? []).filter((a) => typeof a === 'string' && PLACEHOLDER.test(a)).map((a) => `${s.name}: ${a}`),
  ]);
}

const format = (servers: McpServer[]) => (servers.length ? JSON.stringify(servers, null, 2) : '');

/** Adds the preset's server, or removes the server with its name. Returns null when the text is not a valid list. */
export function togglePreset(text: string, preset: McpPreset): string | null {
  const check = checkMcp(text);
  if (check.state === 'invalid') return null;
  const has = check.servers.some((s) => s.name === preset.server.name);
  return format(has ? check.servers.filter((s) => s.name !== preset.server.name) : [...check.servers, preset.server]);
}

export const formatMcp = (text: string) => {
  const check = checkMcp(text);
  return check.state === 'invalid' ? text : format(check.servers);
};
