import { chromium } from "playwright";

async function main() {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();

  // Test each variant
  const urls = [
    "http://localhost:5173/",
    "http://127.0.0.1:5173/",
    "http://[::1]:5173/",
  ];

  for (const url of urls) {
    try {
      const resp = await page.request.get(url, { timeout: 5000 });
      console.log(`${url} => ${resp.status()} ${resp.ok()}`);
    } catch (e: any) {
      console.log(`${url} => FAIL: ${e.message?.split('\n')[0]}`);
    }
  }

  await browser.close();
}

main();
