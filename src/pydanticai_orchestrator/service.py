from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed

from pydanticai_orchestrator.adapters import CodexMcpAdapter, HermesAdapter, PiAdapter, StokowskiAdapter
from pydanticai_orchestrator.agent import OrchestratorDeps, build_agent
from pydanticai_orchestrator.schemas import (
    OrchestrationReport,
    PromptResponse,
    ReviewResult,
    RouteDecision,
    WorkerResult,
    WorkflowResult,
)
from pydanticai_orchestrator.settings import AppSettings


class OrchestratorService:
    def __init__(self, settings: AppSettings):
        self.settings = settings
        self._hermes = HermesAdapter(
            mode=settings.orch_hermes_mode,
            timeout_seconds=settings.orch_worker_timeout_seconds,
            command_template=settings.orch_hermes_command_template,
        )
        self._pi = PiAdapter(
            mode=settings.orch_pi_mode,
            timeout_seconds=settings.orch_worker_timeout_seconds,
            command_template=settings.orch_pi_command_template,
        )
        self._codex = CodexMcpAdapter(
            mode=settings.orch_hermes_mode,
            timeout_seconds=settings.orch_worker_timeout_seconds,
            command_template=settings.orch_codex_command_template,
        )
        self._stokowski = StokowskiAdapter(
            mode=settings.orch_stokowski_mode,
            timeout_seconds=settings.orch_worker_timeout_seconds,
            binary=settings.orch_stokowski_bin,
            workflow_path=settings.orch_stokowski_workflow_path,
            submit_template=settings.orch_stokowski_submit_template,
        )
        self._agent = build_agent(self, settings.orch_model)

    def hermes(self, task: str) -> WorkerResult:
        return self._hermes.run_task(task)

    def codex(self, task: str) -> WorkerResult:
        return self._codex.run_task(task)

    def pi(self, task: str) -> WorkerResult:
        return self._pi.run_task(task)

    def stokowski_dry_run(self) -> WorkflowResult:
        return self._stokowski.dry_run()

    def stokowski_status(self) -> WorkflowResult:
        return self._stokowski.status()

    def stokowski_submit(self, task: str) -> WorkflowResult:
        return self._stokowski.submit(task)

    def doctor(self) -> dict:
        return {
            'model': self.settings.orch_model,
            'hermes_mode': self.settings.orch_hermes_mode,
            'pi_mode': self.settings.orch_pi_mode,
            'stokowski_mode': self.settings.orch_stokowski_mode,
            'stokowski_workflow_path': self.settings.orch_stokowski_workflow_path,
            'telegram_configured': bool(self.settings.telegram_bot_token),
            'max_parallel_workers': self.settings.orch_max_parallel_workers,
            'hermes_mcp_stdio': self.settings.orch_hermes_mcp_stdio,
            'pi_mcp_stdio': self.settings.orch_pi_mcp_stdio,
            'codex_mcp_stdio': self.settings.orch_codex_mcp_stdio,
            'mcporter_bin': self.settings.orch_mcporter_bin,
            'codex_mcp_import': self.settings.orch_codex_mcp_import,
            'claude_code_mcp_import': self.settings.orch_claude_code_mcp_import,
        }

    def route_request(self, prompt: str) -> RouteDecision:
        lowered = prompt.lower()
        if any(k in lowered for k in ['stokowski status', 'workflow status']):
            return RouteDecision(target='stokowski_status', rationale='explicit workflow status request')
        if any(k in lowered for k in ['stokowski', 'workflow dry-run', 'dry run workflow']):
            return RouteDecision(target='stokowski_dry_run', rationale='explicit workflow dry-run request')
        if any(k in lowered for k in ['submit workflow', 'send to workflow']):
            return RouteDecision(target='stokowski_status', task=prompt, rationale='workflow submission-like request')
        if any(k in lowered for k in ['both', 'compare', 'cross-check', 'review with hermes and pi']):
            return RouteDecision(
                target='multi_worker',
                task=prompt,
                rationale='request mentions multiple workers',
                use_review_loop=True,
                use_multi_worker=True,
                workers=['hermes', 'pi'],
            )
        if 'codex' in lowered:
            return RouteDecision(target='codex', task=prompt, rationale='codex-oriented MCP worker request')
        if 'pi' in lowered or 'pi-mono' in lowered:
            return RouteDecision(target='pi', task=prompt, rationale='pi-oriented request')
        if any(k in lowered for k in ['code', 'implement', 'analyze', 'refactor', 'hermes']):
            return RouteDecision(target='hermes', task=prompt, rationale='coding/general analysis request')
        return RouteDecision(target='direct_answer', task=prompt, rationale='no worker-specific keywords')

    def review_results(self, worker_results: list[WorkerResult]) -> ReviewResult:
        failures = [r for r in worker_results if not r.ok]
        if failures:
            return ReviewResult(
                approved=False,
                summary='One or more workers failed',
                reasons=[f'{r.worker}: {r.summary}' for r in failures],
            )
        return ReviewResult(
            approved=True,
            summary='All worker results look healthy',
            reasons=[f'{r.worker}: ok' for r in worker_results],
        )

    def run_workers_parallel(self, task: str, workers: list[str]) -> list[WorkerResult]:
        call_map = {
            'hermes': lambda: self.hermes(task),
            'pi': lambda: self.pi(task),
            'codex': lambda: self.codex(task),
        }
        results: list[WorkerResult] = []
        selected = [w for w in workers if w in call_map][: self.settings.orch_max_parallel_workers]
        with ThreadPoolExecutor(max_workers=max(1, len(selected))) as pool:
            futures = {pool.submit(call_map[w]): w for w in selected}
            for future in as_completed(futures):
                results.append(future.result())
        results.sort(key=lambda r: r.worker)
        return results

    def run_prompt_sync(self, prompt: str) -> PromptResponse:
        deps = OrchestratorDeps(service=self)
        result = self._agent.run_sync(prompt, deps=deps)
        output = result.output
        if isinstance(output, PromptResponse):
            return output
        if isinstance(output, str):
            return PromptResponse(answer=output)
        return PromptResponse(answer=str(output))

    def handle_request(self, prompt: str) -> OrchestrationReport:
        route = self.route_request(prompt)
        worker_results: list[WorkerResult] = []
        workflow_results: list[WorkflowResult] = []
        review: ReviewResult | None = None

        if route.target == 'hermes':
            worker_results.append(self.hermes(route.task or prompt))
            answer = worker_results[0].summary
        elif route.target == 'codex':
            worker_results.append(self.codex(route.task or prompt))
            answer = worker_results[0].summary
        elif route.target == 'pi':
            worker_results.append(self.pi(route.task or prompt))
            answer = worker_results[0].summary
        elif route.target == 'stokowski_dry_run':
            workflow_results.append(self.stokowski_dry_run())
            answer = workflow_results[0].summary
        elif route.target == 'stokowski_status':
            workflow_results.append(self.stokowski_status())
            answer = workflow_results[0].summary
        elif route.target == 'multi_worker':
            worker_results = self.run_workers_parallel(route.task or prompt, route.workers)
            review = self.review_results(worker_results)
            answer = '\n\n'.join(
                [f'[{r.worker}] {r.summary}' for r in worker_results]
                + ([f'[review] {review.summary}'] if review else [])
            )
        else:
            answer = 'No specific worker selected. Rephrase with Hermes, Pi, or workflow intent.'

        return OrchestrationReport(
            route=route,
            worker_results=worker_results,
            workflow_results=workflow_results,
            review=review,
            answer=answer,
        )
