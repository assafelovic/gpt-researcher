import { Page, Locator } from '@playwright/test';

export class HomePageNextJs {
  readonly page: Page;
  readonly inputArea: Locator;
  readonly formContainer: Locator;
  readonly reportContainer: Locator;
  readonly agentLogs: Locator;
  readonly heroSection: Locator;

  constructor(page: Page) {
    this.page = page;
    this.inputArea = page.locator('#input-area');
    this.formContainer = page.locator('#form');
    this.reportContainer = page.locator('#reportContainer');
    this.agentLogs = page.locator('#output');
    this.heroSection = page.locator('header, [class*="hero"], [class*="Hero"]').first();
  }

  async goto() {
    await this.page.goto('/');
  }

  async isLoaded() {
    await this.page.waitForSelector('#input-area, #form', { state: 'visible', timeout: 30_000 });
  }
}
