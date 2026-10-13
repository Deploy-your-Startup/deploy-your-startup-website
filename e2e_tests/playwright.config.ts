import { defineConfig } from "@playwright/test";
export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  workers: 1,
  forbidOnly: Boolean(process.env.CI),
  use: { baseURL: "http://127.0.0.1:4321", trace: "retain-on-failure" },
  webServer: {
    command: "cd ../frontend && npm run preview -- --host 0.0.0.0",
    url: "http://127.0.0.1:4321",
    reuseExistingServer: false,
  },
});
