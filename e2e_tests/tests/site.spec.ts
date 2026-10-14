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


test("GIVEN a new visitor WHEN opening get-started THEN setup can finish before project and provider choices", async ({ page }) => {
  // GIVEN the real built site.
  // WHEN the visitor follows the installation instructions.
  await page.goto("/get-started/");
  // THEN the visible flow explains GitHub setup and optional project creation.
  await expect(page.getByText("Create your first startup now or come back later.", { exact: false })).toBeVisible();
  await expect(page.getByText("GitHub CLI is installed if needed.", { exact: false })).toBeVisible();
  await expect(page.getByText("your own server", { exact: false })).toBeVisible();
  await expect(page.getByText("Name your startup, choose a template", { exact: false })).toBeVisible();
  await expect(page.getByText("Confirm your GitHub account and review the plan", { exact: false })).toBeVisible();
  await expect(page.locator("#onboarding-code")).toContainText("--onboard");
  await page.getByText("Only need a landing page first?", { exact: true }).click();
  await expect(page.locator("#pitch-code")).toContainText("startup bootstrap --kind pitch");
});
