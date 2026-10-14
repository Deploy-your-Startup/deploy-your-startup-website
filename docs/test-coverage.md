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
