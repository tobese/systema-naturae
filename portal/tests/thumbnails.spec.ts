import { test, expect, type Locator, type Page } from '@playwright/test';

const click = (loc: Locator) => loc.dispatchEvent('click');
const waitForTree = (page: Page) => page.waitForSelector('[data-rank]', { timeout: 90_000 });

test.describe('THUMBNAILS', () => {
  test('species panel reserves space and fades in the thumbnail', async ({ page }) => {
    await page.route('**/upload.wikimedia.org/**', async route => {
      await new Promise(r => setTimeout(r, 700));
      await route.continue();
    });

    await page.goto('?family=corvidae');
    await waitForTree(page);

    const species = page.locator('[data-id="PICA_PICA"]');
    await click(species);

    const image = page.locator('img[alt="Eurasian magpie"]');
    await expect(image).toBeVisible();

    const wrapperBefore = await image.evaluate(el => {
      const parent = el.parentElement as HTMLElement | null;
      const rect = parent?.getBoundingClientRect();
      return rect ? { width: rect.width, height: rect.height } : null;
    });

    expect(wrapperBefore).not.toBeNull();
    expect(wrapperBefore!.height).toBeGreaterThan(0);

    const opacityBefore = await image.evaluate(el => getComputedStyle(el).opacity);
    expect(Number.parseFloat(opacityBefore)).toBeLessThan(0.2);

    await expect.poll(async () => Number.parseFloat(await image.evaluate(el => getComputedStyle(el).opacity))).toBeGreaterThan(0.9);

    const wrapperAfter = await image.evaluate(el => {
      const parent = el.parentElement as HTMLElement | null;
      const rect = parent?.getBoundingClientRect();
      return rect ? { width: rect.width, height: rect.height } : null;
    });

    expect(wrapperAfter).not.toBeNull();
    expect(Math.abs(wrapperAfter!.height - wrapperBefore!.height)).toBeLessThan(1);
  });
});
