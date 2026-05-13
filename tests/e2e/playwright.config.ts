import { defineConfig } from '@playwright/test';

const VANILLA_URL = process.env.VANILLA_URL || 'http://localhost:8002';
const NEXTJS_URL = process.env.NEXTJS_URL || 'http://localhost:3000';

export default defineConfig({
  testDir: './specs',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: process.env.CI ? 1 : 1,

  timeout: 120_000,
  expect: { timeout: 30_000 },

  use: {
    headless: process.env.E2E_HEADLESS !== 'false',
    screenshot: 'only-on-failure',
    trace: 'on-first-retry',
  },

  projects: [
    {
      name: 'vanilla',
      use: { baseURL: VANILLA_URL },
      testMatch: 'vanilla/**/*.spec.ts',
    },
    {
      name: 'nextjs',
      use: { baseURL: NEXTJS_URL },
      testMatch: 'nextjs/**/*.spec.ts',
    },
    {
      name: 'api',
      use: { baseURL: VANILLA_URL },
      testMatch: 'shared/**/*.spec.ts',
    },
  ],

  reporter: [
    ['list'],
    ['html', { outputFolder: 'playwright-report' }],
    ['./reporters/github-issue-reporter.ts'],
  ],
});
