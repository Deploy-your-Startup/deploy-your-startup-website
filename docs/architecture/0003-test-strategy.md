# Integration and E2E tests with GIVEN / WHEN / THEN

**Status**: Accepted

## Context

A successful static build does not prove that visitors see the intended content,
follow the right links or can use a form. Tests should describe those outcomes.

## Decision

**Integration tests are the default; changed user flows require E2E tests.**
Unit tests are reserved for complex algorithms and supplement these tests.
Every behaviour
change includes an integration test; changed user flows also include browser E2E.
A bug fix starts with a scenario that reproduces the bug.

Integration tests build the real Astro site and inspect the generated pages.
Browser E2E serves that build and drives the real page. Do not use isolated tests for routine helpers or mock our own components. For an external form or API provider, use
a local stand-in over the real protocol; replace only an external boundary
that cannot run locally and document why.

Write explicit **GIVEN / WHEN / THEN**:

- **GIVEN:** arrange the page content and any provider state needed by the scenario.
- **WHEN:** perform one business action, such as following a link or submitting a form.
- **THEN:** assert what the visitor sees or the provider receives.

Keep scenarios independent and fixture values visible. Success and failure
are separate scenarios; related scenarios may share one focused spec file.
Find browser controls by role and visible label, using data-testid only when
there is no suitable semantic locator. Never send test sign-ups to a live provider.

### Limited algorithm exception

Use focused unit tests only for complex algorithms with meaningful edge cases
or invariants, such as pathfinding, ranking or non-trivial parsing. Explain in
the test or change description what makes the algorithm complex and which
cases need isolated coverage. Exercise the real algorithm without mocking our
own code. Routine helpers, views, models and service workflows stay covered
through integration tests.

Algorithm unit tests supplement integration and E2E tests; they never replace
the required application or user-flow scenarios. Do not add unit tests merely
to increase a coverage percentage. Use GIVEN / WHEN / THEN for them too.

## Coverage and completion evidence

A green pipeline proves that its enabled checks passed, not that every feature
has complete E2E coverage. Smoke tests cover only their named scenarios. Record
uncovered user flows and report provider scenarios skipped because credentials
or external environments are unavailable. Keep required E2E checks enabled while
improving CI speed through isolation, caching and independent parallel jobs.
See [Testing policy and completion evidence](../testing-policy.md).

## Consequences

- Tests check the built artifact and the actual visitor flow.
- Browser tests catch behaviour a build check cannot establish.
- External integrations need a disposable local test setup.

## Alternatives considered

- **Build only:** catches compilation errors, not broken interactions.
- **Unit tests as the default:** omit the deployed page and integration.
- **Mocked components:** hide the behaviour of the real page.
- **Live provider accounts:** introduce network dependence and real side effects.
