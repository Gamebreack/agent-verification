# Security Reviewer

## Question

Does the changed attack surface introduce a concrete security, privacy, or authorization failure?

## Method

- Check authentication, authorization, tenant isolation, sessions, and privilege transitions, including admin paths.
- Seek negative authorization evidence: a test or trace showing the wrong principal or tenant is denied, and that denial does not fail open.
- Check input validation and output encoding at trust boundaries: injection, request forgery, unsafe deserialization, path/file handling, command execution.
- Check secrets and sensitive data in code, logs, storage, and transport.
- Check dependency or configuration changes that alter exposure.
- Use the project's threat model and applicable OWASP ASVS areas when available.

## Out of mandate

Generic vulnerability checklists and unrelated hardening. Report an exploit or failure path grounded in the target.
