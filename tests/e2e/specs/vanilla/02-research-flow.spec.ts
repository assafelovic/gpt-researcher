import { test, expect } from '@playwright/test';
import { HomePageVanilla } from '../../pages/HomePageVanilla';
import { ResearchPage } from '../../pages/ResearchPage';
import { takeScreenshot } from '../../fixtures/setup';
import { TEST_QUERIES } from '../../fixtures/queries';

test.describe('Vanilla Frontend - Research Flow', () => {
  test('full research lifecycle: submit -> progress -> report', async ({ page }, testInfo) => {
    test.setTimeout(300_000);

    const home = new HomePageVanilla(page);
    const research = new ResearchPage(page);

    await test.step('Open homepage and fill form', async () => {
      await home.goto();
      await home.isLoaded();
      await home.fillQuery(TEST_QUERIES.short.query);
      await takeScreenshot(page, testInfo, '01-form-ready');
    });

    await test.step('Submit research', async () => {
      await home.submitResearch();
      await takeScreenshot(page, testInfo, '02-research-submitted');
    });

    await test.step('Progress logs appear', async () => {
      await research.waitForProgress();
      const outputText = await research.output.innerText();
      expect(outputText.length).toBeGreaterThan(0);
      await takeScreenshot(page, testInfo, '03-progress-running');
    });

    await test.step('Report is generated', async () => {
      await research.waitForReport();
      const hasContent = await research.hasReportContent();
      expect(hasContent).toBe(true);
      await takeScreenshot(page, testInfo, '04-report-ready');
    });

    await test.step('Download buttons are visible', async () => {
      await expect(research.downloadLinkMd).toBeVisible();
      await expect(research.downloadLinkPdf).toBeVisible();
      await takeScreenshot(page, testInfo, '05-download-buttons');
    });
  });
});
