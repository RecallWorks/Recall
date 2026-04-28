# @wbx-modified copilot-b1c4 | 2026-04-28 03:38 MTN | v0.2 | rewrote using requests after recall-client SDK pkg deleted from PyPI | prev: copilot-a3f7@2026-04-24
"""End-to-end agent memory: remember, recall, checkpoint.

Run a server first:
    docker run -d -p 8787:8787 -e API_KEY=changeme \
        -v recall-data:/data ghcr.io/recallworks/recall:latest

Then:
    pip install requests
    python agent_memory.py
"""
from __future__ import annotations

import os

import requests

URL = os.environ.get("RECALL_URL", "http://localhost:8787")
KEY = os.environ.get("RECALL_KEY", "changeme")
H = {"X-API-Key": KEY, "Content-Type": "application/json"}


def call(tool: str, **payload) -> dict:
    # First request triggers embedder model load (~10-30s); use generous timeout.
    r = requests.post(f"{URL}/tool/{tool}", headers=H, json=payload, timeout=120)
    r.raise_for_status()
    return r.json()


def main() -> None:
    # 0. Health
    print("server:", requests.get(f"{URL}/health", headers=H, timeout=10).json())

    # 1. Store a few facts the agent should remember across sessions.
    call("remember", content="user prefers dark mode", source="prefs", tags="ui,dark-mode")
    call("remember", content="project deadline is 2026-05-15", source="project", tags="deadline")
    call("remember", content="lead engineer is Jamie (jamie@example.com)", source="people", tags="contact")

    # 2. Pull them back semantically.
    hits = call("recall", query="when is the deadline", n=3)
    print("\nrecall: when is the deadline")
    print(hits["result"])

    # 3. End-of-session checkpoint so the next agent can pick up.
    cp = call(
        "checkpoint",
        intent="onboard new agent to the project",
        established="user prefers dark mode; deadline 2026-05-15; lead is Jamie",
        pursuing="prepare kickoff doc draft",
        open_questions="which team channel does Jamie use?",
        session="e0a1",
    )
    print("\ncheckpoint:", cp["result"].splitlines()[0])


if __name__ == "__main__":
    main()
