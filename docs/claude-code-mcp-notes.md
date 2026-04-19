# Claude Code MCP notes

Findings from local validation:

- Claude Code exposes an MCP server via:
  - `claude mcp serve`
- This is a real standard stdio MCP server and can be listed by mcporter:
  - `npx mcporter list --stdio "claude mcp serve" --name claude-mcp --schema`
- The currently exposed tools are not a generic one-shot coding worker surface like Codex's `codex(...)`.
- The visible tool surface includes Claude's internal bridge tools such as:
  - `Agent`
  - `TaskOutput`
  - `Bash`
  - and other operational/session tools

Practical conclusion:
- Claude Code *does* support standard MCP.
- But its current MCP tool shape is more like an interactive/agent bridge than a single generic `run_task(prompt)` worker tool.
- Therefore, Claude Code can be integrated as MCP, but not yet as a drop-in replacement for the Codex generic task worker without an additional bridge layer.

Recommended next step if we want generic task execution over Claude MCP:
- add a small Claude MCP bridge that wraps an opinionated one-shot task interface around Claude Code and exposes a `run_prompt`/`run_task` MCP tool, analogous to the Pi bridge.
