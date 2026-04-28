# @wbx-modified copilot-b1c4 | 2026-04-28 04:45 MTN | v1.0 | NEW: license module unit tests | prev: NEW
"""Unit tests for recall.license — issuance, verification, gating."""

from __future__ import annotations

import time

import pytest

from recall.license import (
    OSS_CHUNK_LIMIT,
    OSS_LICENSE,
    License,
    LicenseError,
    issue,
    require_chunk_capacity,
    require_for_tool,
    verify,
)

SK = "test-signing-key-do-not-use-in-prod"
EMAIL = "buyer@example.com"


def _future(days: int = 30) -> int:
    return int(time.time()) + days * 86400


# ---------- issue + verify roundtrip ---------------------------------------


def test_issue_and_verify_roundtrip_pro():
    key = issue(SK, "pro", _future(), EMAIL)
    lic = verify(key, SK)
    assert lic.tier == "pro"
    assert lic.is_pro
    assert not lic.is_enterprise
    assert not lic.expired


def test_issue_and_verify_roundtrip_enterprise():
    key = issue(SK, "enterprise", _future(), EMAIL)
    lic = verify(key, SK)
    assert lic.is_pro  # enterprise implies pro
    assert lic.is_enterprise


def test_issue_rejects_oss_tier():
    with pytest.raises(LicenseError, match="tier must be"):
        issue(SK, "oss", _future(), EMAIL)  # type: ignore[arg-type]


def test_issue_rejects_past_expiry():
    with pytest.raises(LicenseError, match="future"):
        issue(SK, "pro", int(time.time()) - 1, EMAIL)


# ---------- verify failure modes -------------------------------------------


def test_verify_empty_key_raises():
    with pytest.raises(LicenseError, match="empty"):
        verify("", SK)


def test_verify_empty_signing_key_raises():
    with pytest.raises(LicenseError, match="signing key"):
        verify("pro.99999.deadbeef.xxx", "")


def test_verify_malformed_part_count():
    with pytest.raises(LicenseError, match="4 parts"):
        verify("pro.99999.deadbeef", SK)


def test_verify_bad_tier():
    # Build a syntactically-valid key but with wrong tier.
    with pytest.raises(LicenseError, match="unknown tier"):
        verify("trial.99999.deadbeef.x" * 1, SK)


def test_verify_signature_mismatch_with_wrong_key():
    key = issue(SK, "pro", _future(), EMAIL)
    with pytest.raises(LicenseError, match="signature mismatch"):
        verify(key, "different-signing-key")


def test_verify_signature_mismatch_after_tamper():
    key = issue(SK, "pro", _future(), EMAIL)
    tampered = key.replace("pro.", "enterprise.", 1)
    with pytest.raises(LicenseError, match="signature mismatch"):
        verify(tampered, SK)


def test_verify_expired_key_raises():
    # Issue with an expiry already in the past — bypass issue() guard
    # by building the payload manually.
    from recall.license import sign_payload

    past = int(time.time()) - 86400
    payload = f"pro.{past}.deadbeef"
    key = f"{payload}.{sign_payload(SK, payload)}"
    with pytest.raises(LicenseError, match="expired"):
        verify(key, SK)


# ---------- gates ----------------------------------------------------------


def test_oss_blocks_pro_tools():
    with pytest.raises(LicenseError, match="Pro license"):
        require_for_tool(OSS_LICENSE, "recall_filtered")
    with pytest.raises(LicenseError, match="Pro license"):
        require_for_tool(OSS_LICENSE, "backfill_epoch")


def test_oss_allows_free_tools():
    # Should NOT raise for any non-Pro tool.
    for tool in ("remember", "recall", "checkpoint", "reflect", "memory_stats"):
        require_for_tool(OSS_LICENSE, tool)


def test_pro_unlocks_pro_tools():
    pro = License(tier="pro", expiry_unix=_future(), email_hash8="aaaaaaaa")
    require_for_tool(pro, "recall_filtered")
    require_for_tool(pro, "backfill_epoch")


def test_oss_chunk_cap_blocks_at_limit():
    with pytest.raises(LicenseError, match="capped"):
        require_chunk_capacity(OSS_LICENSE, OSS_CHUNK_LIMIT)
    with pytest.raises(LicenseError, match="capped"):
        require_chunk_capacity(OSS_LICENSE, OSS_CHUNK_LIMIT + 1000)


def test_oss_chunk_cap_allows_below_limit():
    require_chunk_capacity(OSS_LICENSE, 0)
    require_chunk_capacity(OSS_LICENSE, OSS_CHUNK_LIMIT - 1)


def test_pro_has_no_chunk_cap():
    pro = License(tier="pro", expiry_unix=_future(), email_hash8="aaaaaaaa")
    require_chunk_capacity(pro, OSS_CHUNK_LIMIT * 100)


# ---------- env loader -----------------------------------------------------


def test_load_from_env_oss_when_unset(monkeypatch):
    monkeypatch.delenv("RECALL_LICENSE_KEY", raising=False)
    monkeypatch.delenv("RECALL_LICENSE_SIGNING_KEY", raising=False)
    from recall.license import load_from_env

    assert load_from_env() is OSS_LICENSE


def test_load_from_env_oss_when_invalid(monkeypatch):
    monkeypatch.setenv("RECALL_LICENSE_KEY", "garbage.key.no.signature.xxx")
    monkeypatch.setenv("RECALL_LICENSE_SIGNING_KEY", SK)
    from recall.license import load_from_env

    assert load_from_env() is OSS_LICENSE  # graceful fallback


def test_load_from_env_valid_pro(monkeypatch):
    key = issue(SK, "pro", _future(), EMAIL)
    monkeypatch.setenv("RECALL_LICENSE_KEY", key)
    monkeypatch.setenv("RECALL_LICENSE_SIGNING_KEY", SK)
    from recall.license import load_from_env

    lic = load_from_env()
    assert lic.is_pro
