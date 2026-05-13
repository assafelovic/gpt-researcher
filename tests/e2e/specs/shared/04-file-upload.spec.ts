import { test, expect } from '@playwright/test';
import { takeScreenshot } from '../../fixtures/setup';
import { API_BASE } from '../../fixtures/queries';
import * as fs from 'node:fs';
import * as path from 'node:path';

test.describe('API - File Upload', () => {
  const screenshotDir = path.resolve(process.cwd(), 'screenshots', 'api');
  const tmpFile = path.resolve(screenshotDir, 'test-upload.txt');

  test.afterEach(() => {
    if (fs.existsSync(tmpFile)) fs.unlinkSync(tmpFile);
  });

  test('upload file and verify it appears in file list', async ({ page, request }, testInfo) => {
    await test.step('Create test file and upload', async () => {
      fs.mkdirSync(screenshotDir, { recursive: true });
      fs.writeFileSync(tmpFile, 'GPT Researcher E2E Test Content');
      const fileBuffer = fs.readFileSync(tmpFile);

      const uploadResp = await request.post(`${API_BASE}/upload/`, {
        multipart: {
          file: {
            name: 'test-upload.txt',
            mimeType: 'text/plain',
            buffer: fileBuffer,
          },
        },
      });

      expect(uploadResp.ok()).toBe(true);
      if (testInfo.project.name === 'api') {
        await takeScreenshot(page, testInfo, '01-upload-response');
      }
    });

    await test.step('File appears in file list', async () => {
      const listResp = await request.get(`${API_BASE}/files/`);
      expect(listResp.ok()).toBe(true);
      const body = await listResp.json();
      expect(body.files).toBeDefined();
      expect(body.files).toContain('test-upload.txt');
    });

    await test.step('Delete uploaded file', async () => {
      const delResp = await request.delete(`${API_BASE}/files/test-upload.txt`);
      expect(delResp.ok()).toBe(true);
    });
  });
});
