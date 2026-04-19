from __future__ import annotations

from pydanticai_orchestrator.adapters.base import BaseAdapter
from pydanticai_orchestrator.adapters.mcp_common import call_mcp_tool, worker_result_from_mcp
from pydanticai_orchestrator.schemas import WorkerResult
from pydanticai_orchestrator.shell import render_command


class PiAdapter(BaseAdapter):
    def __init__(self, *, mode: str, timeout_seconds: int, command_template: str) -> None:
        super().__init__(name='pi', mode=mode, timeout_seconds=timeout_seconds)
        self.command_template = command_template

    def run_task(self, prompt: str) -> WorkerResult:
        if self.is_mock():
            return self.mock_result(f'[MOCK Pi] Would handle task via MCP: {prompt}')
        command = render_command(self.command_template, prompt=prompt)
        result = call_mcp_tool(command=command, timeout_seconds=self.timeout_seconds)
        return worker_result_from_mcp(worker='pi', mode='real', mcp_result=result)
