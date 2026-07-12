import { defineConfig } from '@playwright/test';

export default defineConfig({
  testDir: './tests',
  timeout: 120_000,
  use: {
    baseURL: 'http://localhost:5173',
    headless: true,
  },
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:5173',
    reuseExistingServer: true,
    // `npm run dev` first runs buildData.sh (rebuilds the taxonomy) before Vite,
    // which routinely exceeds the default 60s on a cold cache.
    timeout: 180_000,
  },
});
