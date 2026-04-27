import assert from "node:assert/strict";
import fs from "node:fs";
import { createRequire } from "node:module";
import path from "node:path";
import test from "node:test";
import vm from "node:vm";
import ts from "typescript";

const require = createRequire(import.meta.url);
const sourcePath = path.join(process.cwd(), "utils/reportArtifacts.ts");
const source = fs.readFileSync(sourcePath, "utf8");
const { outputText } = ts.transpileModule(source, {
  compilerOptions: {
    module: ts.ModuleKind.CommonJS,
    target: ts.ScriptTarget.ES2020,
  },
});
const moduleContext = { exports: {} };
vm.runInNewContext(outputText, {
  exports: moduleContext.exports,
  module: moduleContext,
  require,
  URL,
  URLSearchParams,
});

const {
  buildReportArtifactLink,
  normalizeOutputPath,
  reportArtifactUnavailableMessage,
  sanitizeResearchId,
} = moduleContext.exports;

test("normalizes encoded absolute output paths", () => {
  assert.equal(
    normalizeOutputPath("%2Fapp%2Foutputs%2Ftask_123.docx", "docx"),
    "/outputs/task_123.docx",
  );
});

test("normalizes relative output paths", () => {
  assert.equal(
    normalizeOutputPath("outputs/nested/report.md", "md"),
    "/outputs/nested/report.md",
  );
  assert.equal(normalizeOutputPath("report.pdf", "pdf"), "/outputs/report.pdf");
});

test("rejects traversal and mismatched extensions", () => {
  assert.equal(
    normalizeOutputPath("/app/outputs/../secret.docx", "docx"),
    null,
  );
  assert.equal(normalizeOutputPath("/app/outputs/report.pdf", "docx"), null);
});

test("uses the report route for DocX when a research id is present", () => {
  const link = buildReportArtifactLink({
    kind: "docx",
    path: "/app/outputs/task_123.docx",
    researchId: "research_123",
  });

  assert.equal(link.ok, true);
  assert.equal(
    link.href,
    "/api/report-artifact?kind=docx&research_id=research_123&path=%2Foutputs%2Ftask_123.docx",
  );
  assert.equal(link.normalizedPath, "/outputs/task_123.docx");
  assert.equal(link.usesResearchId, true);
});

test("sanitizes research ids used by download links", () => {
  assert.equal(sanitizeResearchId("research_123"), "research_123");
  assert.equal(sanitizeResearchId("../research_123"), null);
  assert.equal(sanitizeResearchId("nested/research_123"), null);
});

test("uses human artifact unavailable copy instead of raw backend errors", () => {
  assert.equal(
    reportArtifactUnavailableMessage("docx"),
    "DocX unavailable. Retry, or open Markdown when available.",
  );
  assert.equal(
    reportArtifactUnavailableMessage("md"),
    "Markdown unavailable. Retry after the run finishes syncing artifacts.",
  );
  assert.doesNotMatch(reportArtifactUnavailableMessage("docx"), /Not Found/);
});
