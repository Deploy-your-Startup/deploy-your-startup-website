# Git conventions

## Branches

- Never commit directly to `main`; use a feature branch and a pull request.
- Name branches `<type>/<short-description>` in kebab-case, for example
  `feat/newsletter-signup` or `chore/update-dependencies`. With a ticket, put
  its key after the type: `feat/ABC-123-newsletter-signup`.
- Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`.

## Commit messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```text
<type>(<scope>): <description>
```

- The scope is optional; use the ticket key or the affected service
  (`frontend`, `ci`).
- Types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`, plus `perf`,
  `build`, `ci`, `revert`.
- Subject: imperative mood, no trailing period, about 50 characters.
- Add a body only when the *what* and *why* are not obvious from the subject;
  wrap it at 72 characters.

## Pull requests

- Write PR titles and descriptions in English, even when the conversation that
  produced the change was in another language.
- Describe what changed, why, and how it was verified.

### Visual evidence

For visible UI changes, capture before/after screenshots of the actual running
application when feasible. Use the same viewport, data and UI state so the
change is easy to compare; use desktop by default and include mobile when the
change affects it. Use demo data and redact sensitive information.

Never commit review screenshots to the code repository; merged history keeps
them forever. Upload them with `startup evidence upload --pr <pr-url> <image>...`,
which stores them in the operator's private evidence repository and prints
Markdown links, or drag and drop them into the pull request on GitHub. Embed the
printed links in the pull request description. Caption each with Before or After, the
screen, viewport dimensions and what changed. If a comparison is impractical,
state what is missing, why, and what you verified instead. Documentation-only
and nonvisual changes do not need screenshots. Screenshots complement the
required integration and E2E checks.
