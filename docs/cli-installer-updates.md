# Automatic CLI installer updates

The Deploy workflow checks the latest stable release of
`Deploy-your-Startup/cli` every ten minutes. GitHub may delay scheduled runs;
this is not an immediate release webhook.

The CLI version is pinned in one place: `startup_cli_version` at the top of
`frontend/public/install.sh`. Each CLI release pins its tested application
template itself, so neither the installer nor the site names a template version.

For a newer `vX.Y.Z` release, it updates only `startup_cli_version`, runs the website's tests and commits the pin to
`main`. A fresh workflow dispatch then tests and deploys that commit through the
shared Cloudflare Pages workflow. Dispatch Deploy manually to check sooner.

Drafts, prereleases, invalid version tags and versions at or below the current
pin are skipped. Existing CLI
installations update only when users rerun the installer.

This uses the website repository's `GITHUB_TOKEN` with `contents: write` and
`actions: write`; no cross-repository personal token is needed. The public CLI
release metadata is read through the GitHub API. Existing Cloudflare credentials
remain the deployment credentials.

If an update or deploy fails, inspect the Deploy run before changing the pin.
For a withdrawal, mark the CLI release as a prerelease and deploy the previous
known-working installer pin manually. The automation never downgrades versions.


## Factory onboarding

`--onboard` delegates workspace creation and first startup setup to
`startup factory onboard`. The CLI owns the pinned public Factory source and
version. Plain installation and CLI updates create no Factory. Existing Factory
files survive onboarding retries; Sprowi requires a separate optional setup.
Deploy this installer change only with a published CLI release containing the
Factory command; the installer fails clearly if that capability is absent.
