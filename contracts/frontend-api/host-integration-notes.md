# Host integration notes

`my-PydanticAI` is expected to be invoked by multiple host/control planes over time.

Planned host categories:
- Pi local/TUI orchestration
- Hermes invoking orchestrator tasks
- future OpenClaw remote orchestration
- future OpenAgent integration

## Stability rule

Host-specific calling conventions should terminate in a stable frontend or adapter contract, not in direct imports into orchestration internals.
