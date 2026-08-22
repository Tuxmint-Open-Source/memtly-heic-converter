import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { test, expect } from '@playwright/test';

const baseURL = process.env.MEMTLY_BROWSER_BASE_URL;
const galleryIdentifier = process.env.MEMTLY_BROWSER_GALLERY_IDENTIFIER;
const validFixturePath = process.env.MEMTLY_BROWSER_HEIC_FIXTURE || 'tests/fixtures/heic/heic2any-demo-1.heic';

test.skip(!baseURL || !galleryIdentifier, 'Set MEMTLY_BROWSER_BASE_URL and MEMTLY_BROWSER_GALLERY_IDENTIFIER for runtime browser tests');

test('valid HEIC fixture is converted before Memtly upload and malformed HEIC fails closed', async ({ page }) => {
  await page.goto(`${baseURL.replace(/\/$/, '')}/Gallery?identifier=${encodeURIComponent(galleryIdentifier)}`);

  const form = page.locator('form.file-uploader-form');
  await expect(form).toHaveAttribute('data-client-heic-conversion', 'true');
  await expect(page.locator('input.upload-input')).toHaveAttribute('accept', /\.heic/);

  await page.evaluate(() => {
    window.__memtlyUploadProbe = { requests: [], errors: [] };
    const originalOpen = XMLHttpRequest.prototype.open;
    const originalSend = XMLHttpRequest.prototype.send;
    XMLHttpRequest.prototype.open = function(method, url) {
      this.__probeMethod = method;
      this.__probeUrl = String(url);
      return originalOpen.apply(this, arguments);
    };
    XMLHttpRequest.prototype.send = function(body) {
      if (this.__probeUrl && this.__probeUrl.includes('/Gallery/Upload')) {
        const entry = { method: this.__probeMethod, url: this.__probeUrl, fields: {}, files: [] };
        if (body instanceof FormData) {
          for (const [key, value] of body.entries()) {
            if (value instanceof File || value instanceof Blob) {
              entry.files.push({
                field: key,
                name: value.name || '',
                type: value.type || '',
                size: value.size,
                magicPromise: value.slice(0, 4).arrayBuffer().then(buffer => Array.from(new Uint8Array(buffer)).map(byte => byte.toString(16).padStart(2, '0')).join(''))
              });
            } else {
              entry.fields[key] = String(value);
            }
          }
        }
        Promise.all(entry.files.map(file => file.magicPromise.then(magic => { file.magic = magic; delete file.magicPromise; }))).then(() => {
          window.__memtlyUploadProbe.requests.push(entry);
        }).catch(error => window.__memtlyUploadProbe.errors.push(String(error)));
      }
      return originalSend.apply(this, arguments);
    };
  });

  const input = page.locator('input.upload-input');
  const heic = readFileSync(resolve(validFixturePath));
  const png = Buffer.from('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAFgwJ/lC3v8wAAAABJRU5ErkJggg==', 'base64');
  const malformed = Buffer.from([0xff, 0xd8, 0xff, 0xd9]);

  await input.setInputFiles([
    { name: 'heic2any-demo-1.heic', mimeType: '', buffer: heic },
    { name: 'ordinary.png', mimeType: 'image/png', buffer: png },
    { name: 'malformed.heic', mimeType: 'image/heic', buffer: malformed }
  ]);

  await expect.poll(async () => page.evaluate(() => window.__memtlyUploadProbe.requests.filter(request => request.url.includes('/Gallery/UploadFileChunk')).length), { timeout: 30000 }).toBe(2);
  const probe = await page.evaluate(() => window.__memtlyUploadProbe);
  const uploadedFiles = probe.requests.flatMap(request => request.files).filter(candidate => candidate.field === 'File');
  const converted = uploadedFiles.find(candidate => candidate.name.toLowerCase().endsWith('.jpg'));
  const ordinary = uploadedFiles.find(candidate => candidate.name === 'ordinary.png');

  expect(converted).toBeTruthy();
  expect(converted.type).toBe('image/jpeg');
  expect(converted.magic).toMatch(/^ffd8ff/);

  expect(ordinary).toBeTruthy();
  expect(ordinary.type).toBe('image/png');
  expect(ordinary.magic).toBe('89504e47');

  expect(uploadedFiles.some(candidate => candidate.name.toLowerCase().endsWith('.heic') || candidate.name.toLowerCase().endsWith('.heif'))).toBe(false);

  await expect.poll(
    async () => page.evaluate(() => window.__memtlyUploadProbe.requests.some(request => request.url.includes('/Gallery/UploadCompleted'))),
    { timeout: 30000 }
  ).toBe(true);
});
