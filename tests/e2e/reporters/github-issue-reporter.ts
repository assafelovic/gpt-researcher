import type { Reporter, TestCase, TestResult, FullResult } from '@playwright/test/reporter';
import { execSync } from 'node:child_process';
import * as path from 'node:path';
import * as fs from 'node:fs';

interface FailureEntry {
  test: TestCase;
  result: TestResult;
}

export default class GitHubIssueReporter implements Reporter {
  private failures: FailureEntry[] = [];

  onTestEnd(test: TestCase, result: TestResult) {
    if (result.status !== 'passed') {
      this.failures.push({ test, result });
    }
  }

  async onEnd(result: FullResult) {
    if (this.failures.length === 0) return;
    if (!process.env.GITHUB_TOKEN && !this._ghCliAvailable()) {
      console.log(
        '\n[GitHubIssueReporter] No GITHUB_TOKEN and no `gh` CLI. Skipping issues.\n',
      );
      return;
    }

    for (const { test, result: testResult } of this.failures) {
      try {
        await this._createIssue(test, testResult);
      } catch (err) {
        console.error(`[GitHubIssueReporter] Failed to create issue for "${test.title}":`, err);
      }
    }
  }

  private _createIssue(test: TestCase, result: TestResult) {
    const title = this._buildTitle(test);
    const body = this._buildBody(test, result);

    if (process.env.GITHUB_TOKEN) {
      this._createIssueViaApi(title, body);
    } else {
      this._createIssueViaGhCli(title, body);
    }
  }

  private _buildTitle(test: TestCase): string {
    return `[E2E] ${test.title} failed`;
  }

  private _buildBody(test: TestCase, result: TestResult): string {
    const project = test.titlePath()[0] || 'unknown';
    const file = test.location.file;
    const line = test.location.line;

    const lines = [
      '## E2E-Test fehlgeschlagen',
      '',
      `**Projekt:** \`${project}\``,
      `**Datei:** \`${file}:${line}\``,
      `**Test:** ${test.title}`,
      '',
      '### Fehler',
      '```',
      result.error?.message || 'Unknown error',
      '```',
      '',
      '### Stack Trace',
      '```',
      result.error?.stack || 'N/A',
      '```',
      '',
      '### Screenshots',
    ];

    const screenshots = result.attachments.filter(
      a => a.contentType?.startsWith('image/'),
    );

    if (screenshots.length > 0) {
      for (const att of screenshots) {
        lines.push(`- ${att.name}`);
      }
    } else {
      lines.push('_Keine Screenshots verfuegbar._');
    }

    lines.push('', '### Dauer', `${result.duration}ms`);
    lines.push('', '---', '_Automatisch erstellt vom GitHubIssueReporter_');

    return lines.join('\n');
  }

  private _createIssueViaApi(title: string, body: string) {
    const token = process.env.GITHUB_TOKEN!;
    const repo = process.env.GITHUB_REPO || 'assafelovic/gpt-researcher';

    const payload = JSON.stringify({ title, body, labels: ['e2e-test'] });

    try {
      const output = execSync(
        `curl -s -X POST "https://api.github.com/repos/${repo}/issues" \
          -H "Authorization: token ${token}" \
          -H "Accept: application/vnd.github.v3+json" \
          -d @-`,
        { input: payload, timeout: 15_000, encoding: 'utf-8' },
      );
      const data = JSON.parse(output);
      if (data.html_url) {
        console.log(`\n[GitHubIssueReporter] Issue created: ${data.html_url}\n`);
      }
    } catch (err) {
      console.error('[GitHubIssueReporter] API call failed:', err);
    }
  }

  private _createIssueViaGhCli(title: string, body: string) {
    const repo = process.env.GITHUB_REPO || 'assafelovic/gpt-researcher';
    const bodyPath = path.resolve(process.cwd(), '.gh-issue-body.md');

    try {
      fs.writeFileSync(bodyPath, body, 'utf-8');
      const cmd = `gh issue create --repo "${repo}" --title '${title}' --body-file "${bodyPath}" --label "e2e-test"`;
      const output = execSync(cmd, { timeout: 15_000, encoding: 'utf-8' });
      console.log(`\n[GitHubIssueReporter] Issue created: ${output.trim()}\n`);
    } catch (err) {
      console.error('[GitHubIssueReporter] gh CLI failed:', err);
    } finally {
      if (fs.existsSync(bodyPath)) fs.unlinkSync(bodyPath);
    }
  }

  private _ghCliAvailable(): boolean {
    try {
      execSync('gh --version', { stdio: 'ignore' });
      return true;
    } catch {
      return false;
    }
  }
}
