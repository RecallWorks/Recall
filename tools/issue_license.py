#!/usr/bin/env python3
# @wbx-modified copilot-b1c4 | 2026-04-28 04:48 MTN | v1.0 | NEW: license issuance CLI for operators | prev: NEW
"""Mint a Recall Pro/Enterprise license key.

Usage:
    # Set the signing key once (KEEP THIS SECRET — losing it means re-issuing
    # all customer keys; leaking it means anyone can mint free keys).
    $env:RECALL_LICENSE_SIGNING_KEY = "<your secret>"

    python tools/issue_license.py --tier pro --email buyer@acme.com --years 1
    python tools/issue_license.py --tier enterprise --email ops@bigco.com --days 90

Output is the license key printed to stdout. Email it to the customer with:

    Set RECALL_LICENSE_KEY=<key> in your container env.
    Server's RECALL_LICENSE_SIGNING_KEY must match the one used to issue.

Generate a fresh signing key:
    python -c "import secrets;print(secrets.token_urlsafe(48))"
"""

from __future__ import annotations

import argparse
import os
import sys
import time

# Allow running from repo root without install.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from recall.license import LicenseError, issue, verify  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser(description="Mint a Recall license key.")
    p.add_argument("--tier", choices=("pro", "enterprise"), required=True)
    p.add_argument("--email", required=True, help="Customer email (for support lookup hash).")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--days", type=int, help="License validity in days.")
    g.add_argument("--years", type=int, help="License validity in years.")
    p.add_argument(
        "--signing-key",
        default=os.environ.get("RECALL_LICENSE_SIGNING_KEY", ""),
        help="Signing key (default: $RECALL_LICENSE_SIGNING_KEY).",
    )
    args = p.parse_args()

    if not args.signing_key:
        print(
            "ERROR: signing key required. Set $RECALL_LICENSE_SIGNING_KEY or pass --signing-key.",
            file=sys.stderr,
        )
        print(
            "Generate one with: python -c \"import secrets;print(secrets.token_urlsafe(48))\"",
            file=sys.stderr,
        )
        return 2

    days = args.days if args.days else args.years * 365
    expiry_unix = int(time.time()) + days * 86400

    try:
        key = issue(args.signing_key, args.tier, expiry_unix, args.email)
        # Self-verify so the operator immediately sees if anything's wrong.
        lic = verify(key, args.signing_key)
    except LicenseError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1

    print()
    print(f"  Tier:     {lic.tier}")
    print(f"  Email:    {args.email}")
    print(f"  Expires:  {time.strftime('%Y-%m-%d', time.gmtime(lic.expiry_unix))} UTC")
    print(f"  Hash:     {lic.email_hash8}  (for support lookup)")
    print()
    print("  License key:")
    print(f"    {key}")
    print()
    print("  Customer instructions:")
    print(f'    docker run -d -p 8787:8787 \\')
    print(f'      -e API_KEY=<theirs> \\')
    print(f'      -e RECALL_LICENSE_KEY={key} \\')
    print(f'      -e RECALL_LICENSE_SIGNING_KEY=<your secret> \\')
    print(f"      -v recall-data:/data \\")
    print(f"      ghcr.io/recallworks/recall:latest")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
