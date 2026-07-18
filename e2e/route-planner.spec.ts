import type { Page } from "@playwright/test";
import { test, expect } from "./fixtures";

/**
 * The planner is a client component with no server-rendered fallback state —
 * the slider, the vehicle picker and "Plan My Route" are all inert until React
 * hydrates. Waiting for network idle gates on the dev-server chunks having
 * loaded and run, which is what makes those interactions stick.
 */
async function gotoPlanner(page: Page) {
  await page.goto("/route-planner");
  await page.waitForLoadState("networkidle");
}

async function planRoute(page: Page, from: string, to: string) {
  await page.locator("#source-input").fill(from);
  await page.locator("#destination-input").fill(to);
  await page.locator("#plan-route-btn").click();
  await expect(page.locator("#route-summary")).toBeVisible();
}

test.describe("route planner page", () => {
  test("renders the planner form with all inputs", async ({ page }) => {
    await gotoPlanner(page);

    await expect(page.locator("#route-planner-form")).toBeVisible();
    await expect(page.locator("#source-input")).toBeVisible();
    await expect(page.locator("#destination-input")).toBeVisible();
    await expect(page.locator("#battery-slider")).toBeVisible();
    await expect(page.locator("#capacity-input")).toBeVisible();
    await expect(page.locator("#plan-route-btn")).toBeVisible();

    // Vehicle type picker — one button per VEHICLE_TYPES entry.
    await expect(page.getByRole("button", { name: /Car/ })).toBeVisible();
    await expect(page.getByRole("button", { name: /Scooter/ })).toBeVisible();
  });

  test("results stay hidden until both source and destination are filled", async ({
    page,
  }) => {
    await gotoPlanner(page);

    const summary = page.locator("#route-summary");
    await expect(summary).toHaveCount(0);

    // Source only — handlePlanRoute requires both, so nothing should appear.
    await page.locator("#source-input").fill("Hyderabad");
    await page.locator("#plan-route-btn").click();
    await expect(summary).toHaveCount(0);

    await planRoute(page, "Hyderabad", "Vizag");
  });

  test("planned route shows summary stats and charging stops", async ({
    page,
  }) => {
    await gotoPlanner(page);
    await planRoute(page, "Hyderabad", "Vizag");

    const summary = page.locator("#route-summary");
    await expect(summary.getByText(/Total Distance/i)).toBeVisible();
    await expect(summary.getByText(/Total Time/i)).toBeVisible();
    await expect(summary.getByText(/Charging Stops/i)).toBeVisible();
    await expect(summary.getByText(/Est\. Charging Cost/i)).toBeVisible();

    await expect(
      page.getByRole("heading", { name: /Recommended Charging Stops/i })
    ).toBeVisible();

    // Stops render as station cards, populated from the station store.
    await expect(page.locator('a[href^="/station/"]').first()).toBeVisible({
      timeout: 20_000,
    });
  });

  test("battery slider updates its label", async ({ page }) => {
    await gotoPlanner(page);

    const label = page.locator("label", { hasText: /Current Battery/ });
    await expect(label).toHaveText(/Current Battery:\s*80%/);

    await page.locator("#battery-slider").fill("35");
    await expect(label).toHaveText(/Current Battery:\s*35%/);
  });

  test("selecting a vehicle type marks it active", async ({ page }) => {
    await gotoPlanner(page);

    const bike = page.getByRole("button", { name: /Bike/ });
    const car = page.getByRole("button", { name: /Car/ });

    // "car" is the default selection — it carries the accent border class.
    await expect(car).toHaveClass(/border-\[var\(--accent\)\]/);

    await bike.click();
    await expect(bike).toHaveClass(/border-\[var\(--accent\)\]/);
    await expect(car).not.toHaveClass(/border-\[var\(--accent\)\]/);
  });
});
