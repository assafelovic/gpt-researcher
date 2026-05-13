import { Page, Locator } from '@playwright/test';

export class ChatPage {
  readonly page: Page;
  readonly chatContainer: Locator;
  readonly chatInput: Locator;
  readonly sendButton: Locator;
  readonly chatMessages: Locator;

  constructor(page: Page) {
    this.page = page;
    this.chatContainer = page.locator('#chatContainer');
    this.chatInput = page.locator('#chatInput');
    this.sendButton = page.locator('#sendChatBtn');
    this.chatMessages = page.locator('#chatMessages');
  }

  async sendMessage(message: string) {
    await this.chatInput.fill(message);
    await this.sendButton.click();
  }

  async waitForResponse(timeout = 60_000) {
    await this.page.waitForSelector('#chatMessages > :not(:empty)', { timeout });
  }

  async getMessages(): Promise<string[]> {
    const messageElements = await this.chatMessages.locator('> div').all();
    const texts: string[] = [];
    for (const el of messageElements) {
      texts.push(await el.innerText());
    }
    return texts;
  }

  async isVisible(): Promise<boolean> {
    return await this.chatContainer.isVisible();
  }
}
