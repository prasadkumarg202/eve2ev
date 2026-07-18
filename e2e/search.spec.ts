import { test, expect } from "./fixtures";

test.describe("search page", () => {
  test("renders the search input and results grid or empty state", async ({
    page,
  }) => {
    await page.goto("/search");

    await expect(page.locator("#search-input")).toBeVisible();
    await expect(page.locator("#filter-toggle")).toBeVisible();

    // The results count line always renders ("N results found").
    await expect(page.getByText(/\d+\s+results/i).first()).toBeVisible();

    // Results are shown as station cards, the "no results" empty state, or —
    // in map view (the persisted default; the list panel is lg-only) — the map.
    const stationCards = page.locator('a[href^="/station/"]');
    const noResults = page.getByText(/no charging stations found/i);
    const map = page.locator(".maplibregl-map");
    await expect
      .poll(
        async () => {
          for (const candidate of [stationCards, noResults, map]) {
            if (
              await candidate
                .first()
                .isVisible()
                .catch(() => false)
            ) {
              return true;
            }
          }
          return false;
        },
        { timeout: 20_000, message: "expected station cards, empty state, or map" }
      )
      .toBe(true);
  });

  test("filter toggle opens and closes the filter panel", async ({ page }) => {
    await page.goto("/search");

    // The filter panel is the only place with checkboxes (24x7, free parking).
    const panelCheckboxes = page.getByRole("checkbox");
    const toggle = page.locator("#filter-toggle");
    await expect(toggle).toBeVisible();

    // First paint can precede hydration on a cold dev server, and the panel's
    // open state may be restored from the client store — retry the first
    // toggle until the click provably flips the panel state.
    await expect(async () => {
      const wasOpen = (await panelCheckboxes.count()) > 0;
      await toggle.click();
      if (wasOpen) {
        await expect(panelCheckboxes).toHaveCount(0, { timeout: 2_000 });
      } else {
        await expect(panelCheckboxes.first()).toBeVisible({ timeout: 2_000 });
      }
    }).toPass({ timeout: 30_000 });

    // Hydrated now — toggle once more and assert the state flips back.
    const openNow = (await panelCheckboxes.count()) > 0;
    await toggle.click();
    if (openNow) {
      await expect(panelCheckboxes).toHaveCount(0);
    } else {
      await expect(panelCheckboxes.first()).toBeVisible();
    }
  });

  test("query from the URL is applied to the input", async ({ page }) => {
    await page.goto("/search?q=Mumbai");
    await expect(page.locator("#search-input")).toHaveValue("Mumbai");
  });
});
