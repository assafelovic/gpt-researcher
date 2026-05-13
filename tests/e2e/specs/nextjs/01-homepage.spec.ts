import { test, expect } from '@playwright/test';
import { HomePageNextJs } from '../../pages/HomePageNextJs';
import { takeScreenshot } from '../../fixtures/setup';

test.describe('Next.js Frontend - Homepage', () => {
  test('homepage loads with key sections', async ({ page }, testInfo) => {
    const home = new HomePageNextJs(page);

    await test.step('Open Next.js frontend', async () => {
      await home.goto();
      await home.isLoaded();
      await takeScreenshot(page, testInfo, '01-page-loaded');
    });

    await test.step('Input area is present', async () => {
      await expect(home.inputArea).toBeVisible();
      await takeScreenshot(page, testInfo, '02-input-area');
    });

    await test.step('Form container is rendered', async () => {
      await expect(home.formContainer).toBeVisible();
      await takeScreenshot(page, testInfo, '03-form-container');
    });
  });
});
