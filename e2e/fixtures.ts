import { test as base, expect } from "@playwright/test";

/**
 * Shared test fixture: marks the PWA install prompt as already dismissed so
 * its fixed overlay banner never intercepts taps (it otherwise shows up on
 * mobile/iOS user agents and covers form buttons and the bottom nav).
 */
export const test = base.extend({
  page: async ({ page }, use) => {
    await page.addInitScript(() => {
      try {
        window.localStorage.setItem(
          "ev2ev-install-dismissed",
          String(Date.now())
        );
      } catch {
        /* storage unavailable — banner may show, tests stay best-effort */
      }
    });
    await use(page);
  },
});

export { expect };
