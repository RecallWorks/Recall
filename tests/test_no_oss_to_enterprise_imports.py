# @wbx-modified copilot-a3f7·MTN | 2026-04-24 | enforce OSS-never-imports-enterprise rule | prev: NEW
"""Guard: nothing under src/recall/ may import from enterprise/.

This protects the OSS-core/enterprise license boundary. The OSS core is MIT;
the enterprise tree is BSL. If MIT code took a runtime dependency on BSL code
the boundary would be effectively unilateral.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OSS_SRC = ROOT / "src" / "recall"

IMPORT_RE = re.compile(r"^\s*(?:from|import)\s+enterprise(?:\.|\s|$)", re.MULTILINE)


def test_oss_does_not_import_enterprise() -> None:
    offenders: list[str] = []
    for py in OSS_SRC.rglob("*.py"):
        text = py.read_text(encoding="utf-8")
        if IMPORT_RE.search(text):
            offenders.append(str(py.relative_to(ROOT)))
    assert not offenders, (
        "OSS core (MIT) imports from enterprise/ (BSL). Reverse the dependency:\n  "
        + "\n  ".join(offenders)
    )
