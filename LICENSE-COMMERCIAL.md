<!-- @wbx-modified copilot-a3f7·MTN | 2026-04-23 | Wk2: BSL marker for /enterprise/ tree | prev: NEW -->
# Business Source License 1.1

**Licensor:** Recall contributors
**Licensed Work:** Files contained in the `enterprise/` directory of this repository.
**Additional Use Grant:** You may use the Licensed Work for any non-production
purpose, and for production use by a single organization with no more than five
(5) seats accessing the deployment.
**Change Date:** Three (3) years from the release date of each tagged version.
**Change License:** MIT License (see `LICENSE`).

---

## Why BSL on `enterprise/`

The OSS core (`server/`, `clients/`, `docker/single-tenant/`, `docs/`,
`examples/`) is **MIT** — fully free for any use, commercial or otherwise,
forever.

The `enterprise/` tree contains commercial-grade implementations (multi-tenant
isolation, SSO connectors, audit-grade exports, managed-cloud control plane).
These are licensed under BSL 1.1 so that a third party cannot stand up a
hosted competitor on day one. After three years, each version converts
automatically to MIT.

If you need production use beyond the Additional Use Grant, contact us for a
commercial license.

---

## Full BSL 1.1 text

The full Business Source License 1.1 text is available at
<https://mariadb.com/bsl11/>. The terms above set the parameters; the legal
text governs.
