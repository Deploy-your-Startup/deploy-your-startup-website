# Automatic CLI installer updates

The Deploy workflow checks the latest stable release of
`Deploy-your-Startup/cli` every ten minutes. GitHub may delay scheduled runs;
this is not an immediate release webhook.

The CLI version is pinned in one place: `startup_cli_version` at the top of
`frontend/public/install.sh`. Each CLI release pins its tested application
template itself, so neither the installer nor the site names a template version.

For a newer `vX.Y.Z` release, it updates only `startup_cli_version`, runs the
website's tests and opens a pull request from `release/cli-vX.Y.Z`
(`scripts/cli_release_pr.sh`). `main` is protected, so the pin never lands
without review. Pull requests opened with the workflow token start no
`pull_request` runs; the workflow therefore dispatches Deploy on the release
branch, which runs the required checks there and never deploys. While that pull
request is open, scheduled runs skip the release; a newer release closes older
pin proposals. Merging the pull request deploys the pin. Dispatch Deploy on
`main` manually to check for a release sooner.

Opening the pull request requires the repository setting **Allow GitHub Actions
to create and approve pull requests** (Settings → Actions → General).

Drafts, prereleases, invalid version tags and versions at or below the current
pin are skipped. Existing CLI
installations update only when users rerun the installer.

This uses the website repository's `GITHUB_TOKEN` with `contents: write`,
`pull-requests: write` and `actions: write`; no cross-repository personal token
is needed. The public CLI
release metadata is read through the GitHub API. Existing Cloudflare credentials
remain the deployment credentials.

If an update or deploy fails, inspect the Deploy run before changing the pin.
For a withdrawal, mark the CLI release as a prerelease and deploy the previous
known-working installer pin manually. The automation never downgrades versions.


## Factory onboarding

`--onboard` delegates workspace creation, agent skill setup and first startup
setup to `startup factory onboard`, avoiding a second skill-install prompt. The CLI owns the pinned public Factory source and
version. Plain installation and CLI updates create no Factory. Existing Factory
files survive onboarding retries; Sprowi requires a separate optional setup.
Before the setup check, onboarding requests missing GitHub workflow and package
scopes with `gh auth refresh` in the same terminal and names the signed-in account.
Deploy this installer change only with a published CLI release containing the
Factory command; the installer fails clearly if that capability is absent.
