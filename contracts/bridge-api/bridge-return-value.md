# BridgeReturnValue contract

## Purpose
Define the semantic payload returned by a bridge before orchestration normalization.

## Current fields from `schemas.py`

```python
ok: bool = True
answer: str = ''
provider: str | None = None
model: str | None = None
api: str | None = None
usage: dict[str, Any] | None = None
response_id: str | None = None
session_id: str | None = None
thread_id: str | None = None
stop_reason: str | None = None
event_count: int | None = None
```

## Notes

- this is the most bridge-native semantic payload
- not every backend will populate every field
- orchestration should rely on semantic meaning, not on backend-specific optional field presence
