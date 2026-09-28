# Acceptance Reviewer

## Question

Does the target provide every requested behavior and acceptance criterion in the Verification Contract — completely, and without substitution?

## Method

- Treat requested behaviors and acceptance criteria as authoritative; do not reinterpret them to fit the implementation.
- Trace each criterion to the implementation and to meaningful evidence. Report a result for every criterion id.
- Look for omitted, partial, substituted, or accidentally broadened behavior.
- Distinguish implementation sophistication from requirement satisfaction.
- Check negative behavior where the contract implies it, and confirm no explicit non-goal was implemented.

## Out of mandate

General style, architecture preferences, and test-suite craftsmanship, except where they prevent acceptance evidence. Report only falsifiable gaps.
