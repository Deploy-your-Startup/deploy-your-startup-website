import { test, expect } from "@playwright/test";

for (const width of [1440, 390]) {
  test(`GIVEN a ${width}px visitor WHEN following the deployment diagram THEN FAQ answers open with the keyboard`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/");
    const diagram = page.getByRole("region", { name: "Your startup. In your hands." });
    await expect(diagram.getByText("Your computer", { exact: true })).toBeVisible();
    await expect(diagram.getByText("GitHub Actions", { exact: true })).toBeVisible();
    await diagram.getByRole("link", { name: "Explore the FAQ" }).click();
    await expect(page).toHaveTitle("FAQ — Deploy Your Startup");
    const question = page.getByText("Where are passwords and API keys stored?", { exact: true });
    await question.focus();
    await page.keyboard.press("Enter");
    await expect(page.getByText(/The deployment runner can decrypt these secrets/)).toBeVisible();
    await page.keyboard.press("Enter");
    await expect(page.getByText(/The deployment runner can decrypt these secrets/)).toBeHidden();
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    await page.getByRole("link", { name: "Get started", exact: true }).first().click();
    await expect(page).toHaveURL(/\/get-started\/?$/);
  });
}

test("GIVEN reduced motion WHEN viewing the deployment flow THEN the explanation stays visible without animation", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("/");
  const diagram = page.getByRole("region", { name: "Your startup. In your hands." });
  await diagram.scrollIntoViewIfNeeded();
  await expect(diagram.getByText("Your server", { exact: true })).toBeVisible();
  expect(await diagram.evaluate(element => element.getAnimations({ subtree: true }).filter(animation => animation.playState === "running").length)).toBe(0);
});

test("GIVEN JavaScript is disabled WHEN opening the FAQ THEN native questions and navigation still work", async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false });
  const page = await context.newPage();
  await page.goto("http://127.0.0.1:4321/faq");
  await page.getByText("Can Deploy Your Startup access my accounts?", { exact: true }).click();
  await expect(page.getByText(/The standard setup does not add Deploy Your Startup/)).toBeVisible();
  await page.getByRole("link", { name: "Deploy Your Startup home" }).click();
  await expect(page.getByRole("heading", { name: "Your startup. In your hands." })).toBeVisible();
  await context.close();
});
