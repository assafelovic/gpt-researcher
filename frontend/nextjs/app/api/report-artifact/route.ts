import { NextResponse } from "next/server";
import { backendHeaders, backendUrl } from "../_utils/backend";
import {
  normalizeOutputPath,
  sanitizeResearchId,
  type ReportArtifactKind,
} from "@/utils/reportArtifacts";

export const dynamic = "force-dynamic";

const SUPPORTED_KINDS = new Set<ReportArtifactKind>([
  "md",
  "pdf",
  "docx",
  "json",
]);

function jsonError(message: string, status: number) {
  return NextResponse.json({ error: message }, { status });
}

function contentTypeFor(
  kind: ReportArtifactKind,
  upstreamContentType: string | null,
): string {
  if (upstreamContentType) return upstreamContentType;
  if (kind === "docx") {
    return "application/vnd.openxmlformats-officedocument.wordprocessingml.document";
  }
  if (kind === "pdf") return "application/pdf";
  if (kind === "json") return "application/json; charset=utf-8";
  return "text/markdown; charset=utf-8";
}

function dispositionFor(
  kind: ReportArtifactKind,
  upstreamDisposition: string | null,
): string {
  if (upstreamDisposition) return upstreamDisposition;
  if (kind === "docx")
    return 'attachment; filename="mastery-research-report.docx"';
  if (kind === "pdf") return 'inline; filename="mastery-research-report.pdf"';
  if (kind === "json")
    return 'attachment; filename="mastery-research-log.json"';
  return 'inline; filename="mastery-research-report.md"';
}

async function proxyArtifact(request: Request, headOnly = false) {
  const url = new URL(request.url);
  const kind = url.searchParams.get("kind") as ReportArtifactKind | null;
  const rawPath = url.searchParams.get("path");
  const researchId = sanitizeResearchId(url.searchParams.get("research_id"));

  if (!kind || !SUPPORTED_KINDS.has(kind)) {
    return jsonError("Unsupported report artifact kind.", 400);
  }

  const normalizedPath = normalizeOutputPath(rawPath, kind);
  let backendPath: string | null = null;

  if (kind === "docx" && researchId) {
    backendPath = `/report/${encodeURIComponent(researchId)}`;
  } else if (normalizedPath) {
    backendPath = normalizedPath;
  }

  if (!backendPath) {
    return jsonError(
      `No safe ${kind.toUpperCase()} artifact path is available.`,
      400,
    );
  }

  try {
    const response = await fetch(`${backendUrl()}${backendPath}`, {
      // The FastAPI file routes are GET-first; probing with GET avoids surfacing a
      // false unavailable state when an upstream route does not implement HEAD.
      method: "GET",
      headers: backendHeaders(),
      cache: "no-store",
    });

    if (!response.ok) {
      return jsonError(
        `The ${kind.toUpperCase()} report artifact is not available yet or was not generated.`,
        response.status,
      );
    }

    const headers = new Headers({
      "content-type": contentTypeFor(
        kind,
        response.headers.get("content-type"),
      ),
      "cache-control": "no-store",
      "content-disposition": dispositionFor(
        kind,
        response.headers.get("content-disposition"),
      ),
    });

    const contentLength = response.headers.get("content-length");
    if (contentLength) headers.set("content-length", contentLength);

    if (headOnly) {
      await response.body?.cancel();
      return new Response(null, { status: 200, headers });
    }

    const body = await response.arrayBuffer();
    return new Response(body, { status: 200, headers });
  } catch (error) {
    console.error("GET /api/report-artifact - Error proxying artifact:", error);
    return jsonError("Failed to connect to the report artifact service.", 502);
  }
}

export async function GET(request: Request) {
  return proxyArtifact(request);
}

export async function HEAD(request: Request) {
  return proxyArtifact(request, true);
}
