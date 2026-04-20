from __future__ import annotations

import json
from functools import lru_cache
from typing import Literal

from pydanticai_orchestrator.schemas import (
    OrchestrationReport,
    PromptResponse,
    WorkerName,
    WorkflowResult,
)
from pydanticai_orchestrator.service import OrchestratorService
from pydanticai_orchestrator.settings import get_settings


@lru_cache(maxsize=1)
def _service() -> OrchestratorService:
    return OrchestratorService(get_settings())


def _json_text(value) -> str:
    if hasattr(value, "model_dump"):
        return json.dumps(value.model_dump(), ensure_ascii=False, indent=2)
    return json.dumps(value, ensure_ascii=False, indent=2)


def create_server():
    try:
        from fastmcp import FastMCP
    except Exception as exc:  # pragma: no cover - import-path fallback only
        raise RuntimeError(
            "FastMCP is required. Install dependencies with `uv sync` or ensure pydantic-ai extras are installed."
        ) from exc

    mcp = FastMCP(
        name="my-pydanticai",
        instructions=(
            "MCP surface for my-PydanticAI orchestration. "
            "Use this server to route prompts or invoke specific workers with normalized structured results."
        ),
    )

    @mcp.tool()
    def doctor() -> str:
        return _json_text(_service().doctor())

    @mcp.tool()
    def run_task(prompt: str) -> str:
        result: OrchestrationReport = _service().handle_request(prompt)
        return _json_text(result)

    @mcp.tool()
    def run_prompt(prompt: str) -> str:
        result: PromptResponse = _service().run_prompt_sync(prompt)
        return _json_text(result)

    @mcp.tool()
    def route_request(prompt: str) -> str:
        result = _service().route_request(prompt)
        return _json_text(result)

    @mcp.tool()
    def run_worker(backend: WorkerName, prompt: str) -> str:
        service = _service()
        if backend == "hermes":
            result = service.hermes(prompt)
        elif backend == "pi":
            result = service.pi(prompt)
        elif backend == "codex":
            result = service.codex(prompt)
        else:
            raise ValueError(f"Unsupported direct worker backend: {backend}")
        return _json_text(result)

    @mcp.tool()
    def workflow_action(action: Literal["dry-run", "status", "submit"], task: str = "") -> str:
        service = _service()
        result: WorkflowResult
        if action == "dry-run":
            result = service.stokowski_dry_run()
        elif action == "status":
            result = service.stokowski_status()
        else:
            result = service.stokowski_submit(task)
        return _json_text(result)

    return mcp


def main() -> None:
    server = create_server()
    server.run()


if __name__ == "__main__":
    main()
