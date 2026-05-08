"""
recall.py — Recall · Networked Brain (stub for v0.1, full impl in v0.2)

This file is intentionally a thin stub. The architecture is documented in
brain/README.md. A working reference implementation will land here in v0.2.

Until then, this stub:
  - boots a FastAPI app
  - serves GET /health -> 200 {ok: true, version: "0.1-stub"}
  - returns 501 NotImplemented on every other endpoint

You can build the docker image today (`docker compose up --build`) to verify
the dependency layer pins compile cleanly on your platform. The data volume
will sit empty until the v0.2 service code is wired in.
"""

import os
from fastapi import FastAPI, HTTPException

VERSION = "0.1-stub"
DATA_DIR = os.environ.get("RECALL_DATA", "/data")
PORT = int(os.environ.get("RECALL_PORT", "8080"))

app = FastAPI(title="Recall Brain", version=VERSION)


@app.get("/health")
def health():
    return {"ok": True, "version": VERSION, "data_dir": DATA_DIR}


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
def not_implemented(path: str):
    raise HTTPException(
        status_code=501,
        detail=(
            f"recall.py is a v0.1 stub. /{path} is part of the v0.2 spec and "
            "is not yet implemented. See brain/README.md for the design and "
            "the architecture note. Pull requests welcome."
        ),
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
