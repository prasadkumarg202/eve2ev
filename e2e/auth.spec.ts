import { test, expect } from "./fixtures";

test.describe("auth pages", () => {
  test("/login renders email, password, and submit", async ({ page }) => {
    await page.goto("/login");

    await expect(page.locator("#login-email")).toBeVisible();
    await expect(page.locator("#login-password")).toBeVisible();
    await expect(page.locator("#login-submit")).toBeVisible();
    await expect(page.locator("#google-login")).toBeVisible();
  });

  test("/register renders the sign-up form", async ({ page }) => {
    await page.goto("/register");

    await expect(page.locator("#register-name")).toBeVisible();
    await expect(page.locator("#register-email")).toBeVisible();
    await expect(page.locator("#register-password")).toBeVisible();
    await expect(page.locator("#register-submit")).toBeVisible();
  });

  test("/forgot-password renders the reset form", async ({ page }) => {
    await page.goto("/forgot-password");

    await expect(page.locator("#forgot-email")).toBeVisible();
    await expect(page.locator("#forgot-submit")).toBeVisible();
  });

  test("login with dummy credentials shows an error banner and stays on /login", async ({
    page,
  }) => {
    await page.goto("/login");
    await expect(page.locator("#login-submit")).toBeVisible();

    // Tolerant of backend state: either Supabase rejects the credentials or
    // auth is unconfigured — both paths surface the #login-error alert banner.
    // A submit that lands before hydration falls through to a native form GET
    // (page reload, fields cleared), so retry the whole fill+submit sequence.
    const errorBanner = page.locator("#login-error");
    await expect(async () => {
      await page.locator("#login-email").fill("e2e-dummy@example.com");
      await page
        .locator("#login-password")
        .fill("definitely-wrong-password-123");
      await page.locator("#login-submit").click();
      await expect(errorBanner).toBeVisible({ timeout: 8_000 });
    }).toPass({ timeout: 60_000 });
    await expect(errorBanner).not.toBeEmpty();

    // No navigation happened and the page did not crash.
    expect(new URL(page.url()).pathname).toBe("/login");
    await expect(page.locator("#login-submit")).toBeVisible();
  });
});
