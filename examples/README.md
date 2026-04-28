# Recall examples

Tiny end-to-end programs you can copy-paste. Each one assumes a Recall server running locally:

```bash
docker run -d --name recall -p 8787:8787 -e API_KEY=changeme \
  -v recall-data:/data ghcr.io/recallworks/recall:latest
```

| Example | Stack | What it shows |
|---|---|---|
| [`python/agent_memory.py`](python/agent_memory.py) | Python 3.11+ | Remember session facts, recall by query, checkpoint at the end |
| [`typescript/agent_memory.ts`](typescript/agent_memory.ts) | Node 18+ / Bun / Deno | Same flow, async client |
| [`bash/curl_round_trip.sh`](bash/curl_round_trip.sh) | curl | Raw HTTP — no SDK needed |

## Run a Python example

```bash
pip install requests
python examples/python/agent_memory.py
```

## Run a TypeScript example

Zero-config (uses local `package.json`):

```bash
cd examples/typescript
npm install
npm start
```

Or one-liner without installing:

```bash
npm install @recallworks/recall-client
npx tsx examples/typescript/agent_memory.ts
```

## Run the curl example

```bash
bash examples/bash/curl_round_trip.sh
```
