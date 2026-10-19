# GIVEN / WHEN / THEN tests are the specification

**Status**: Accepted

## Context

Spec-driven development writes the expected behaviour into separate documents
before the code. Those documents are not executed, so nothing notices when they
drift from what the application does, and agents then follow a stale source.
Our integration and E2E scenarios already describe behaviour as
GIVEN / WHEN / THEN and run in CI (ADR 0003).

## Decision

**The GIVEN / WHEN / THEN integration and E2E scenarios are the specification
of behaviour.** Do not maintain separate spec, requirements or PRD documents
that restate what the application does.

- **Intent comes first.** Write the scenario before the implementation and see
  it fail; a bug fix starts with a scenario that reproduces it. A task may draft
  its scenarios in prose, but the draft becomes tests and is not kept.
- **Name the behaviour.** Test names and GIVEN / WHEN / THEN read as the rule
  they enforce, so a reader learns the behaviour without reading the code.
- **Decisions live in ADRs.** Why we chose a behaviour, the alternatives and
  the constraints belong in an ADR (ADR 0001), not in a test or a spec.
- **What a scenario cannot express stays a note.** Visual design, copy and
  legal text are documented where they live; they are not a behaviour spec.

## Consequences

- Every specified behaviour is checked on every change; a changed rule changes
  a test.
- There is one source for what the application does and one for why.
- Behaviour without a scenario is unspecified; record such gaps as described
  in the [testing policy](../testing-policy.md).

## Alternatives considered

- **Spec documents with spec-driven tooling:** a second, unexecuted source of
  truth that drifts from the code and the tests.
- **Specs plus tests:** the same rules written twice, kept in sync by hand.
- **Gherkin feature files with step definitions:** executable, but adds a layer
  between the scenario and the real test code.
