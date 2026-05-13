import { test, expect } from '@playwright/test';
import { HomePageNextJs } from '../../pages/HomePageNextJs';
import { ResearchPage } from '../../pages/ResearchPage';
import { takeScreenshot } from '../../fixtures/setup';
import { TEST_QUERIES } from '../../fixtures/queries';

test.describe('Next.js Frontend - Research Flow', () => {
  test('research lifecycle through Next.js UI', async ({ page }, testInfo) => {
    test.setTimeout(300_000);

    const home = new HomePageNextJs(page);
    const research = new ResearchPage(page);

    await test.step('Open Next.js frontend', async () => {
      await home.goto();
      await home.isLoaded();
      await takeScreenshot(page, testInfo, '01-home-loaded');
    });

    await test.step('Research progresses', async () => {
      await research.waitForProgress();
      const outputText = await research.output.innerText();
      expect(outputText.length).toBeGreaterThan(0);
      await takeScreenshot(page, testInfo, '02-progress');
    });

    await test.step('Report is generated', async () => {
      await research.waitForReport();
      const hasContent = await research.hasReportContent();
      expect(hasContent).toBe(true);
      await takeScreenshot(page, testInfo, '03-report-ready');
    });
  });
});
