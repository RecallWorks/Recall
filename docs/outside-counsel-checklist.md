<!-- @wbx-modified copilot-a3f7·MTN | 2026-04-24 | outside-counsel-review checklist -->
# Outside-Counsel Review — Pre-Brief Checklist

> Internal-only. Not committed in any release zip. Used to brief outside
> counsel before they look at Recall's license stack and IceWhisperer's
> commercial posture.

## What we want counsel to confirm

1. **MIT/BSL boundary holds.** Confirm `src/recall/*` (MIT) takes no runtime
   dep on `enterprise/*` (BSL 1.1), and that the CI test
   [`tests/test_no_oss_to_enterprise_imports.py`](../tests/test_no_oss_to_enterprise_imports.py)
   is the right enforcement mechanism.
2. **BSL 1.1 Additional Use Grant** as drafted in
   [`LICENSE-COMMERCIAL.md`](../LICENSE-COMMERCIAL.md) is enforceable and
   matches the intent: free for non-prod and ≤5-seat single-org prod, paid
   above that, auto-converts to MIT 3 years after each tagged release.
3. **License-boundary one-pager** at [`docs/license-boundary.md`](./license-boundary.md)
   accurately summarises the legal stack for a commercial buyer.
4. **IceWhisperer EULA** at `IceWhisperer/bundle/EULA.md` is enforceable in
   the United States (Steve's first 5 ICPs are US lenders). Confirm the
   binding-arbitration clause survives state-law variance.
5. **ICE non-affiliation disclosure** on the IceWhisperer landing + pricing
   pages is sufficient to defeat any trademark-confusion claim by ICE
   Mortgage Technology.
6. **Corpus posture (v1.0.2)** described in
   `/memories/icewhisperer-corpus-legal.md` v1.2: SDK XML + Developer
   Connect + Resource Center articles authored by ICE, scraped under
   Steve's senior-ICE standing, redistributed inside customer perimeter
   only. Confirm this is defensible.

## Hard rule for counsel

> **Counsel may quote any text in this file or in `docs/license-boundary.md`
> directly back at us.** Do not assume any of this is privileged advice
> until they say so in writing.

## Pre-brief packet (assemble before the call)

- [ ] [`LICENSE`](../LICENSE) (MIT)
- [ ] [`LICENSE-COMMERCIAL.md`](../LICENSE-COMMERCIAL.md) (BSL 1.1 + grant)
- [ ] [`docs/license-boundary.md`](./license-boundary.md)
- [ ] [`tests/test_no_oss_to_enterprise_imports.py`](../tests/test_no_oss_to_enterprise_imports.py)
- [ ] `IceWhisperer/bundle/EULA.md`
- [ ] `IceWhisperer/_strategy/non-affiliation.md` (if it exists; otherwise
      the disclosure block from `pricing.html`)
- [ ] `/memories/icewhisperer-corpus-legal.md` v1.2 — printed/exported
- [ ] One-page founder summary (Steve to write 5 lines)

## Logistics

- Engage at least 2 weeks before first paid Team customer onboards
  (current pilot is 60-day pre-paid, no Team tier active).
- Counsel must specialise in **OSS licensing AND fintech vendor contracts**.
  Not just one of the two. Likely candidate firms: Heather Meeker
  (license + OSS), Outside GC (fintech vendor contracts).
- Budget envelope: typically $5-15k for a 4-hour review of this scope.

## What we are NOT asking counsel to do

- Re-draft any of these documents. We will iterate based on red-line.
- Review individual customer contracts. Each Team contract uses a stock
  MSA + Order Form template that needs its own review pass.
- Opine on patent posture. Recall + IceWhisperer file no patents.

## Open questions for counsel

1. Does the BSL Additional Use Grant need a per-deployment seat-counter
   audit clause to be enforceable? Or does honor-system + telemetry suffice?
2. Is "powered by Recall" co-branding sufficient to satisfy MIT attribution
   in the IceWhisperer bundle? The bundle re-distributes the Recall MIT
   image — the MIT attribution lives in `bundle/THIRD-PARTY-NOTICES.md`.
3. Is the Resource Center scrape (ICE-authored articles, partner login
   under Steve's name) safer characterised as "fair use" or "agency"
   under our reseller agreement? We've documented as agency in
   `/memories/icewhisperer-corpus-legal.md` v1.2 — confirm.

## Owner

Steve Paltridge. Schedule via Calendly; no agent action.
