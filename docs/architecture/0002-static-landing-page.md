# Static landing page

**Status**: Accepted

## Context

A pitch page tests an idea before there is a product: it explains the offer,
collects interest and must be online within minutes, at little or no cost.
It has no users to log in, no data of its own and no server-side logic.

## Decision

- **Astro** builds the page to static HTML and CSS. It ships no JavaScript to
  the browser unless a component needs it.
- **Cloudflare Pages** serves the build. Every push to `main` builds and
  deploys it through GitHub Actions; credentials live in repository secrets.
- **No backend.** Anything dynamic (a sign-up form, analytics) uses a hosted
  service or becomes a separate module with its own `make.sh` next to
  `frontend/`.

## Consequences

- Hosting is free or close to it, fast worldwide and needs no servers or
  operations work.
- Every push to `main` is a production deployment, so changes go through pull
  requests.
- Moving from pitch to product means starting an application template; the
  page can stay as the public marketing site.

## Alternatives considered

- **Starting with the full application template:** more power than a pitch
  needs, with servers and costs before the idea is validated.
- **A site builder:** quick, but the page would live outside the owner's
  repository and the coding-agent workflow.
