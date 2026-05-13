import { test, expect } from '@playwright/test';
import { HomePageVanilla } from '../../pages/HomePageVanilla';
import { takeScreenshot } from '../../fixtures/setup';

test.describe('Vanilla Frontend - Homepage', () => {
  test('homepage loads with all key elements', async ({ page }, testInfo) => {
    const home = new HomePageVanilla(page);

    await test.step('Open homepage', async () => {
      await home.goto();
      await home.isLoaded();
      await takeScreenshot(page, testInfo, '01-page-loaded');
    });

    await test.step('Hero heading is visible', async () => {
      await expect(home.landingHeading).toBeVisible();
      await takeScreenshot(page, testInfo, '02-hero-visible');
    });

    await test.step('Research form is visible with all fields', async () => {
      await expect(home.taskInput).toBeVisible();
      await expect(home.reportTypeSelect).toBeVisible();
      await expect(home.toneSelect).toBeVisible();
      await expect(home.reportSourceSelect).toBeVisible();
      await expect(home.submitButton).toBeVisible();
      await takeScreenshot(page, testInfo, '03-form-visible');
    });

    await test.step('Connection status indicator is present', async () => {
      await expect(home.connectionStatus).toBeVisible();
    });
  });

  test('form fields are interactive', async ({ page }, testInfo) => {
    const home = new HomePageVanilla(page);
    await home.goto();
    await home.isLoaded();

    await test.step('Fill query input', async () => {
      await home.fillQuery('KI in der Medizin');
      const value = await home.taskInput.inputValue();
      expect(value).toBe('KI in der Medizin');
      await takeScreenshot(page, testInfo, '01-query-filled');
    });

    await test.step('Select report type', async () => {
      await home.selectReportType('detailed_report');
      const value = await home.reportTypeSelect.inputValue();
      expect(value).toBe('detailed_report');
    });

    await test.step('Select tone', async () => {
      await home.toneSelect.selectOption('Analytical');
      const value = await home.toneSelect.inputValue();
      expect(value).toBe('Analytical');
    });
  });
});
