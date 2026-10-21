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


## Factory onboarding

The installer process tests exercise the real shell installer in a pseudo-terminal
and verify delegation to `startup factory onboard` after GitHub, doctor and the
optional agent skill. The installed CLI/downloads remain boundary stand-ins in
that suite. The CLI Factory integration tests separately exercise real Copier,
Git, bootstrap, registry persistence, failure/resume and owner preservation.
Browser checks verify the built get-started page and copyable command. These
checks do not establish one continuous fresh-Mac-to-live-cloud deployment.


`python3 scripts/check_installer_factory_e2e.py` runs the real shell installer in
a macOS pseudo-terminal, downloads the published CLI and runtimes, checks doctor,
creates the public Factory, installs its skills and tooling, reviews the first
startup plan and cancels. Only GitHub authentication/identity is substituted;
there are no cloud or repository mutations. The `installer-factory` macOS CI job
runs this scenario for PRs and production deployments and gates deployment.
Actual GitHub OAuth, Keychain interaction, provider setup and a live application
remain unverified by this cancellation scenario.

## Installer pin updates

The scheduled release check advances the installer's CLI pin through a pull
request, because `main` requires owner review and PR checks. The integration
test runs the workflow's proposal step against real Git repositories: the pin
lands on `chore/cli-<tag>`, `main` is untouched, the checks are dispatched on
that branch, and an existing proposal is not repeated. `gh` is a recording
stand-in, so creating the PR and running the dispatched checks on GitHub are
verified only by the first real scheduled run.
