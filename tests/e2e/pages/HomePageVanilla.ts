import { Page, Locator } from '@playwright/test';

export class HomePageVanilla {
  readonly page: Page;
  readonly form: Locator;
  readonly taskInput: Locator;
  readonly submitButton: Locator;
  readonly reportTypeSelect: Locator;
  readonly toneSelect: Locator;
  readonly reportSourceSelect: Locator;
  readonly output: Locator;
  readonly reportContainer: Locator;
  readonly connectionStatus: Locator;
  readonly landingHeading: Locator;

  constructor(page: Page) {
    this.page = page;
    this.form = page.locator('#researchForm');
    this.taskInput = page.locator('#task');
    this.submitButton = page.locator('#submitButton');
    this.reportTypeSelect = page.locator('#report_type');
    this.toneSelect = page.locator('#tone');
    this.reportSourceSelect = page.locator('#report_source');
    this.output = page.locator('#output');
    this.reportContainer = page.locator('#reportContainer');
    this.connectionStatus = page.locator('#connectionStatus');
    this.landingHeading = page.locator('.landing h1');
  }

  async goto() {
    await this.page.goto('/');
  }

  async isLoaded() {
    await this.page.waitForSelector('#researchForm', { state: 'visible', timeout: 30_000 });
  }

  async fillQuery(query: string) {
    await this.taskInput.fill(query);
  }

  async selectReportType(type: string) {
    await this.reportTypeSelect.selectOption(type);
  }

  async submitResearch() {
    await this.submitButton.click();
  }

  async waitForProgress(timeout = 120_000) {
    await this.page.waitForSelector('#output:not(:empty)', { timeout });
  }

  async waitForReport(timeout = 180_000) {
    await this.page.waitForSelector('#reportContainer:not(:empty)', { timeout });
  }
}
