# BridgeEnvelope contract

## Purpose
Normalize bridge transport outputs before they become `WorkerResult` or `WorkflowResult`.

## Current fields from `schemas.py`

```python
return_value: BridgeReturnValue
content: str
metadata: BridgeMetadata
```

## Design intent

A bridge may be MCP-backed or CLI-backed, but it should expose a common envelope containing:
- high-signal semantic value (`return_value`)
- human-readable content/body (`content`)
- transport/debug metadata (`metadata`)

This keeps backend quirks out of orchestration-facing schemas.
