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
