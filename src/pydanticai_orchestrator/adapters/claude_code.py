from __future__ import annotations

from pydanticai_orchestrator.adapters.base import BaseAdapter
from pydanticai_orchestrator.adapters.mcp_stdio import call_mcp_stdio, worker_result_from_mcp_stdio
from pydanticai_orchestrator.schemas import WorkerResult


class ClaudeCodeAdapter(BaseAdapter):
    """Claude Code adapter via native MCP server (claude mcp serve)."""

    def __init__(self, *, mode: str, timeout_seconds: int, mcp_command: str = 'claude mcp serve') -> None:
        super().__init__(name='claude_code', mode=mode, timeout_seconds=timeout_seconds)
        self.mcp_command = mcp_command

    def run_task(self, prompt: str) -> WorkerResult:
        if self.is_mock():
            return self.mock_result(f'[MOCK Claude Code] Would handle task: {prompt}')
        result = call_mcp_stdio(
            server_command=self.mcp_command,
            tool_name='run_task',
            arguments={'prompt': prompt},
            timeout_seconds=self.timeout_seconds,
        )
        return worker_result_from_mcp_stdio(worker='claude_code', result=result)
