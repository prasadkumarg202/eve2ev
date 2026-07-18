import { test, expect } from "./fixtures";

test.describe("PWA assets", () => {
  test("manifest.json is served and valid", async ({ request }) => {
    const res = await request.get("/manifest.json");
    expect(res.status()).toBe(200);

    const manifest = await res.json();
    expect(manifest.name).toContain("Ev2Ev");
    expect(manifest.short_name).toBe("Ev2Ev");
    expect(Array.isArray(manifest.icons)).toBe(true);
    expect(manifest.icons.length).toBeGreaterThan(0);
    for (const icon of manifest.icons) {
      expect(icon.src).toMatch(/^\/icons\//);
      expect(icon.sizes).toMatch(/^\d+x\d+$/);
    }
  });

  test("service worker script is served as JavaScript", async ({ request }) => {
    const res = await request.get("/sw.js");
    expect(res.status()).toBe(200);
    expect(res.headers()["content-type"]).toMatch(/javascript/);
    expect((await res.text()).length).toBeGreaterThan(0);
  });

  test("192x192 icon is served as an image", async ({ request }) => {
    const res = await request.get("/icons/icon-192x192.png");
    expect(res.status()).toBe(200);
    expect(res.headers()["content-type"]).toMatch(/image\/png/);
    expect((await res.body()).length).toBeGreaterThan(0);
  });

  test("offline fallback route renders", async ({ page }) => {
    await page.goto("/offline");
    await expect(
      page.getByRole("heading", { name: /offline/i })
    ).toBeVisible();
    // Escape links back into the app.
    await expect(page.getByRole("link", { name: /home/i })).toBeVisible();
  });
});
