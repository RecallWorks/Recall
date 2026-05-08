# Recall Brain — reference Dockerfile (blueprint)
# v0.2 target. Today this builds the dependency layer; the actual
# recall.py service is a stub that returns 501 on every endpoint
# until the v0.2 source drop.

FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    RECALL_DATA=/data \
    RECALL_PORT=8080

RUN apt-get update && apt-get install -y --no-install-recommends \
    git curl ca-certificates build-essential \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Pinning these is intentional — embedding model + chromadb wire format
# must move together or the persistent store breaks across upgrades.
RUN pip install --no-cache-dir \
      chromadb==0.5.5 \
      fastapi==0.115.0 \
      "uvicorn[standard]==0.30.6" \
      sentence-transformers==3.0.1 \
      pydantic==2.9.2 \
      sse-starlette==2.1.3

COPY recall.py /app/recall.py

VOLUME ["/data"]
EXPOSE 8080

# When v0.2 drops, this becomes:
#   CMD ["uvicorn", "recall:app", "--host", "0.0.0.0", "--port", "8080"]
# Until then, the stub serves /health only and 501s the rest.
CMD ["python", "/app/recall.py"]
