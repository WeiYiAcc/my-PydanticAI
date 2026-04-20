# BridgeMetadata contract

## Purpose
Capture low-level transport/debugging data from worker bridges.

## Current fields from `schemas.py`

```python
stdout: str | None = None
stderr: str | None = None
raw_payload: dict[str, Any] | None = None
```

## Rule

Metadata is for diagnostics and observability. Business logic should not depend on unstable backend-specific metadata details unless that dependency is promoted into a documented contract.
