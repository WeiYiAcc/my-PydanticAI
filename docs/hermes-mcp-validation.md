# Hermes -> MCP -> my-PydanticAI -> Pi validation

## Status
Validated.

## What was configured

Hermes now has an MCP server entry named `my-pydanticai` in `~/.hermes/config.yaml`:
- transport: stdio
- command: `bash -lc 'cd /home/weiyiacc/my-agent-monorepo/apps/my-PydanticAI && uv run my-pydanticai-mcp'`
- env: `ORCH_PI_MODE=real`

## MCP tools discovered

Hermes successfully connects to the `my-pydanticai` MCP server and discovers:
- `doctor`
- `run_task`
- `run_prompt`
- `route_request`
- `run_worker`
- `workflow_action`

## Practical validation

A direct Hermes chat invocation was able to call the MCP tool path and get Pi output through `my-PydanticAI`:

Prompt used:

```text
Use the mcp_my_pydanticai_run_worker tool with backend 'pi' and prompt 'reply exactly ok-from-hermes-via-pydanticai'. Return only the final answer.
```

Observed final output:

```text
ok-from-hermes-via-pydanticai
```

## Interpretation

This proves the chain works:

```text
Hermes
  -> MCP tool call
  -> my-PydanticAI MCP server
  -> my-PydanticAI Pi adapter
  -> Pi MCP bridge
  -> normalized result back through Hermes
```

## Current limitations

- Hermes still requires either explicit prompting or a future higher-level adapter/skill to use this path ergonomically.
- `my-PydanticAI` remains the orchestration/bridge kernel, but it is not yet exposed to Hermes through a dedicated polished host adapter.
- Pi routing is currently forced to real mode for the MCP server entry.

## Recommended next step

Create a small Hermes-facing skill or adapter convention that tells Hermes when to use:
- `mcp_my_pydanticai_run_worker`
- `mcp_my_pydanticai_run_task`

instead of requiring manual tool-name prompting.
