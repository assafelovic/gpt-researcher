const LINK = /\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g;
const CITE_GROUP =
  /\s*\(\s*(\[[^\]]+\]\(https?:\/\/[^\s)]+\)(?:\s*[;,]\s*\[[^\]]+\]\(https?:\/\/[^\s)]+\))*)\s*\)/g;

/** Identifies a page regardless of protocol, `www.`, fragment or trailing slash. */
export function sourceKey(url: string): string {
  try {
    const u = new URL(url);
    const host = u.hostname.replace(/^www\./, '').toLowerCase();
    return `${host}${u.pathname.replace(/\/+$/, '')}${u.search}`;
  } catch {
    return url;
  }
}

/** URLs the report cites, in the order they first appear. */
export function citedUrls(markdown: string): string[] {
  const seen = new Map<string, string>();
  for (const [, , url] of Array.from(markdown.matchAll(LINK))) {
    const key = sourceKey(url);
    if (!seen.has(key)) seen.set(key, url);
  }
  return Array.from(seen.values());
}

/** How often each source is cited inline, keyed by `sourceKey`. Links in the reference list do not count. */
export function citationCounts(markdown: string): Map<string, number> {
  const counts = new Map<string, number>();
  for (const [, group] of Array.from(markdown.matchAll(CITE_GROUP))) {
    for (const [, , url] of Array.from(group.matchAll(LINK))) {
      const key = sourceKey(url);
      counts.set(key, (counts.get(key) ?? 0) + 1);
    }
  }
  return counts;
}

/**
 * Turns the writer's inline citations, e.g. `([Diaz, 2026](https://...))`,
 * into numbered marks that point at the run's source list.
 */
export function numberCitations(markdown: string, numberFor: (url: string) => number | undefined): string {
  return markdown.replace(CITE_GROUP, (_, group: string) => {
    const marks = Array.from(group.matchAll(LINK)).map(([, label, url]) => {
      const n = numberFor(url);
      const safeLabel = label.replace(/"/g, '&quot;');
      return `<a class="cite" href="${url}" data-cite="${n ?? ''}" data-label="${safeLabel}" aria-label="Source ${n ?? ''}: ${safeLabel}">${n ?? '•'}</a>`;
    });
    return `<sup class="cites">${marks.join('')}</sup>`;
  });
}
