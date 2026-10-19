# Startup landing page instructions

An Astro landing page in `frontend/`, built to static files and deployed to
Cloudflare Pages by `.github/workflows/deploy.yml` on every push to `main`.

```bash
./make.sh run      # local dev server on http://localhost:4321
./make.sh build    # static output in frontend/dist/
./make.sh preview  # serve the production build locally
```

`make.sh` is the contract for every module: add new commands there and keep
`mise.toml` tasks delegating to it. A new module (for example `backend/`) lives
next to `frontend/` with its own `make.sh`.

Cloudflare credentials stay in repository secrets set by `startup bootstrap`.
Never print, commit or hard-code them, and do not deploy manually unless the
user asks for it.

## Testing

The shared container E2E workflow gates Cloudflare deployment. Browser tooling
lives in `e2e_tests/Dockerfile`; each shard tests the real Astro production build.
The small default suite uses one shard; increase the caller’s `shards` as it grows.
PRs run checks without deploying. Reports are collected before Compose cleanup.

Follow [Testing policy and completion evidence](docs/testing-policy.md) and
[ADR 0003](docs/architecture/0003-test-strategy.md): integration tests run
against the real Astro build, changed visitor flows get browser E2E. Find
controls by role and visible label, and never submit test data to live providers.
Read the [coverage inventory](docs/test-coverage.md) before changing a visitor
flow and update it with new scenarios and gaps.

## Working conventions

- Keep it simple: Astro is the only framework; avoid premature abstractions and
  unnecessary dependencies (ADR 0002).
- Ship as little client-side JavaScript as possible; prefer native HTML
  elements and keep pages accessible (semantic headings, labels, alt text).
- Use descriptive names; booleans start with `is`, `has`, `can` or `should`;
  declare return types on named TypeScript functions.
- Comment the why, once, at the interface (ADR 0001).
- Never push directly to `main`; every push deploys. Open a pull request with
  an English title and description; branch and commit format:
  [commit conventions](.github/git-commit-instructions.md).
- Before finishing, run `./make.sh build`, the affected integration tests and
  browser E2E for changed visitor flows.

## Architecture decisions

Load an ADR when its topic comes up. Numbers 0001-0099 belong to the template
and arrive through template updates; number project ADRs from 0100 upward.

- [ADR 0001](docs/architecture/0001-documentation-at-interfaces.md) — load when adding comments, documentation or an ADR.
- [ADR 0002](docs/architecture/0002-static-landing-page.md) — load for hosting, framework or backend choices.
- [ADR 0003](docs/architecture/0003-test-strategy.md) — load when writing integration or browser E2E scenarios; includes GIVEN / WHEN / THEN.

## Template updates (Copier)

From the repo root with a clean working tree:

```bash
startup template update --version <release-tag> --dry-run
startup template update --version <release-tag>
```

Review the diff, resolve conflicts, run `./make.sh build`, then commit
including `.copier-answers.yml`. Do not edit Copier answers manually.

## Project notes

- Updating the pinned CLI in the installer: [CLI installer updates](docs/cli-installer-updates.md).
- Keeping Actions minutes down without dropping checks: [CI costs](docs/ci-costs.md).
