import { test } from "node:test";
import assert from "node:assert/strict";
import { execFileSync } from "node:child_process";
import { readFileSync } from "node:fs";

test("GIVEN the landing page WHEN Astro builds THEN visitors see the harness and two startups on a shared harness", () => {
  // GIVEN the real site, WHEN its production build renders the pages.
  execFileSync("npm", ["run", "build"], { cwd: new URL("../", import.meta.url), stdio: "pipe" });
  const html = readFileSync(new URL("../dist/index.html", import.meta.url), "utf8");
  const section = html.match(/<section class="how-it-works"[\s\S]*?<\/section>/)?.[0];

  // THEN the rendered section shows both apps on the shared foundation with working destinations.
  assert.ok(section);
  for (const text of ["Build your idea. Find out what works.", "features, real users and feedback", "About Phil", "Gaming Buch Club", "We take care of the harness.", "Agent-ready projects", "Automated checks", "Deployment & operations", "community contribution", "Ballern", "Go all in. Build. Ship. Validate."]) {
    assert.ok(section.includes(text), `Missing visible content: ${text}`);
  }
  assert.match(section, /href="https:\/\/aboutphil\.de"/);
  assert.match(section, /href="https:\/\/gamingbuchclub\.de"/);
  assert.doesNotMatch(section, /runtime-flow|HTTPS|<script|Einfach ballern|Dann validieren/);
  assert.match(html, /class="factory"/);
  assert.match(html, /title="k3s - lightweight Kubernetes"/);
  assert.match(html, /<span class="step"[^>]*>k3s<\/span>/);
  assert.doesNotMatch(html, /cloud os|the operating system of your cloud/);
  assert.match(html, /id="onboarding-code"/);
  assert.ok(readFileSync(new URL("../dist/get-started/index.html", import.meta.url), "utf8").includes("--onboard"));
});

test("GIVEN the get-started page WHEN Astro builds THEN visitors find the landing-page path next to onboarding", () => {
  // GIVEN the real site, WHEN its production build renders the pages.
  execFileSync("npm", ["run", "build"], { cwd: new URL("../", import.meta.url), stdio: "pipe" });
  const html = readFileSync(new URL("../dist/get-started/index.html", import.meta.url), "utf8");
  const option = html.match(/<details class="pitch-option[\s\S]*?<\/details>/)?.[0];

  // THEN the full application stays the default and the landing page is an explicit, copyable option.
  assert.ok(html.indexOf('id="onboarding-code"') < html.indexOf('id="pitch-code"'));
  assert.ok(option);
  for (const text of ["Only need a landing page first?", "Cloudflare Pages", "install.sh | bash", "gh auth setup-git", "startup bootstrap --kind pitch --template-version v0.1.0"]) {
    assert.ok(option.includes(text), `Missing visible content: ${text}`);
  }
  assert.doesNotMatch(option, /--onboard|startup doctor|Hetzner Cloud/);
});
