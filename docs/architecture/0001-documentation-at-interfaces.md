# Documentation at interfaces

**Status**: Accepted

## Context

Repeating a rule across schemas, routes, services and components adds noise
and lets the copies drift apart. Code should explain its mechanics;
documentation should capture the context code alone cannot express.

## Decision

Document a rule once, at its relevant interface: an API schema, a public type,
a use-case entry point, the README, or an ADR.

Comments explain:

- why a non-obvious decision was made;
- business rules and invariants;
- external constraints and intentional exceptions.

Keep comments short and prefer **why** over **what**. Do not comment what clear
code already says. Explain mechanics only when an interface or implementation
remains genuinely hard to read, and simplify the code first when practical.
Remove comments that have become redundant.

Tests are executable specifications. They may be more verbose and repeat
business context when that makes a scenario understandable on its own.

Record a decision that shapes how the project is built as a new ADR in
`docs/architecture/`, numbered sequentially, with Context, Decision,
Consequences and Alternatives considered. Link it from `AGENTS.md` with a note
on when an agent should load it.

## Consequences

- Each rule has one authoritative location.
- Implementations carry fewer, more useful comments.
- Tests remain intentionally descriptive.

## Alternatives considered

- **Document every use:** convenient locally, but duplicates information.
- **Avoid comments entirely:** loses rationale and external constraints.
- **Only the README:** separates documentation from the interface it describes.
