import { Page, TestInfo } from '@playwright/test';
import * as path from 'node:path';

const SCREENSHOT_DIR = process.env.SCREENSHOT_DIR || path.resolve(process.cwd(), 'screenshots');

export function screenshotPath(projectName: string, testName: string, step: string): string {
  const dir = path.join(SCREENSHOT_DIR, projectName, sanitize(testName));
  return path.join(dir, `${sanitize(step)}.png`);
}

function sanitize(s: string): string {
  return s.replace(/[^a-zA-Z0-9_-]/g, '_').slice(0, 100);
}

export async function takeScreenshot(
  page: Page,
  testInfo: TestInfo,
  stepName: string,
): Promise<string> {
  const project = testInfo.project.name;
  const test = testInfo.title;
  const filePath = screenshotPath(project, test, stepName);
  const dir = path.dirname(filePath);
  const { mkdir } = await import('node:fs/promises');
  await mkdir(dir, { recursive: true });
  await page.screenshot({ path: filePath, fullPage: true });
  return filePath;
}

export function buildIssueBody(
  testInfo: TestInfo,
  error: Error | undefined,
  screenshotFiles: string[],
): string {
  const lines = [
    `## ❌ E2E-Test fehlgeschlagen`,
    ``,
    `**Frontend:** \`${testInfo.project.name}\``,
    `**File:** \`${testInfo.file}\``,
    `**Test:** ${testInfo.title}`,
    error ? `**Error:** \`${error.message}\`\n` : '',
    `### Screenshots:`,
    ...screenshotFiles.map(f => `- \`${f}\``),
    ``,
    error?.stack
      ? `### Stack Trace:\n\`\`\`\n${error.stack}\n\`\`\``
      : '',
  ];
  return lines.filter(l => l !== '').join('\n');
}

export function buildIssueTitle(testInfo: TestInfo): string {
  return `E2E: ${testInfo.title} (${testInfo.project.name})`;
}
