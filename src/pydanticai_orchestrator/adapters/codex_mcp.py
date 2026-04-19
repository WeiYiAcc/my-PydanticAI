from __future__ import annotations

from pydanticai_orchestrator.adapters.base import BaseAdapter
from pydanticai_orchestrator.adapters.mcp_common import call_mcp_tool, worker_result_from_mcp
from pydanticai_orchestrator.schemas import WorkerResult
from pydanticai_orchestrator.shell import render_command


class CodexMcpAdapter(BaseAdapter):
    def __init__(self, *, mode: str, timeout_seconds: int, command_template: str) -> None:
        super().__init__(name='codex', mode=mode, timeout_seconds=timeout_seconds)
        self.command_template = command_template

    def run_task(self, prompt: str) -> WorkerResult:
        if self.is_mock():
            return self.mock_result(f'[MOCK Codex MCP] Would handle task: {prompt}')
        command = render_command(self.command_template, prompt=prompt)
        result = call_mcp_tool(command=command, timeout_seconds=self.timeout_seconds)
        return worker_result_from_mcp(worker='codex', mode='real', mcp_result=result)
