import { Page, Locator } from '@playwright/test';

export class ResearchPage {
  readonly page: Page;
  readonly output: Locator;
  readonly reportContainer: Locator;
  readonly downloadLinkMd: Locator;
  readonly downloadLinkPdf: Locator;
  readonly chatContainer: Locator;

  constructor(page: Page) {
    this.page = page;
    this.output = page.locator('#output');
    this.reportContainer = page.locator('#reportContainer');
    this.downloadLinkMd = page.locator('#downloadLinkMd');
    this.downloadLinkPdf = page.locator('#downloadLink');
    this.chatContainer = page.locator('#chatContainer');
  }

  async waitForProgress(timeout = 120_000) {
    await this.page.waitForSelector('#output:not(:empty)', { timeout });
  }

  async waitForReport(timeout = 180_000) {
    await this.page.waitForSelector('#reportContainer:not(:empty)', { timeout });
  }

  async hasReportContent(): Promise<boolean> {
    const text = await this.reportContainer.innerText();
    return text.trim().length > 0;
  }

  async getReportText(): Promise<string> {
    return await this.reportContainer.innerText();
  }
}
