# WorkerResult outline

Current fields from `schemas.py`:

```python
worker: Literal["hermes", "pi", "stokowski", "codex"]
ok: bool
mode: Literal["mock", "real"]
summary: str
command: str | None
returncode: int | None
stdout: str | None
stderr: str | None
structured: dict | None
```

## Field intent

- `worker` — normalized backend identity
- `ok` — coarse success/failure flag
- `mode` — whether result came from mock or real execution
- `summary` — concise human-readable result synopsis
- `command` / `returncode` — transport/exec diagnostics
- `stdout` / `stderr` — raw adapter diagnostics
- `structured` — normalized machine-readable payload or adapter-specific structured result
