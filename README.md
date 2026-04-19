# my-PydanticAI

A forked experimental orchestration project derived from the local `pydanticai-orchestrator` workbench, focused on protocol-first agent bridges and PydanticAI-aligned structured results.

Current focus:
- MCP-first worker integration
- Generic task bridges for Hermes / Pi / Codex
- Bridge outputs normalized toward PydanticAI-style `return_value` / `content` / `metadata`
- Future upstreaming of reusable bridge patterns when stable

Repository layout:
- `src/pydanticai_orchestrator/` — current orchestrator codebase and adapters
- `bridges/` — standalone MCP task bridges for external agents
- `docs/` — migration notes and bridge design findings

Included bridges:
- `bridges/pi-mcp-serve.js`
- `bridges/hermes-task-mcp-serve.js`

Status notes:
- Codex is currently the cleanest generic MCP worker reference.
- Pi works through a JSON-to-MCP bridge.
- Hermes works through a quiet CLI-to-MCP task bridge.
- Claude Code has a real MCP server (`claude mcp serve`) but still needs a dedicated generic task bridge if we want a Codex-like worker shape.

Upstream tracking intent:
- This repo is intended to track upstream PydanticAI concepts and eventually upstream reusable pieces via PRs once the bridge shapes settle.
