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

`--onboard` delegates workspace creation, agent skill setup and first startup
setup to `startup factory onboard`, avoiding a second skill-install prompt. The CLI owns the pinned public Factory source and
version. Plain installation and CLI updates create no Factory. Existing Factory
files survive onboarding retries; Sprowi requires a separate optional setup.
Before the setup check, onboarding requests missing GitHub workflow and package
scopes with `gh auth refresh` in the same terminal and names the signed-in account.
Deploy this installer change only with a published CLI release containing the
Factory command; the installer fails clearly if that capability is absent.

## Runtime reuse

The installer checks an existing `uv` for the required tool-install options.
It reuses compatible installations without updating them. Otherwise it reuses
its previous private uv or downloads the pinned fallback into its own directory.
The launcher uses the selected uv directory for subsequent CLI operations.

The CLI remains isolated under `~/.local/share/startup/tools`. Repeating the
installer no longer forces reinstallation of the same pinned Git release.
New installations use uv's managed Python storage; older installations keep
using their private Python directory. Users do not need to install Python
manually. Uninstalling removes the managed CLI and private fallback, while
shared uv and Python installations remain available to other tools.

Installation output shows the current step. Dependency output is suppressed on
success and printed on failure; failures never print the ready message.

Run the installer process tests with `python3 -m unittest discover -s tests -v`.
On macOS, also run `python3 scripts/check_installer_e2e.py /path/to/cli-checkout`
with uv available. This exercises real uv and the real CLI from the checkout's
HEAD in a temporary home, replacing only the GitHub source URL with local Git.
It verifies installation, repeat-install stability, CLI help, shell setup and
uninstallation. Python and dependency downloads may require network access.
