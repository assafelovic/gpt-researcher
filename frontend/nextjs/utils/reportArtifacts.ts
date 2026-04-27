export type ReportArtifactKind = "md" | "pdf" | "docx" | "json";

export type ReportArtifactInput = {
  kind: ReportArtifactKind;
  path?: string | null;
  researchId?: string | null;
};

export type ReportArtifactLink =
  | {
      ok: true;
      href: string;
      normalizedPath: string | null;
      usesResearchId: boolean;
    }
  | {
      ok: false;
      reason: string;
    };

const EXTENSIONS_BY_KIND: Record<ReportArtifactKind, string[]> = {
  md: [".md"],
  pdf: [".pdf"],
  docx: [".docx"],
  json: [".json"],
};

const LABELS_BY_KIND: Record<ReportArtifactKind, string> = {
  md: "Markdown",
  pdf: "PDF",
  docx: "DocX",
  json: "Logs",
};

export function reportArtifactLabel(kind: ReportArtifactKind): string {
  return LABELS_BY_KIND[kind];
}

export function reportArtifactUnavailableMessage(
  kind: ReportArtifactKind,
): string {
  const label = reportArtifactLabel(kind);
  if (kind === "md") {
    return `${label} unavailable. Retry after the run finishes syncing artifacts.`;
  }
  return `${label} unavailable. Retry, or open Markdown when available.`;
}

function decodePath(value: string): string {
  let decoded = value.trim();

  for (let index = 0; index < 2; index += 1) {
    try {
      const next = decodeURIComponent(decoded);
      if (next === decoded) break;
      decoded = next;
    } catch {
      break;
    }
  }

  return decoded;
}

export function sanitizeResearchId(value?: string | null): string | null {
  const id = value?.trim();
  if (!id || id.includes("/") || id.includes("\\") || id.includes(".."))
    return null;
  return id;
}

export function normalizeOutputPath(
  rawPath: string | null | undefined,
  kind: ReportArtifactKind,
): string | null {
  if (!rawPath) return null;

  let path =
    decodePath(rawPath).replace(/\\/g, "/").split(/[?#]/)[0]?.trim() ?? "";
  if (!path) return null;

  if (/^https?:\/\//i.test(path)) {
    try {
      path = new URL(path).pathname;
    } catch {
      return null;
    }
  }

  const outputsIndex = path.toLowerCase().lastIndexOf("/outputs/");
  if (outputsIndex >= 0) {
    path = path.slice(outputsIndex + 1);
  } else {
    path = path.replace(/^\/+/, "");
    if (!path.startsWith("outputs/")) {
      path = `outputs/${path}`;
    }
  }

  const segments = path
    .split("/")
    .map((segment) => segment.trim())
    .filter(Boolean);

  if (segments[0] !== "outputs" || segments.length < 2) return null;
  if (segments.some((segment) => segment === "." || segment === ".."))
    return null;

  const filename = segments[segments.length - 1].toLowerCase();
  if (
    !EXTENSIONS_BY_KIND[kind].some((extension) => filename.endsWith(extension))
  ) {
    return null;
  }

  return `/${segments.map((segment) => encodeURIComponent(segment)).join("/")}`;
}

export function buildReportArtifactLink(
  input: ReportArtifactInput,
): ReportArtifactLink {
  const safeResearchId = sanitizeResearchId(input.researchId);
  const normalizedPath = normalizeOutputPath(input.path, input.kind);

  if (input.kind === "docx" && safeResearchId) {
    const params = new URLSearchParams({
      kind: input.kind,
      research_id: safeResearchId,
    });

    if (normalizedPath) {
      params.set("path", normalizedPath);
    }

    return {
      ok: true,
      href: `/api/report-artifact?${params.toString()}`,
      normalizedPath,
      usesResearchId: true,
    };
  }

  if (!normalizedPath) {
    return {
      ok: false,
      reason: `No safe ${input.kind.toUpperCase()} artifact path is available for this run.`,
    };
  }

  const params = new URLSearchParams({
    kind: input.kind,
    path: normalizedPath,
  });

  return {
    ok: true,
    href: `/api/report-artifact?${params.toString()}`,
    normalizedPath,
    usesResearchId: false,
  };
}
