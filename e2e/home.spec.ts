import { test, expect } from "./fixtures";

test.describe("home page", () => {
  test("loads with hero search and featured section", async ({ page }) => {
    await page.goto("/");

    await expect(page).toHaveTitle(/Ev2Ev/i);
    await expect(page.locator("#hero-search-input")).toBeVisible();
    await expect(page.locator("#hero-search-btn")).toBeVisible();

    // Featured stations section is rendered further down the page.
    await expect(page.locator("#featured-section")).toBeAttached();
    await expect(
      page.locator("#featured-section").getByRole("heading").first()
    ).toBeVisible();
  });

  test("typing a city and searching navigates to /search?q=...", async ({
    page,
  }) => {
    await page.goto("/");

    const input = page.locator("#hero-search-input");
    await expect(input).toBeVisible();

    // On a cold dev server, first paint can precede React hydration, so a
    // single fill+click may land before handlers are attached. Retry the
    // interaction until the navigation actually happens.
    await expect(async () => {
      if (!page.url().includes("/search")) {
        await input.fill("Delhi");
        await page.locator("#hero-search-btn").click();
      }
      await expect(page).toHaveURL(/\/search\?q=Delhi/, { timeout: 3_000 });
    }).toPass({ timeout: 40_000 });

    expect(new URL(page.url()).searchParams.get("q")).toBe("Delhi");

    // The search page picks up the query into its own input.
    await expect(page.locator("#search-input")).toHaveValue("Delhi", {
      timeout: 30_000,
    });
  });
});
