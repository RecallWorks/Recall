<!-- @wbx-modified copilot-b1c4 | 2026-04-28 04:05 MTN | v1.5 | bumped to 0.3.4 (chromadb<2.0, cp312 wheel) | prev: copilot-b1c4@2026-04-28 03:20 MTN -->

# Recall + Claude Desktop (Windows) — 60-second test

## 1. Make sure Recall is running

```powershell
docker run -d --name recall -p 8787:8787 `
  -e API_KEY=test-key-123 `
  ghcr.io/recallworks/recall:0.3.3
```

Verify:

```powershell
curl -s http://localhost:8787/health
# {"ok":true,"chunks":0,"version":"0.3.3"}
```

## 2. Install the `recall-mcp` stdio bridge in your Python env

```powershell
pip install ai-recallworks>=0.3.4
```

## 3. Add this to your Claude Desktop config

File: `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "recall": {
      "command": "recall-mcp",
      "env": {
        "RECALL_BASE_URL": "http://localhost:8787",
        "RECALL_API_KEY": "test-key-123"
      }
    }
  }
}
```

## 4. Restart Claude Desktop

Open Claude → look in the bottom-right of the chat box for the 🔌 (plug) icon → confirm `recall` is listed with green status.

## 5. Test it

In a Claude conversation, type:

> Remember that my favorite color is blue. Use the `remember` tool.

Claude should call `remember`, you'll see a tool-call confirmation in the UI, and the response will confirm it was stored.

Then in a new conversation:

> What's my favorite color? Use the `recall` tool to check.

Claude should call `recall`, get back the memory, and answer "blue."

## What to capture for verification

If it works:
- Screenshot of Claude's tool-call UI showing `recall.remember` succeeding
- Screenshot of the recall response in a new chat

If it fails:
- Screenshot of any error
- Output of: `docker logs recall --tail 50`
- Output of: `recall-mcp --version` (should print `0.3.3`)
