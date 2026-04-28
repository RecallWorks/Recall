<!-- @wbx-modified copilot-a3f7·MTN | 2026-04-24 | MIT/BSL boundary one-pager -->
# Recall License Boundary

> One-pager for contributors and customers. The legal text is in
> [`LICENSE`](./LICENSE) (MIT) and [`LICENSE-COMMERCIAL.md`](./LICENSE-COMMERCIAL.md) (BSL 1.1).

## TL;DR

| Tree | License | What it covers | Production use |
|------|---------|----------------|----------------|
| `src/recall/` | MIT | Single-tenant memory engine, tools, transports, CLI, store interfaces, the OSS Docker image | Free, forever, any scale |
| `clients/` | MIT | Python + TypeScript SDKs (`recall-client`, `@recallworks/recall-client`) | Free, forever |
| `docker/single-tenant/` | MIT | The image at `ghcr.io/recallworks/recall:0.1.0` | Free, forever |
| `docs/`, `examples/`, `tests/` | MIT | Quickstarts, conventions, conformance tests | Free, forever |
| `enterprise/` | BSL 1.1 | Multi-tenant isolation, SSO connectors, hash-chain audit log, managed-cloud control plane | Free for non-prod and ≤5-seat single-org prod; commercial license for larger; converts to MIT 3 years after each tagged release |

## Why two licenses

The OSS core stays MIT so anyone can run it on their own boxes for any
purpose, commercially or otherwise, without a conversation with us. That's
the deal: own your memory, on your hardware, forever.

The `enterprise/` tree adds the things a hosted competitor would need to
spin up a paid clone overnight: per-tenant isolation, SSO, audit-grade
exports, control plane. We license that under BSL 1.1 — free for small
production and any non-production use, paid only when you're at scale, and
auto-converted to MIT three years after each release.

## Hard rule: dependency direction

> **`src/recall/*` MUST NOT import from `enterprise/*`.**
> The reverse is fine.

The CI test [`tests/test_no_oss_to_enterprise_imports.py`](./tests/test_no_oss_to_enterprise_imports.py)
walks every `.py` under `src/recall/` and fails the build if it finds a
`from enterprise.*` or `import enterprise.*` line.

If MIT code took a runtime dependency on BSL code, the boundary would be
unilateral: an OSS user could no longer run the OSS core without pulling in
BSL terms. Refuse the dep instead — design the OSS core's interface to be
satisfied by either side.

## How to build a feature

Ask: "would a hosted-Recall competitor copy this on day one?"

* **No** → MIT, lands in `src/recall/`. Examples: a new tool, a new
  embedder backend, a CLI flag, an SDK helper.
* **Yes** → BSL, lands in `enterprise/`. Examples: a new SSO connector,
  multi-tenant ABAC, a managed-cloud quota service, an audit exporter.

When you're not sure, default to MIT and move it later. It's easier to
relicense towards proprietary than away from it.

## Contributing under each license

Both trees accept external contributions. The CLA + DCO requirements in
[`CONTRIBUTING.md`](./CONTRIBUTING.md) apply uniformly. By contributing to
`enterprise/` you are accepting that your contribution lands under BSL 1.1
and converts to MIT on the same 3-year clock as the rest of the tree.

## Buying a commercial license

If your production deployment exceeds the BSL Additional Use Grant
(more than 5 seats per organization), reach out via the contact in
[`README.md`](./README.md). Commercial licenses are flat-rate per
deployment and include the SOC 2 evidence pack pulled from
`HashChainAuditLog`.
