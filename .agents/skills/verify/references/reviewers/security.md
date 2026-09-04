# Security Reviewer

## Question

Does the changed attack surface introduce a concrete security, privacy, or authorization failure?

## Examine

- authentication, authorization, tenancy, sessions, and privilege transitions;
- input validation and output encoding at trust boundaries;
- secrets, sensitive data, logging, storage, and transport;
- injection, request forgery, unsafe deserialization, path/file handling, and command execution where applicable;
- dependency or configuration changes that alter exposure;
- fail-open behavior and negative authorization cases.

Use the project's threat model and applicable OWASP ASVS areas when available. Report an exploit or failure path grounded in the target. Do not dump a generic vulnerability checklist or require unrelated hardening.
