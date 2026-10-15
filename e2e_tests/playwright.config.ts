import { defineConfig } from "@playwright/test";
import { fileURLToPath } from "node:url";
export default defineConfig({
  testDir: "./tests",
  fullyParallel: true,
  workers: 1,
  forbidOnly: Boolean(process.env.CI),
  use: { baseURL: "http://127.0.0.1:4321", trace: "retain-on-failure" },
  webServer: {
    command: "node node_modules/astro/bin/astro.mjs preview --host 0.0.0.0 --port 4321 --ignore-lock",
    cwd: fileURLToPath(new URL("../frontend", import.meta.url)),
    url: "http://127.0.0.1:4321",
    reuseExistingServer: false,
  },
});
