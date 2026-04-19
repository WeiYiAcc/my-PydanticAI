from __future__ import annotations

from dataclasses import dataclass

from pydantic_ai import Agent, RunContext
from pydantic_ai.models.function import FunctionModel
from pydantic_ai.messages import ModelResponse, TextPart

from pydanticai_orchestrator.schemas import PromptResponse


@dataclass
class OrchestratorDeps:
    service: object


def resolve_model(model_name: str):
    if model_name == 'test':
        async def function_model(_messages, _agent_info):
            return ModelResponse(parts=[TextPart(content='{"answer":"Test model response: use CLI/Telegram with worker-specific prompts or configure a real model for semantic routing."}')])
        return FunctionModel(function=function_model, model_name='orchestrator-test')
    return model_name


def build_agent(service, model_name: str):
    model = resolve_model(model_name)
    agent = Agent(
        model,
        deps_type=OrchestratorDeps,
        output_type=PromptResponse,
        instructions=(
            'You are an orchestration assistant. You help route requests across Hermes, Pi, and Stokowski. '
            'Use Hermes for general coding and code analysis, Pi for pi-mono-oriented coding requests, '
            'Stokowski for workflow dry-run/status style requests, and recommend multi-worker mode when comparison or cross-checking is requested. '
            'Respond in one concise paragraph.'
        ),
    )

    @agent.tool
    def use_hermes(ctx: RunContext[OrchestratorDeps], task: str) -> str:
        return ctx.deps.service.hermes(task).model_dump_json(indent=2)

    @agent.tool
    def use_pi(ctx: RunContext[OrchestratorDeps], task: str) -> str:
        return ctx.deps.service.pi(task).model_dump_json(indent=2)

    @agent.tool
    def run_stokowski_dry_run(ctx: RunContext[OrchestratorDeps]) -> str:
        return ctx.deps.service.stokowski_dry_run().model_dump_json(indent=2)

    @agent.tool
    def run_stokowski_status(ctx: RunContext[OrchestratorDeps]) -> str:
        return ctx.deps.service.stokowski_status().model_dump_json(indent=2)

    return agent
