import { HLTResearchScope } from "@/types/data";

export const defaultHLTResearchScope: HLTResearchScope = {
  codebase: false,
  cms: false,
  qbank: false,
  metrics: false,
  firecrawl: false,
  media: false,
  audience: false,
  recruiting: false,
  depth: "balanced",
  mode: "standard",
};

export function normalizeHLTResearchScope(
  scope?: Partial<HLTResearchScope>,
): HLTResearchScope {
  return {
    ...defaultHLTResearchScope,
    ...(scope || {}),
  };
}

export function selectedScopeCount(scope?: Partial<HLTResearchScope>): number {
  const normalized = normalizeHLTResearchScope(scope);
  return [
    normalized.codebase,
    normalized.cms,
    normalized.qbank,
    normalized.metrics,
    normalized.firecrawl,
    normalized.media,
    normalized.audience,
    normalized.recruiting,
  ].filter(Boolean).length;
}
