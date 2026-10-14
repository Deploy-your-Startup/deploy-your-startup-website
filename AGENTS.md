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

**Integration tests are the default; changed user flows require E2E tests.**
Unit tests are reserved for complex algorithms and supplement these tests.
Every behaviour
change includes an integration test of the real Astro build; changed visitor
flows also get browser E2E (ADR 0003).

Use explicit **GIVEN / WHEN / THEN**: arrange the relevant state, perform one
business action and assert what the visitor observes. Keep scenarios independent.
Find controls by role and visible label. Do not mock our own code; use local
stand-ins for external services and never submit test data to live providers.

## Working conventions

- KEEP IT SIMPLE: a landing page needs no framework beyond Astro. Avoid
  over-engineering, premature abstractions and unnecessary dependencies.
- Never push directly to `main`; every push deploys. Use a feature branch and a
  pull request. Branch names and commit format:
  [`.github/git-commit-instructions.md`](.github/git-commit-instructions.md).
- **Pull request titles and descriptions are always in English**, even when the
  conversation was in another language.
- Before finishing, run `./make.sh build` and the affected integration tests;
  run browser E2E for changed visitor flows.

## Code style

- Prefer descriptive names over abbreviations.
- Boolean functions and variables start with `is`, `has`, `can` or `should`.
- Declare return types on named TypeScript functions.
- Prefer native HTML elements (`<dialog>`, `<details>`, `<form>`) over
  reimplementing their behaviour in JavaScript; ship as little client-side
  JavaScript as possible.
- Keep pages accessible: semantic headings, labelled controls, alt text.
- Comment the why, not the what; document a rule once at its interface
  (ADR 0001).

## Architecture decisions

Record decisions that shape the project as numbered ADRs in
`docs/architecture/` and list them here with when to load them.

- [ADR 0001](docs/architecture/0001-documentation-at-interfaces.md) — load when adding comments, documentation or an ADR.
- [ADR 0002](docs/architecture/0002-static-landing-page.md) — load for hosting, framework or backend choices.
- [ADR 0003](docs/architecture/0003-test-strategy.md) — load when writing integration or browser E2E scenarios; includes GIVEN / WHEN / THEN.

## Template updates (Copier)

From the repo root with a clean working tree:

```bash
startup template update --version main --dry-run
startup template update --version main
```

Review the diff, resolve conflicts, run `./make.sh build`, then commit
including `.copier-answers.yml`. Do not edit Copier answers manually.

## Test coverage and completion claims

Follow [Testing policy and completion evidence](docs/testing-policy.md).
Keep integration tests as the default and E2E coverage for changed user flows.
A green pipeline confirms the executed checks; smoke tests and skipped provider
checks do not establish full feature coverage. Record uncovered flows and report
remaining gaps when completing work. Never remove required E2E scenarios to
improve deployment speed.

## Current user-flow coverage

Read the [coverage inventory](docs/test-coverage.md) before changing a user flow.
Update its named scenarios and gaps as tests are added or provider checks become
available. Report what executed and what remains unverified.
