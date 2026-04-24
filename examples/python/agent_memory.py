# @wbx-modified copilot-a3f7·MTN | 2026-04-24 | minimal Recall agent-memory example
"""End-to-end agent memory: remember, recall, checkpoint.

Run a server first:
    docker run -d -p 8787:8787 -e API_KEY=changeme \
        -v recall-data:/data ghcr.io/recallworks/recall:latest

Then:
    pip install recall-client
    python agent_memory.py
"""
from __future__ import annotations

import os

from recall_client import RecallClient

URL = os.environ.get("RECALL_URL", "http://localhost:8787")
KEY = os.environ.get("RECALL_KEY", "changeme")


def main() -> None:
    with RecallClient(URL, api_key=KEY) as c:
        # 0. Health
        print("server:", c.health())

        # 1. Store a few facts the agent should remember across sessions.
        c.remember("user prefers dark mode", source="prefs", tags="ui,dark-mode")
        c.remember("project deadline is 2026-05-15", source="project", tags="deadline")
        c.remember("lead engineer is Jamie (jamie@example.com)", source="people", tags="contact")

        # 2. Pull them back semantically.
        hits = c.recall("when is the deadline", n=3)
        print("\nrecall: when is the deadline")
        print(hits.result)

        # 3. End-of-session checkpoint so the next agent can pick up.
        cp = c.checkpoint(
            intent="onboard new agent to the project",
            established="user prefers dark mode; deadline 2026-05-15; lead is Jamie",
            pursuing="prepare kickoff doc draft",
            open_questions="which team channel does Jamie use?",
            session="e0a1",
        )
        print("\ncheckpoint:", cp.result.splitlines()[0])


if __name__ == "__main__":
    main()
