# Bridge payload examples

## Generic MCP worker bridge target shape

Desired normalized output should be representable as:

```json
{
  "return_value": {
    "ok": true,
    "answer": "short normalized answer",
    "provider": "...",
    "model": "...",
    "usage": {},
    "response_id": "...",
    "session_id": "..."
  },
  "content": "human-readable content",
  "metadata": {
    "stdout": "...",
    "stderr": "...",
    "raw_payload": {}
  }
}
```

## Why this matters

This allows different backends (Pi, Hermes, Codex, future Claude/OpenAgent/OpenClaw) to converge on a common orchestration contract.
