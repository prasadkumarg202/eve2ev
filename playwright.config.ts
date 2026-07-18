import { defineConfig, devices } from "@playwright/test";

/**
 * Playwright E2E configuration for Ev2Ev.
 *
 * - Reuses an already-running dev server on :3000, otherwise starts one.
 * - Desktop Chrome plus two mobile emulation projects (Android + iOS) so the
 *   PWA/mobile layout (bottom nav, responsive breakpoints) is exercised.
 */
export default defineConfig({
  testDir: "./e2e",
  outputDir: "./test-results",
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  reporter: [["list"], ["html", { open: "never" }]],
  timeout: 45_000,
  expect: { timeout: 10_000 },
  use: {
    baseURL: "http://localhost:3000",
    trace: "on-first-retry",
    navigationTimeout: 30_000,
    actionTimeout: 15_000,
  },
  webServer: {
    command: "npm run dev",
    url: "http://localhost:3000",
    reuseExistingServer: true,
    timeout: 120_000,
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "mobile-android",
      use: { ...devices["Pixel 7"] },
    },
    {
      name: "mobile-ios",
      // iPhone 14 runs on the real WebKit engine (installed via
      // `npx playwright install webkit`).
      use: { ...devices["iPhone 14"] },
    },
  ],
});
