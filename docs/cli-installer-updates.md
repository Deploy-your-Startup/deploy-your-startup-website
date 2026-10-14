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

## Optional onboarding release dependency

The [new onboarding flow](onboarding-flow.md) needs a CLI release with the basic
`startup doctor` profile, `doctor --provider`, and the interactive stack picker.
Merge/release the companion CLI change first, then advance `startup_cli_version`
to that published tag before merging the installer change. Keep the installer
PR in draft until this is done. Do not point the public installer at a feature
branch or invent an unreleased version tag.

The installer also pins official GitHub CLI binaries and their SHA-256 digests
for Intel and Apple Silicon Macs. It reuses an existing `gh`; otherwise it
installs into the managed runtime and links `~/.local/bin/gh`. Uninstall removes
only that managed link and preserves independent GitHub CLI installations and
GitHub credentials.
