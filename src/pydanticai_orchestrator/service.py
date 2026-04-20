from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed

from pydanticai_orchestrator.adapters import CodexMcpAdapter, HermesAdapter, PiAdapter, StokowskiAdapter
from pydanticai_orchestrator.agent import OrchestratorDeps, build_agent
from pydanticai_orchestrator.schemas import (
    OrchestrationEvent,
    OrchestrationReport,
    OrchestrationRunState,
    PromptResponse,
    ReviewResult,
    RouteDecision,
    RunSummary,
    WorkerResult,
    WorkflowResult,
)
from pydanticai_orchestrator.settings import AppSettings
from pydanticai_orchestrator.state_store import FileRunStore


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
        self._run_store = FileRunStore(settings.orch_state_path)

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
            'state_dir': str(self.settings.orch_state_path),
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

    def list_runs(self) -> list[OrchestrationRunState]:
        return self._run_store.list_runs()

    def list_run_summaries(self) -> list[RunSummary]:
        return [RunSummary.from_state(run) for run in self.list_runs()]

    def get_run_state(self, run_id: str) -> OrchestrationRunState:
        return self._run_store.load_state(run_id)

    def get_latest_run_state(self) -> OrchestrationRunState | None:
        return self._run_store.load_latest_state()

    def get_run_events(self, run_id: str) -> list[OrchestrationEvent]:
        return self._run_store.load_events(run_id)

    def mark_run_waiting(self, run_id: str, reason: str, node: str = 'review') -> OrchestrationRunState:
        state = self.get_run_state(run_id)
        state.status = 'waiting'
        state.current_node = node
        state.waiting_for = reason
        self._save_state(state)
        self._append_event(state, 'run_waiting', node, {'reason': reason, 'run_id': run_id})
        return state

    def _append_event(
        self,
        state: OrchestrationRunState,
        event_type: str,
        node: str,
        payload: dict | None = None,
    ) -> None:
        state.event_count += 1
        event = OrchestrationEvent(
            seq=state.event_count,
            event_type=event_type,
            node=node,
            payload=payload or {},
        )
        self._run_store.append_event(state.run_id, event)

    def _save_state(self, state: OrchestrationRunState) -> None:
        state.updated_at = state.updated_at.now(state.updated_at.tzinfo)
        self._run_store.save_state(state)

    def _execute_from_state(self, state: OrchestrationRunState) -> OrchestrationReport:
        route = state.route
        if route is None:
            if state.current_node != 'init':
                raise ValueError('Cannot continue run: missing route for non-init state')
            route = self.route_request(state.prompt)
            state.route = route
            state.current_node = 'routing'
            self._save_state(state)
            self._append_event(state, 'route_decided', 'routing', route.model_dump(mode='json'))

        worker_results = list(state.worker_results)
        workflow_results = list(state.workflow_results)
        review = state.review

        if route.target == 'hermes':
            state.current_node = 'worker_execution'
            worker_results = [self.hermes(route.task or state.prompt)]
            answer = worker_results[0].summary
            self._append_event(state, 'worker_completed', 'worker_execution', worker_results[0].model_dump(mode='json'))
        elif route.target == 'codex':
            state.current_node = 'worker_execution'
            worker_results = [self.codex(route.task or state.prompt)]
            answer = worker_results[0].summary
            self._append_event(state, 'worker_completed', 'worker_execution', worker_results[0].model_dump(mode='json'))
        elif route.target == 'pi':
            state.current_node = 'worker_execution'
            worker_results = [self.pi(route.task or state.prompt)]
            answer = worker_results[0].summary
            self._append_event(state, 'worker_completed', 'worker_execution', worker_results[0].model_dump(mode='json'))
        elif route.target == 'stokowski_dry_run':
            state.current_node = 'workflow_execution'
            workflow_results = [self.stokowski_dry_run()]
            answer = workflow_results[0].summary
            self._append_event(state, 'workflow_completed', 'workflow_execution', workflow_results[0].model_dump(mode='json'))
        elif route.target == 'stokowski_status':
            state.current_node = 'workflow_execution'
            workflow_results = [self.stokowski_status()]
            answer = workflow_results[0].summary
            self._append_event(state, 'workflow_completed', 'workflow_execution', workflow_results[0].model_dump(mode='json'))
        elif route.target == 'multi_worker':
            state.current_node = 'worker_execution'
            worker_results = self.run_workers_parallel(route.task or state.prompt, route.workers)
            for worker_result in worker_results:
                self._append_event(state, 'worker_completed', 'worker_execution', worker_result.model_dump(mode='json'))
            state.current_node = 'review'
            review = self.review_results(worker_results)
            answer = '\n\n'.join(
                [f'[{r.worker}] {r.summary}' for r in worker_results]
                + ([f'[review] {review.summary}'] if review else [])
            )
            self._append_event(state, 'review_completed', 'review', review.model_dump(mode='json'))
        else:
            state.current_node = 'direct_answer'
            answer = 'No specific worker selected. Rephrase with Hermes, Pi, or workflow intent.'

        state.worker_results = worker_results
        state.workflow_results = workflow_results
        state.review = review
        state.answer = answer
        state.status = 'completed'
        state.current_node = 'completed'
        state.waiting_for = None
        state.error = None
        self._save_state(state)
        self._append_event(state, 'run_completed', 'completed', {'answer': answer})

        return OrchestrationReport(
            route=route,
            worker_results=worker_results,
            workflow_results=workflow_results,
            review=review,
            answer=answer,
            run_id=state.run_id,
        )

    def continue_run(self, run_id: str) -> OrchestrationReport:
        state = self.get_run_state(run_id)
        if state.status == 'completed':
            raise ValueError(f'Run {run_id} is already completed')
        if state.status == 'running':
            raise ValueError(f'Run {run_id} is already running')
        state.status = 'running'
        self._save_state(state)
        self._append_event(state, 'run_resumed', state.current_node, {'run_id': run_id})
        try:
            return self._execute_from_state(state)
        except Exception as exc:
            state.status = 'failed'
            state.current_node = 'failed'
            state.error = str(exc)
            self._save_state(state)
            self._append_event(state, 'run_failed', 'failed', {'error': str(exc)})
            raise

    def handle_request(self, prompt: str) -> OrchestrationReport:
        state = OrchestrationRunState(prompt=prompt, status='running', current_node='init')
        self._save_state(state)
        self._append_event(state, 'run_started', 'init', {'prompt': prompt})
        try:
            return self._execute_from_state(state)
        except Exception as exc:
            state.status = 'failed'
            state.current_node = 'failed'
            state.error = str(exc)
            self._save_state(state)
            self._append_event(state, 'run_failed', 'failed', {'error': str(exc)})
            raise
