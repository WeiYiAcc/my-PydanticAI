# Hermes -> my-PydanticAI MCP adapter plan

## Goal
Use Hermes as the frontdoor/runtime host, while calling `my-PydanticAI` through a clean MCP surface instead of ad hoc CLI parsing.

## New MCP server
`my-PydanticAI` now exposes a local MCP stdio server via:

```bash
uv run my-pydanticai-mcp
```

or from the monorepo root:

```bash
mono pyd mcp
```

## Current MCP tools

- `doctor()`
- `run_task(prompt)`
- `run_prompt(prompt)`
- `route_request(prompt)`
- `run_worker(backend, prompt)`
- `workflow_action(action, task='')`

## Intended Hermes usage

Hermes should consume this as an MCP server, then either:
- call `run_task(prompt)` for orchestrated routing
- call `run_worker('pi', prompt)` for direct Pi delegation through PydanticAI
- call `workflow_action('dry-run')` or related actions when Stokowski workflow control is needed

## Why this is better than raw CLI wrapping

- stable tool names
- explicit arguments
- structured JSON text results
- avoids shell-quoting complexity in higher-level adapters
- matches the existing Pi/Codex bridge direction already used inside `my-PydanticAI`

## Immediate next step

Configure Hermes `mcp_servers` with a local stdio entry for `my-pydanticai-mcp`, then validate Hermes can invoke `run_worker('pi', ...)` through MCP.
