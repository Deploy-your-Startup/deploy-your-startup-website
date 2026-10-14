# User-flow coverage inventory

## Observed baseline

This baseline describes the suites checked during the pipeline rollout on
2026-10-13. Update it as scenarios are added, changed or enabled.

The two browser checks verify homepage content and mobile layout against the real Astro production build. Existing integration checks cover installer and rendered-page contracts.

The scenario definitions live in [browser tests](../e2e_tests/tests/).
A successful run establishes only the scenarios that actually executed.

## Coverage to maintain

Add named browser scenarios for changed onboarding/navigation interactions. Build/installer assertions and homepage smoke checks do not establish that every visitor flow works.

For each changed critical flow record the integration case, browser case and
status (covered, partial or unverified). Cover success, validation and denied
access where applicable. Report skips and missing prerequisites explicitly.
Follow the [testing policy](testing-policy.md) when reporting completion.

## Optional onboarding flow

- Installer terminal integration (`tests/test_installer_agent_skill.py`): real
  Bash installer and controlling terminal with local download/GitHub boundaries;
  installation, existing login, environment token, native login, cancelled login,
  invalid token, missing GitHub CLI, rejected checksum, CLI-version guard,
  optional skills, **Later**, **Create now**, and failed project setup.
- Rendered-page integration (`frontend/tests/landing.test.mjs`): real Astro build
  communicates optional project creation and the name/template/folder/hosting/
  GitHub confirmation/review order.
- Browser E2E (`e2e_tests/tests/site.spec.ts`): get-started instructions and the
  expandable Cloudflare landing-page command on the real production build.
- Uninstaller integration (`tests/test_installer_agent_skill.py`): removes only
  the managed GitHub CLI link; separately installed GitHub CLI is preserved.

Not established by these tests: actual OAuth approval, macOS execution of the
GitHub CLI download, Keychain access, paid provider provisioning or a live first
deployment. Run those separately on a disposable Mac/account before release.
