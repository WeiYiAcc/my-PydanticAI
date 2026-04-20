# ReviewResult contract

## Purpose
Captures approval or rejection after comparing worker results.

## Current fields from `schemas.py`

```python
approved: bool
summary: str
reasons: list[str]
```

## Semantics

- `approved` — whether the review gate accepts the current worker set
- `summary` — concise gate decision statement
- `reasons` — machine-readable-ish reason strings suitable for logs and UIs

## Rule

Review logic may evolve, but this result shape should remain simple and backend-agnostic.
