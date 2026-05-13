import { test, expect } from '@playwright/test';
import { HomePageVanilla } from '../../pages/HomePageVanilla';
import { ResearchPage } from '../../pages/ResearchPage';
import { ChatPage } from '../../pages/ChatPage';
import { takeScreenshot } from '../../fixtures/setup';
import { TEST_QUERIES, CHAT_MESSAGE } from '../../fixtures/queries';

test.describe('Vanilla Frontend - Chat', () => {
  test('chat with AI after research completes', async ({ page }, testInfo) => {
    test.setTimeout(300_000);

    const home = new HomePageVanilla(page);
    const research = new ResearchPage(page);
    const chat = new ChatPage(page);

    await test.step('Run research first', async () => {
      await home.goto();
      await home.isLoaded();
      await home.fillQuery(TEST_QUERIES.withReport.query);
      await home.submitResearch();
      await research.waitForReport();
      await takeScreenshot(page, testInfo, '01-research-done');
    });

    await test.step('Chat container is visible', async () => {
      const visible = await chat.isVisible();
      expect(visible).toBe(true);
      await takeScreenshot(page, testInfo, '02-chat-visible');
    });

    await test.step('Send chat message and get response', async () => {
      await chat.sendMessage(CHAT_MESSAGE);
      await takeScreenshot(page, testInfo, '03-message-sent');
      await chat.waitForResponse();
      await takeScreenshot(page, testInfo, '04-response-received');

      const messages = await chat.getMessages();
      expect(messages.length).toBeGreaterThanOrEqual(2);
    });
  });
});
