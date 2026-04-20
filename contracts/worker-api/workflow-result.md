# WorkflowResult contract

## Purpose
Represents normalized outcomes from workflow-oriented backends that are not simple one-shot workers.

## Current example backend
- `Stokowski`

## Current fields from `schemas.py`

```python
action: Literal["dry_run", "status", "submit"]
ok: bool
mode: Literal["mock", "real"]
summary: str
command: str | None
returncode: int | None
stdout: str | None
stderr: str | None
structured: dict | None
```

## Semantics

- `action` — which workflow control verb was executed
- `ok` — coarse success/failure
- `mode` — mock vs real execution
- `summary` — concise human-readable status or outcome
- `command` / `returncode` — execution diagnostics
- `stdout` / `stderr` — raw transport output
- `structured` — normalized machine-readable workflow payload when available
