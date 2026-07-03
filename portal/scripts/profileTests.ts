import { chromium } from "playwright";
import { writeFileSync, mkdirSync } from "fs";
import { resolve } from "path";

const profileDir = resolve(import.meta.dirname, "../profiles");
mkdirSync(profileDir, { recursive: true });

async function main() {
  const browser = await chromium.launch({ headless: false });
  const page = await browser.newPage({ viewport: { width: 1280, height: 900 } });
  const cdp = await page.context().newCDPSession(page);

  const events: any[] = [];
  cdp.on("Tracing.dataCollected", (p: any) => {
    if (p.value) events.push(...p.value);
  });

  await cdp.send("Tracing.start", {
    traceConfig: {
      recordMode: "recordContinuously",
      includedCategories: ["blink", "blink.user_timing", "devtools.timeline", "disabled-by-default-devtools.timeline", "loading", "latency"],
    },
  });

  try {
    console.log("1/6  Loading home page...");
    await page.goto("http://localhost:5173", { waitUntil: "domcontentloaded", timeout: 30_000 });
    await page.waitForSelector("text=Mammals", { timeout: 30_000 });
    console.log(`     ${Date.now()}ms`);

    console.log("2/6  Clicking Mammalia class...");
    await page.evaluate(() => {
      document.querySelector('[data-rank="CLASS"][data-id="MAMMALIA"]')?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    });
    await page.waitForTimeout(2000);

    console.log("3/6  Clicking Carnivora (lazy-load)...");
    await page.evaluate(() => {
      document.querySelector('[data-id="CARNIVORA"]')?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    });
    await page.waitForSelector('[data-rank="FAMILY"]', { timeout: 20_000 });
    await page.waitForTimeout(1000);

    console.log("4/6  Focusing Canidae family...");
    await page.evaluate(() => {
      document.querySelector('[data-id="FAM_CANIDAE"]')?.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    });
    await page.waitForTimeout(2000);

    console.log("5/6  Deep-link to corvidae...");
    await page.goto("http://localhost:5173/?family=corvidae", { waitUntil: "domcontentloaded", timeout: 30_000 });
    await page.waitForSelector('[data-rank="GENUS"]', { timeout: 30_000 });
    await page.waitForTimeout(2000);

  } catch (err) {
    console.error("Error during test:", err instanceof Error ? err.message : err);
  } finally {
    console.log("6/6  Stopping trace...");
    await cdp.send("Tracing.end").catch(() => {});
    await page.waitForTimeout(2000);

    const trace = { traceEvents: events };
    const tracePath = resolve(profileDir, "full-session.json");
    writeFileSync(tracePath, JSON.stringify(trace, null, 2));
    console.log(`     Saved ${events.length} events to profiles/full-session.json`);

    await browser.close();
  }
}

main();
