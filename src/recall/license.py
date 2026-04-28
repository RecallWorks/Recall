# @wbx-modified copilot-b1c4 | 2026-04-28 04:35 MTN | v1.0 | NEW: license-key validation for Pro/Enterprise gates | prev: NEW
"""License key validation — offline HMAC, no phone-home.

Format: ``tier.expiry_unix.email_hash8.sig`` (base64url, no padding)

  - tier:        ``pro`` | ``enterprise``
  - expiry_unix: integer seconds since epoch (license expiry)
  - email_hash8: first 8 hex chars of sha256(email) — for support lookup
  - sig:         base64url(hmac_sha256(SIGNING_KEY, "tier.expiry.email8"))[:32]

Server reads ``RECALL_LICENSE_SIGNING_KEY`` env var. If unset, server runs in
**OSS mode** — Pro tools (``recall_filtered``, ``backfill_epoch``) are
unavailable and chunk count > 50_000 is refused at write time.

Operators issue keys via ``tools/issue_license.py`` using the same signing key.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import logging
import os
import time
from dataclasses import dataclass
from typing import Literal

log = logging.getLogger("recall.license")

Tier = Literal["oss", "pro", "enterprise"]
PRO_TIERS: frozenset[str] = frozenset({"pro", "enterprise"})
ENTERPRISE_TIERS: frozenset[str] = frozenset({"enterprise"})

# Soft chunk ceiling for OSS — above this you need a paid license.
# Reason: small projects fit free; brain-scale workloads pay.
OSS_CHUNK_LIMIT = 50_000


@dataclass(frozen=True)
class License:
    tier: Tier
    expiry_unix: int
    email_hash8: str

    @property
    def expired(self) -> bool:
        return time.time() > self.expiry_unix

    @property
    def is_pro(self) -> bool:
        return self.tier in PRO_TIERS and not self.expired

    @property
    def is_enterprise(self) -> bool:
        return self.tier in ENTERPRISE_TIERS and not self.expired


# Sentinel for OSS / no-license mode.
OSS_LICENSE = License(tier="oss", expiry_unix=2**31 - 1, email_hash8="00000000")


class LicenseError(ValueError):
    """Raised when a license key is malformed, signature-invalid, or expired."""


def _b64url_decode(s: str) -> bytes:
    pad = "=" * ((4 - len(s) % 4) % 4)
    return base64.urlsafe_b64decode(s + pad)


def _b64url_encode(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode("ascii").rstrip("=")


def sign_payload(signing_key: str, payload: str) -> str:
    """Sign ``payload`` (the ``tier.expiry.email8`` portion) and return short sig."""
    if not signing_key:
        raise LicenseError("signing key is empty")
    mac = hmac.new(signing_key.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).digest()
    return _b64url_encode(mac)[:32]


def issue(signing_key: str, tier: Tier, expiry_unix: int, email: str) -> str:
    """Mint a license key. Operator-side; not called by server."""
    if tier not in ("pro", "enterprise"):
        raise LicenseError(f"tier must be pro|enterprise, got {tier!r}")
    if expiry_unix <= int(time.time()):
        raise LicenseError("expiry must be in the future")
    email_hash8 = hashlib.sha256(email.lower().encode("utf-8")).hexdigest()[:8]
    payload = f"{tier}.{expiry_unix}.{email_hash8}"
    sig = sign_payload(signing_key, payload)
    return f"{payload}.{sig}"


def verify(key: str, signing_key: str) -> License:
    """Parse + cryptographically verify a license key. Raises LicenseError."""
    if not key:
        raise LicenseError("empty license key")
    if not signing_key:
        raise LicenseError("server has no signing key configured")
    parts = key.strip().split(".")
    if len(parts) != 4:
        raise LicenseError(f"malformed key: expected 4 parts, got {len(parts)}")
    tier, expiry_str, email_hash8, sig = parts
    if tier not in ("pro", "enterprise"):
        raise LicenseError(f"unknown tier: {tier}")
    try:
        expiry_unix = int(expiry_str)
    except ValueError:
        raise LicenseError("expiry is not an integer") from None
    expected_sig = sign_payload(signing_key, f"{tier}.{expiry_unix}.{email_hash8}")
    if not hmac.compare_digest(expected_sig, sig):
        raise LicenseError("signature mismatch — key was not signed by this server's signing key")
    lic = License(tier=tier, expiry_unix=expiry_unix, email_hash8=email_hash8)
    if lic.expired:
        raise LicenseError(f"license expired on unix {expiry_unix}")
    return lic


def load_from_env() -> License:
    """Read ``RECALL_LICENSE_KEY`` + ``RECALL_LICENSE_SIGNING_KEY``.

    Returns OSS_LICENSE if either is unset (silent — that's the OSS posture).
    Returns OSS_LICENSE and logs WARN if a key is present but invalid (so a
    typo'd key doesn't take the server down).
    """
    key = os.environ.get("RECALL_LICENSE_KEY", "").strip()
    signing_key = os.environ.get("RECALL_LICENSE_SIGNING_KEY", "").strip()
    if not key or not signing_key:
        log.info("Running in OSS mode (no license key set)")
        return OSS_LICENSE
    try:
        lic = verify(key, signing_key)
    except LicenseError as e:
        log.warning("License key rejected: %s — falling back to OSS mode", e)
        return OSS_LICENSE
    log.info(
        "License: tier=%s expiry=%s email_hash=%s",
        lic.tier,
        time.strftime("%Y-%m-%d", time.gmtime(lic.expiry_unix)),
        lic.email_hash8,
    )
    return lic


# Tool-name → required tier. Used by transport layer to gate access.
PRO_TOOLS: frozenset[str] = frozenset({"recall_filtered", "backfill_epoch"})


def require_for_tool(lic: License, tool_name: str) -> None:
    """Raise LicenseError if ``lic`` cannot use ``tool_name``."""
    if tool_name in PRO_TOOLS and not lic.is_pro:
        raise LicenseError(
            f"tool '{tool_name}' requires a Pro license — see https://recall.works/pricing"
        )


def require_chunk_capacity(lic: License, current_chunks: int) -> None:
    """Raise LicenseError if writing more chunks would exceed OSS limit."""
    if not lic.is_pro and current_chunks >= OSS_CHUNK_LIMIT:
        raise LicenseError(
            f"OSS mode is capped at {OSS_CHUNK_LIMIT:,} chunks; "
            f"have {current_chunks:,}. Upgrade at https://recall.works/pricing"
        )
