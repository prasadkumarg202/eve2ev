import { test, expect } from "./fixtures";

test.describe("mobile bottom navigation", () => {
  test("bottom nav visibility matches the viewport", async ({
    page,
    isMobile,
  }) => {
    await page.goto("/");

    const nav = page.locator("#mobile-bottom-nav");
    await expect(nav).toBeAttached();

    if (isMobile) {
      await expect(nav).toBeVisible();
      await expect(nav.getByRole("link")).toHaveCount(4);
    } else {
      // md:hidden — the nav exists in the DOM but is display:none on desktop.
      await expect(nav).toBeHidden();
    }
  });

  test("search tab navigates to /search", async ({ page, isMobile }) => {
    test.skip(!isMobile, "Bottom nav is only shown on mobile viewports");

    await page.goto("/");
    const nav = page.locator("#mobile-bottom-nav");
    await expect(nav).toBeVisible();

    // The tab bar re-renders while auth state resolves, which keeps the link
    // from ever passing Playwright's stability check on slow dev loads. It is
    // a plain anchor, so a forced click still navigates; retry until it does.
    await expect(async () => {
      if (!page.url().includes("/search")) {
        await nav
          .getByRole("link", { name: /search/i })
          .click({ timeout: 5_000, force: true });
      }
      await expect(page).toHaveURL(/\/search/, { timeout: 3_000 });
    }).toPass({ timeout: 30_000 });

    await expect(page.locator("#search-input")).toBeVisible({
      timeout: 30_000,
    });
  });
});
