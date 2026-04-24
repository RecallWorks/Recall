<!-- @wbx-modified copilot-a3f7·MTN | 2026-04-23 | Wk2: responsible-disclosure policy | prev: NEW -->
# Security Policy

## Reporting a vulnerability

Please do **not** open a public GitHub issue for security vulnerabilities.

Email **security@recall.works** with:

- A description of the issue and its impact.
- Steps to reproduce, or a proof-of-concept.
- The version(s) affected.
- Your contact info if you want credit.

We will acknowledge within 72 hours and aim to ship a fix within 30 days for
high-severity issues. Coordinated disclosure preferred; we will credit you in
the release notes unless you ask otherwise.

## Supported versions

Only the latest minor release on `main` receives security patches during the
pre-1.0 phase. After 1.0, the latest two minor releases will be supported.

## Scope

In scope:

- Authentication and authorization bypass in `server/`.
- Data leakage between tenants in `enterprise/multi-tenant/`.
- Remote code execution via tool inputs.
- Dependency vulnerabilities with a viable exploit path through Recall.

Out of scope:

- Denial-of-service from a tenant exceeding their own quota.
- Issues in third-party MCP clients.
- Self-hosting misconfigurations (e.g. exposing the server without auth).
