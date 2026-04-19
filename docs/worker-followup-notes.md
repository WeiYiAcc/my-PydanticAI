# Worker follow-up notes

Current MCP-backed workers:
- Codex: fully usable as a generic MCP task worker via `codex mcp-server`
- Pi: usable as a generic MCP task worker via the custom `pi-mcp-serve.js` bridge
- Hermes: usable as a generic MCP task worker via the custom `hermes-task-mcp-serve.js` bridge

Implications:
1. Codex can serve as the reference generic MCP worker shape.
2. Pi should be optimized toward the same shape by shrinking `run_prompt` payloads and exposing additional focused tools if needed.
3. Hermes now follows the same bridge pattern as Pi, so the next work is convergence and cleanup rather than inventing a new path.

Recommended next steps:
- Hermes: keep the new `hermes-task-mcp-serve.js` bridge and add `continue_task` if session continuation becomes important.
- Pi: reduce `run_prompt` structured payload size by extracting concise summary fields and optionally keeping raw stdout under an opt-in debug field.
- Claude Code: add a dedicated task bridge analogous to Pi/Hermes if we want generic MCP worker semantics on top of `claude mcp serve`.
- Keep Codex and Claude Code MCP configs/imports intact; use Codex as the current generic reference implementation.
