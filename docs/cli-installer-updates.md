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

## Installation output

The installer adds a branded welcome and real completion steps while preserving
the detailed runtime and dependency output, including package lists. Commands
stream directly to the terminal, with static step headings so animation cannot
overwrite their logs. Verification checks CLI startup without printing its help
page; failures remain visible and stop installation before a success checkmark.
GitHub authentication and onboarding prompts remain interactive.

With `--onboard`, CLI installation is followed by `Checking GitHub connection…`
and `✓ GitHub connected` only after authentication is verified. If login is
needed, the progress animation stops for GitHub's prompts and the connection is
checked again afterwards. Only the silent connection check animates. The final
ready message follows successful setup.

Color and the progress animation depend on stdout being a terminal, including when
the script arrives through `curl | bash`. Redirected output, `TERM=dumb`, a
nonempty `NO_COLOR`, or a nonempty `CI` use plain installer progress lines.
Animation never adds artificial delays to installation; external tools keep
control of their own output.

The palette, wording and directional motion follow the current website; see the
[design reference and terminal fallbacks](installer-design.md). Set
`STARTUP_NO_ANIMATION=1` to keep supported colors with static progress.

## Optional onboarding release dependency

The [new onboarding flow](onboarding-flow.md) needs a CLI release with the basic
`startup doctor` profile, `doctor --provider`, and the interactive stack picker.
The installer pins the published [CLI v0.1.13](https://github.com/Deploy-your-Startup/cli/releases/tag/v0.1.13),
which includes these capabilities. The released CLI's `doctor --help` and
`bootstrap --help` were checked for the required provider and stack options.
For future onboarding changes, release the compatible CLI before advancing the
installer pin. Do not point the public installer at a feature branch or invent
an unreleased version tag.

The installer also pins official GitHub CLI binaries and their SHA-256 digests
for Intel and Apple Silicon Macs. It reuses an existing `gh`; otherwise it
installs into the managed runtime and links `~/.local/bin/gh`. Uninstall removes
only that managed link and preserves independent GitHub CLI installations and
GitHub credentials.
