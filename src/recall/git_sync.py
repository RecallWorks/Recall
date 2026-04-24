# @wbx-modified copilot-c4a1·MTN | 2026-04-23 | optional git sync of external knowledge repo | prev: NEW
"""Optional clone/pull of an external knowledge repo at startup.

Single-tenant deployments often want the brain to index a separate docs
repo on every boot. This module is a thin wrapper around `git clone --depth 1`
and `git pull --ff-only`. If GIT_REPO_URL is unset, all calls are no-ops.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
from pathlib import Path

log = logging.getLogger("recall.git")


def _inject_token(url: str, token: str) -> str:
    if not token:
        return url
    if "@" in url:
        return url.replace("@", f":{token}@", 1)
    return url.replace("https://", f"https://{token}@", 1)


def git_sync(repo_url: str, repo_dir: str, token: str = "") -> None:
    """Clone or fast-forward pull into repo_dir. No-op if repo_url is empty."""
    if not repo_url:
        log.warning("git_sync: no repo URL configured, skipping")
        return

    clone_url = _inject_token(repo_url, token)
    repo_path = Path(repo_dir)

    if (repo_path / ".git").exists():
        log.info("Pulling latest from %s", repo_url)
        proc = subprocess.run(
            ["git", "pull", "--ff-only"],
            cwd=str(repo_path),
            capture_output=True,
            text=True,
            timeout=300,
        )
        if proc.returncode == 0:
            log.info("Git pull: %s", proc.stdout.strip())
            return
        log.error("Git pull failed (rc=%d): %s — re-cloning", proc.returncode, proc.stderr.strip())
        shutil.rmtree(str(repo_path), ignore_errors=True)

    repo_path.parent.mkdir(parents=True, exist_ok=True)
    if repo_path.exists():
        shutil.rmtree(str(repo_path), ignore_errors=True)
    log.info("Cloning %s into %s", repo_url, repo_dir)
    proc = subprocess.run(
        ["git", "clone", "--depth", "1", clone_url, str(repo_path)],
        capture_output=True,
        text=True,
        timeout=300,
    )
    if proc.returncode != 0:
        log.error("Git clone failed (rc=%d): %s", proc.returncode, proc.stderr.strip())
    else:
        log.info("Git clone OK")


def resolve_index_paths(repo_dir: str, index_dirs: list[str], artifacts_dir: str) -> list[str]:
    """Return absolute paths to index. repo_dir/<each index_dir> + artifacts_dir."""
    paths: list[str] = []
    for d in index_dirs:
        full = os.path.join(repo_dir, d)
        if os.path.isdir(full):
            paths.append(full)
    if os.path.isdir(artifacts_dir):
        paths.append(artifacts_dir)
    return paths
