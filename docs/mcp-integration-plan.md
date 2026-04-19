# Unified MCP integration plan

Validated MCP entrypoints:

- Hermes MCP task bridge:
  - command: `node /home/weiyiacc/.pi/agent/git/github.com/WeiYiAcc/pi-mcp-adapter/hermes-task-mcp-serve.js`
  - bridge implementation: wraps `hermes chat -q --quiet` and exposes generic MCP tools `doctor` and `run_task`
- Pi MCP bridge server:
  - command: `node /home/weiyiacc/.pi/agent/git/github.com/WeiYiAcc/pi-mcp-adapter/pi-mcp-serve.js`
  - validated with:
    - `npx mcporter list --stdio "node /home/weiyiacc/.pi/agent/git/github.com/WeiYiAcc/pi-mcp-adapter/pi-mcp-serve.js" --name pi-agent --schema`
    - `npx mcporter call run_prompt prompt="Reply exactly ok-from-mcp" --stdio "node /home/weiyiacc/.pi/agent/git/github.com/WeiYiAcc/pi-mcp-adapter/pi-mcp-serve.js" --name pi-agent --output json`

Current Pi MCP bridge behavior:
- exposes `doctor`
- exposes `run_prompt`
- internally runs `pi --mode json --no-session -p <prompt>` and extracts the final assistant text plus provider/model/usage metadata
- keeps full raw stdout/stderr in structured output for debugging

Recommended next project step for pydanticai-orchestrator:
1. Replace text CLI adapters with MCP-backed adapters.
2. Hermes adapter should connect to `hermes-task-mcp-serve.js` over stdio.
3. Pi adapter should connect to `pi-mcp-serve.js` over stdio.
4. Codex adapter should connect to `codex mcp-server` over stdio.
5. Normalize all of them into the existing `WorkerResult` schema.
6. Keep compact structured payloads by default; reserve raw protocol dumps for debugging.

Why this is better than stdout scraping:
- stable schemas from MCP tool metadata
- no banner/spinner pollution
- explicit tool contracts
- easier future expansion to Claude Code / Codex MCP servers
