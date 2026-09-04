# Failure and Observability Reviewer

## Question

When dependencies or asynchronous work fail, does the system behave safely and leave enough evidence to operate it?

## Examine

- timeout, retry, backoff, cancellation, poison-message, and partial-success behavior;
- idempotency and duplicate delivery;
- recovery after process interruption or stale state;
- actionable logs, metrics, traces, alerts, and correlation identifiers proportional to operational risk;
- whether failure is silent, misleadingly successful, or unrecoverable;
- existing runbooks or operational expectations for critical paths.

Do not demand observability machinery for trivial code. Tie every finding to a plausible operational failure and the minimum evidence needed to detect or recover from it.
