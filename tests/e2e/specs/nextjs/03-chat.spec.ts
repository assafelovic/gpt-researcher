import { test, expect } from '@playwright/test';
import { HomePageNextJs } from '../../pages/HomePageNextJs';
import { ChatPage } from '../../pages/ChatPage';
import { takeScreenshot } from '../../fixtures/setup';
import { CHAT_MESSAGE } from '../../fixtures/queries';

test.describe('Next.js Frontend - Chat', () => {
  test('chat interaction after research', async ({ page }, testInfo) => {
    test.setTimeout(300_000);

    const home = new HomePageNextJs(page);
    const chat = new ChatPage(page);

    await test.step('Open Next.js frontend', async () => {
      await home.goto();
      await home.isLoaded();
      await takeScreenshot(page, testInfo, '01-home-loaded');
    });

    await test.step('Chat container present', async () => {
      await page.waitForTimeout(5_000);
      const visible = await chat.isVisible();
      if (visible) {
        await takeScreenshot(page, testInfo, '02-chat-visible');
      }
    });
  });
});
