import { test, expect } from "@playwright/test";

for (const width of [1440, 390]) {
  test(`GIVEN a ${width}px visitor WHEN exploring the Factory THEN they can navigate its parts and read the access FAQ`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto("/");
    await page.getByRole("link", { name: "Take a look inside the Factory" }).click();
    await expect(page).toHaveTitle("Inside the Factory — Deploy Your Startup");
    const map = page.getByRole("navigation", { name: "Factory components" });
    await map.getByRole("link", { name: /skills/ }).click();
    await expect(page).toHaveURL(/#skills$/);
    await expect(page.getByRole("heading", { name: "Agent skills", exact: true })).toBeVisible();
    for (const name of ["Your startups", "Shared tooling", "Project templates"]) {
      await expect(page.getByRole("heading", { name, exact: true })).toBeVisible();
    }
    expect(await page.evaluate(() => document.documentElement.scrollWidth)).toBeLessThanOrEqual(width);
    await page.getByRole("link", { name: "Ownership & access FAQ" }).click();
    await expect(page).toHaveTitle("FAQ — Deploy Your Startup");
    await page.getByRole("navigation", { name: "Main navigation" }).getByRole("link", { name: "The Factory", exact: true }).click();
    await expect(page).toHaveURL(/\/factory\/?$/);
  });
}
