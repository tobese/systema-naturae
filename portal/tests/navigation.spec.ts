import { test, expect, type Locator } from '@playwright/test';

// SVG nodes sit inside a D3 zoom container — dispatchEvent bypasses SVG
// pointer-event interception and D3 transition instability checks.
const click = (loc: Locator) => loc.dispatchEvent('click');

// Wait for D3 entrance transitions to finish before clicking.
const settle = (ms = 600) => new Promise(r => setTimeout(r, ms));

const hasParam = (p: string) => new RegExp(`[?&]${p}=`);

// ── KINGDOM ───────────────────────────────────────────────────────────────────

test.describe('KINGDOM', () => {
  test('clicking Animals sets node, clears class and family', async ({ page }) => {
    await page.goto('/?class=AVES&node=AVES');
    await page.waitForTimeout(600);
    await click(page.locator('[data-rank="KINGDOM"]'));
    await expect(page).toHaveURL(hasParam('node'));
    await expect(page).not.toHaveURL(hasParam('class'));
    await expect(page).not.toHaveURL(hasParam('family'));
  });
});

// ── PHYLUM ────────────────────────────────────────────────────────────────────

test.describe('PHYLUM', () => {
  test('clicking Chordates sets node, clears class and family', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(600);
    await click(page.locator('[data-rank="PHYLUM"]').filter({ hasText: 'Chordates' }));
    await expect(page).toHaveURL(hasParam('node'));
    await expect(page).not.toHaveURL(hasParam('class'));
    await expect(page).not.toHaveURL(hasParam('family'));
  });
});

// ── CLASS ─────────────────────────────────────────────────────────────────────

test.describe('CLASS', () => {
  test('clicking Birds sets class and node params', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(600);
    await click(page.locator('[data-rank="CLASS"]').filter({ hasText: 'Birds' }));
    await expect(page).toHaveURL(/[?&]class=AVES/);
    await expect(page).toHaveURL(/[?&]node=AVES/);
    await expect(page).not.toHaveURL(hasParam('family'));
  });

  test('clicking Birds twice toggles class focus off', async ({ page }) => {
    await page.goto('/');
    await page.waitForTimeout(600);
    const birds = page.locator('[data-rank="CLASS"]').filter({ hasText: 'Birds' });
    await click(birds);
    await expect(page).toHaveURL(hasParam('class'));
    await click(birds);
    await expect(page).not.toHaveURL(hasParam('class'));
  });

  test('clicking a class from inside a family clears family focus', async ({ page }) => {
    await page.goto('/?family=corvidae');
    await page.waitForTimeout(600);
    await click(page.locator('[data-rank="CLASS"]').filter({ hasText: 'Birds' }));
    await expect(page).toHaveURL(hasParam('class'));
    await expect(page).not.toHaveURL(hasParam('family'));
  });
});

// ── FAMILY ────────────────────────────────────────────────────────────────────
// Family nodes in the global radial tree are very small — start from class
// focus so Corvidae is prominently rendered.

test.describe('FAMILY', () => {
  test('clicking Corvidae sets family focus, clears class', async ({ page }) => {
    await page.goto('/?class=AVES&node=AVES');
    await page.waitForTimeout(600);
    await click(page.locator('[data-id="FAM_CORVIDAE"]'));
    await expect(page).toHaveURL(/[?&]family=corvidae/);
    await expect(page).toHaveURL(hasParam('node'));
    await expect(page).not.toHaveURL(hasParam('class'));
  });

  test('clicking the focused family again clears focus', async ({ page }) => {
    await page.goto('/?family=corvidae');
    await page.waitForTimeout(600);
    await click(page.locator('[data-id="FAM_CORVIDAE"]'));
    await expect(page).not.toHaveURL(hasParam('family'));
  });

  test('clicking a family from class focus clears class, sets family', async ({ page }) => {
    await page.goto('/?class=AVES&node=AVES');
    await page.waitForTimeout(600);
    await click(page.locator('[data-id="FAM_CORVIDAE"]'));
    await expect(page).toHaveURL(/[?&]family=corvidae/);
    await expect(page).not.toHaveURL(hasParam('class'));
  });
});

// ── SPECIES ───────────────────────────────────────────────────────────────────

test.describe('SPECIES', () => {
  test('clicking a species sets node param within family context', async ({ page }) => {
    await page.goto('/?family=corvidae');
    await page.waitForTimeout(600);
    const species = page.locator('[data-rank="SPECIES"]').first();
    const id = await species.getAttribute('data-id');
    await click(species);
    await expect(page).toHaveURL(new RegExp(`node=${id}`));
    await expect(page).toHaveURL(hasParam('family'));
  });

  test('clicking the same species again deselects it', async ({ page }) => {
    await page.goto('/?family=corvidae');
    await page.waitForTimeout(600);
    const species = page.locator('[data-rank="SPECIES"]').first();
    const id = await species.getAttribute('data-id');
    await click(species);
    await expect(page).toHaveURL(new RegExp(`node=${id}`));
    await click(species);
    await expect(page).not.toHaveURL(new RegExp(`node=${id}`));
  });
});
