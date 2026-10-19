import { test, expect } from "@playwright/test";

test("GIVEN a built site WHEN a visitor opens the homepage THEN its content is visible", async ({ page }) => {
  // GIVEN the real production build served locally.
  // WHEN a visitor opens its homepage.
  const response = await page.goto("/");
  // THEN content and the document title are present.
  expect(response?.status()).toBe(200);
  await expect(page).toHaveTitle(/\S/);
  await expect(page.locator("main")).toBeVisible();
  await expect(page.locator("main")).not.toHaveText("");
});

test("GIVEN a mobile visitor WHEN the homepage opens THEN its content fits the viewport", async ({ page }) => {
  // GIVEN a narrow viewport.
  await page.setViewportSize({ width: 390, height: 844 });
  // WHEN the visitor opens the production build.
  await page.goto("/");
  // THEN the main content is visible without horizontal overflow.
  await expect(page.locator("main")).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(391);
});


test("GIVEN a new user WHEN opening get-started THEN the command includes their Factory workspace", async ({ page }) => {
  // GIVEN the production build, WHEN a visitor opens onboarding.
  await page.goto("/get-started");
  // THEN the visible instructions explain the workspace and offer the installer handoff.
  await expect(page.getByText(/your own Factory workspace and your first project/).first()).toBeVisible();
  await expect(page.locator("#onboarding-code")).toContainText("bash -s -- --onboard");
  await expect(page.getByRole("button", { name: "Copy paste into your terminal command", exact: false })).toBeVisible();
});

test("GIVEN the harness section WHEN a visitor scrolls to it THEN the rocket ships to an app", async ({ page }) => {
  // GIVEN the production build.
  await page.goto("/");
  // WHEN the visitor scrolls to the shared harness.
  await page.locator(".harness-foundation").scrollIntoViewIfNeeded();
  // THEN an app lights up with a delivery status from the harness.
  await expect(page.locator(".example-app.is-shipped .deploy-status")).toHaveText(/✓ deployed/, { timeout: 5000 });
});
