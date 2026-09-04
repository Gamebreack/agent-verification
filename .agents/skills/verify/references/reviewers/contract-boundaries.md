# Contract Boundary Reviewer

## Question

Are producers and consumers still compatible across the changed boundary?

## Examine

- request, response, event, schema, file, CLI, and protocol shapes;
- required versus optional fields, defaults, nullability, enums, and versioning;
- error semantics, status codes, retry expectations, and ordering;
- serialization and backward/forward compatibility;
- consumer-driven or provider contract evidence;
- integration behavior at the real boundary rather than only mocked collaborators.

Identify the affected producer and consumer for every finding. Avoid demanding broad end-to-end tests when a focused contract or integration test proves compatibility.
