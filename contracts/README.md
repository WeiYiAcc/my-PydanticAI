# my-PydanticAI contracts

This directory documents the stable boundaries that `apps/my-PydanticAI` should expose.

Purpose:
- describe worker/result schemas before internal refactors
- stabilize how different control planes call the orchestrator
- keep bridges and backends replaceable

## Contract groups

- `worker-api/` — normalized worker/result/report schemas
- `bridge-api/` — MCP/CLI bridge expectations for backend workers
- `frontend-api/` — CLI and Telegram-facing entrypoint contracts

## Status

Documentation-first. These contracts describe the target layering while current code remains runnable.
