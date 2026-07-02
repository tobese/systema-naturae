import { test, expect, type Locator, type Page } from '@playwright/test';

// SVG nodes sit inside a D3 zoom container — dispatchEvent bypasses SVG
// pointer-event interception and D3 transition instability checks.
const click = (loc: Locator) => loc.dispatchEvent('click');

// Wait for D3 entrance transitions to finish after a click.
const settle = (ms = 600) => new Promise(r => setTimeout(r, ms));

// Wait for the SVG tree to render (initial build is slow in headless — ~12s).
// Use before any click after a navigation.
const waitForTree = (page: Page) => page.waitForSelector('[data-rank]', { timeout: 90_000 });

const hasParam = (p: string) => new RegExp(`[?&]${p}=`);

// ── KINGDOM ───────────────────────────────────────────────────────────────────

test.describe('KINGDOM', () => {
  test('clicking Animals sets node, clears class and family', async ({ page }) => {
    await page.goto('/?class=AVES&node=AVES');
    await waitForTree(page);
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
    await waitForTree(page);
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
    await waitForTree(page);
    await click(page.locator('[data-rank="CLASS"]').filter({ hasText: 'Birds' }));
    await expect(page).toHaveURL(/[?&]class=AVES/);
    await expect(page).toHaveURL(/[?&]node=AVES/);
    await expect(page).not.toHaveURL(hasParam('family'));
  });

  test('clicking Birds twice toggles class focus off', async ({ page }) => {
    await page.goto('/');
    await waitForTree(page);
    const birds = page.locator('[data-rank="CLASS"]').filter({ hasText: 'Birds' });
    await click(birds);
    await expect(page).toHaveURL(hasParam('class'));
    await click(birds);
    await expect(page).not.toHaveURL(hasParam('class'));
  });

  test('clicking a class from inside a family clears family focus', async ({ page }) => {
    await page.goto('/?family=corvidae');
    await waitForTree(page);
    // Graph is pruned to family subtree — press Escape to unfocus, then click
    await page.keyboard.press('Escape');
    await click(page.locator('[data-rank="CLASS"]').filter({ hasText: 'Birds' }));
    await expect(page).toHaveURL(hasParam('class'));
    await expect(page).not.toHaveURL(hasParam('family'));
  });
});

// ── FAMILY ────────────────────────────────────────────────────────────────────

test.describe('FAMILY', () => {
  test('clicking Canidae from class focus sets family focus', async ({ page }) => {
    // Mammalia orders all have ≤5 families — none are collapsed
    await page.goto('/?class=MAMMALIA&node=MAMMALIA');
    await waitForTree(page);
    await click(page.locator('[data-id="FAM_CANIDAE"]'));
    await expect(page).toHaveURL(/[?&]family=canidae/);
    await expect(page).toHaveURL(hasParam('node'));
    await expect(page).not.toHaveURL(hasParam('class'));
  });

  test('clicking the focused family again clears focus', async ({ page }) => {
    await page.goto('/?family=corvidae');
    await waitForTree(page);
    await click(page.locator('[data-id="FAM_CORVIDAE"]'));
    await expect(page).not.toHaveURL(hasParam('family'));
  });
});

// ── SPECIES ───────────────────────────────────────────────────────────────────

test.describe('SPECIES', () => {
  test('clicking a species sets node param within family context', async ({ page }) => {
    await page.goto('/?family=corvidae');
    await waitForTree(page);
    const species = page.locator('[data-rank="SPECIES"]').first();
    const id = await species.getAttribute('data-id');
    await click(species);
    await expect(page).toHaveURL(new RegExp(`node=${id}`));
    await expect(page).toHaveURL(hasParam('family'));
  });

  test('clicking the same species again deselects it', async ({ page }) => {
    await page.goto('/?family=corvidae');
    await waitForTree(page);
    const species = page.locator('[data-rank="SPECIES"]').first();
    const id = await species.getAttribute('data-id');
    await click(species);
    await expect(page).toHaveURL(new RegExp(`node=${id}`));
    await click(species);
    await expect(page).not.toHaveURL(new RegExp(`node=${id}`));
  });

  test('species with subspecies toggles expansion on click', async ({ page }) => {
    await page.goto('/?family=cetacea');
    await waitForTree(page);
    const bowhead = page.locator('[data-id="BAL_MYS"]');
    // First click: expand subspecies (node appears in URL + subspecies children render)
    await click(bowhead);
    await expect(page).toHaveURL(/[?&]node=BAL_MYS/);
    // After expansion, descendant SUBSPECIES node should be in the tree
    await expect(page.locator('[data-id="BAL_MYS_MYS"]')).toBeAttached();
    // Second click: collapse subspecies (descendant disappears)
    await click(bowhead);
    await expect(page).not.toHaveURL(/[?&]node=BAL_MYS/);
    await expect(page.locator('[data-id="BAL_MYS_MYS"]')).not.toBeAttached();
  });
});

// ── ORDER ────────────────────────────────────────────────────────────────────

test.describe('ORDER', () => {
  test('clicking Carnivora from class focus sets node param', async ({ page }) => {
    await page.goto('/?class=MAMMALIA&node=MAMMALIA');
    await waitForTree(page);
    await click(page.locator('[data-id="CARNIVORA"]'));
    await expect(page).toHaveURL(/[?&]node=CARNIVORA/);
  });

  test('clicking an order sets node param, preserves class, no family', async ({ page }) => {
    await page.goto('/?class=MAMMALIA&node=MAMMALIA');
    await waitForTree(page);
    await click(page.locator('[data-id="CARNIVORA"]'));
    await expect(page).toHaveURL(/[?&]node=CARNIVORA/);
    await expect(page).toHaveURL(hasParam('class'));
    await expect(page).not.toHaveURL(hasParam('family'));
  });
});

// ── GENUS ────────────────────────────────────────────────────────────────────

test.describe('GENUS', () => {
  test('clicking a genus sets node param within family context', async ({ page }) => {
    await page.goto('/?family=corvidae');
    await waitForTree(page);
    await click(page.locator('[data-id="GENUS_PICA"]'));
    await expect(page).toHaveURL(/[?&]node=GENUS_PICA/);
    await expect(page).toHaveURL(hasParam('family'));
  });

  test('clicking same genus again deselects it', async ({ page }) => {
    await page.goto('/?family=corvidae');
    await waitForTree(page);
    const genus = page.locator('[data-id="GENUS_PICA"]');
    await click(genus);
    await expect(page).toHaveURL(/[?&]node=GENUS_PICA/);
    await click(genus);
    await expect(page).not.toHaveURL(/[?&]node=GENUS_PICA/);
  });
});

// ── SUBFAMILY ────────────────────────────────────────────────────────────────

test.describe('SUBFAMILY', () => {
  test('clicking a subfamily sets node param within family context', async ({ page }) => {
    await page.goto('/?family=alcedinidae');
    await waitForTree(page);
    await click(page.locator('[data-id="SUBFAM_ALCEDININAE"]'));
    await expect(page).toHaveURL(/[?&]node=SUBFAM_ALCEDININAE/);
    await expect(page).toHaveURL(hasParam('family'));
  });
});

// ── SUBSPECIES ───────────────────────────────────────────────────────────────

test.describe('SUBSPECIES', () => {
  test('clicking a subspecies sets node param (no zoom, no expand)', async ({ page }) => {
    await page.goto('/?family=cetacea&node=BAL_MYS');
    await waitForTree(page);
    // Subspecies only renders after parent species is expanded
    const parent = page.locator('[data-id="BAL_MYS"]');
    await click(parent);
    await settle();
    const sub = page.locator('[data-id="BAL_MYS_MYS"]');
    await expect(sub).toBeAttached();
    const subId = await sub.getAttribute('data-id');
    await click(sub);
    await expect(page).toHaveURL(new RegExp(`node=${subId}`));
    await expect(page).toHaveURL(hasParam('family'));
  });
});

// ── BREED_GROUP ──────────────────────────────────────────────────────────────

test.describe('BREED_GROUP', () => {
  test('clicking a breed group toggles expansion of its parent species', async ({ page }) => {
    await page.goto('/?family=equidae');
    await waitForTree(page);
    // Expand domestic horse species to reveal breed groups
    const horse = page.locator('[data-id="DOMESTIC_HORSE"]');
    await click(horse);
    await settle();
    const bg = page.locator('[data-id="breed-group-racing"]');
    await expect(bg).toBeAttached();
    // Click the breed group to select it
    await click(bg);
    await expect(page).toHaveURL(/[?&]node=breed-group-racing/);
    await expect(page).toHaveURL(hasParam('family'));
  });
});

// ── HYBRID ───────────────────────────────────────────────────────────────────

test.describe('HYBRID', () => {
  test('clicking a hybrid sets node param within family context', async ({ page }) => {
    await page.goto('/?family=equidae');
    await waitForTree(page);
    const hybrid = page.locator('[data-id="hybrid-mule"]');
    await click(hybrid);
    await expect(page).toHaveURL(/[?&]node=hybrid-mule/);
    await expect(page).toHaveURL(hasParam('family'));
  });
});

// ── CROSS-FAMILY ─────────────────────────────────────────────────────────────

test.describe('CROSS-FAMILY', () => {
  test('clicking a family from class focus navigates to that family', async ({ page }) => {
    await page.goto('/?class=MAMMALIA&node=MAMMALIA');
    await waitForTree(page);
    await click(page.locator('[data-id="FAM_CANIDAE"]'));
    await expect(page).toHaveURL(/[?&]family=canidae/);
    await expect(page).not.toHaveURL(hasParam('class'));
  });
});

// ── FAMILY COLLAPSE ──────────────────────────────────────────────────────────

test.describe('FAMILY COLLAPSE', () => {
  test('family with >30 genera expands fully when focused (not collapsed to a dot)', async ({ page }) => {
    // Labridae has 76 genus children — default collapse threshold is 30.
    // Without the focusedFamilySlug guard, this would collapse to a single dot.
    await page.goto('/?family=labridae&node=FAM_LABRIDAE');
    await waitForTree(page);
    await settle(800);
    // At least 31 GENUS nodes must be in the tree — proves no collapse.
    await expect(page.locator('[data-rank="GENUS"]').nth(30)).toBeAttached();
  });
});

// ── KEYBOARD ─────────────────────────────────────────────────────────────────

test.describe('KEYBOARD', () => {
  test('Escape clears family focus', async ({ page }) => {
    await page.goto('/?family=corvidae');
    await waitForTree(page);
    await page.keyboard.press('Escape');
    await expect(page).not.toHaveURL(hasParam('family'));
    await expect(page).not.toHaveURL(hasParam('class'));
    await expect(page).not.toHaveURL(hasParam('node'));
  });

  test('Escape clears class focus', async ({ page }) => {
    await page.goto('/?class=AVES&node=AVES');
    await waitForTree(page);
    await page.keyboard.press('Escape');
    await expect(page).not.toHaveURL(hasParam('class'));
  });

  test('ArrowRight navigates to next sibling', async ({ page }) => {
    await page.goto('/?family=corvidae&node=GENUS_PICA');
    await waitForTree(page);
    await page.keyboard.press('ArrowRight');
    // Should have moved to next genus sibling
    await expect(page).toHaveURL(/[?&]node=/);
    await expect(page).toHaveURL(hasParam('family'));
    // The node should NOT be GENUS_PICA anymore
    await expect(page).not.toHaveURL(/[?&]node=GENUS_PICA/);
  });

  test('ArrowLeft navigates to previous sibling', async ({ page }) => {
    await page.goto('/?family=corvidae&node=GENUS_PICA');
    await waitForTree(page);
    await page.keyboard.press('ArrowLeft');
    await expect(page).toHaveURL(/[?&]node=/);
    await expect(page).toHaveURL(hasParam('family'));
    await expect(page).not.toHaveURL(/[?&]node=GENUS_PICA/);
  });

  test('ArrowUp navigates to parent node', async ({ page }) => {
    await page.goto('/?family=corvidae&node=PICA_PICA');
    await waitForTree(page);
    await page.keyboard.press('ArrowUp');
    // Should have moved to parent genus
    await expect(page).toHaveURL(/[?&]node=GENUS_PICA/);
    await expect(page).toHaveURL(hasParam('family'));
  });

  test('C key centers on selected node', async ({ page }) => {
    await page.goto('/?family=corvidae&node=GENUS_PICA');
    await waitForTree(page);
    // Press C — should not change URL, just re-center
    await page.keyboard.press('c');
    await expect(page).toHaveURL(/[?&]node=GENUS_PICA/);
    await expect(page).toHaveURL(hasParam('family'));
  });
});

// ── SEARCH ───────────────────────────────────────────────────────────────────

test.describe('SEARCH', () => {
  test('searching and clicking a result navigates to that node', async ({ page }) => {
    await page.goto('/');
    await waitForTree(page);
    await page.locator('input[placeholder="Search…"]').fill('Pica pica');
    await settle(1000);
    await page.getByText('Pica pica').first().click();
    await expect(page).toHaveURL(hasParam('family'));
    await expect(page).toHaveURL(hasParam('node'));
  });
});
