from __future__ import annotations

import shlex

from pydanticai_orchestrator.adapters.base import BaseAdapter
from pydanticai_orchestrator.schemas import WorkflowResult
from pydanticai_orchestrator.shell import run_command


class StokowskiAdapter(BaseAdapter):
    def __init__(self, *, mode: str, timeout_seconds: int, binary: str, workflow_path: str) -> None:
        super().__init__(name='stokowski', mode=mode, timeout_seconds=timeout_seconds)
        self.binary = binary
        self.workflow_path = workflow_path

    def _missing(self, action: str) -> WorkflowResult:
        return WorkflowResult(action=action, ok=False, mode='real', summary='ORCH_STOKOWSKI_WORKFLOW_PATH is not set', stderr='missing workflow path')

    def dry_run(self) -> WorkflowResult:
        if self.is_mock():
            return WorkflowResult(action='dry_run', ok=True, mode='mock', summary='[MOCK Stokowski] Would run workflow dry-run')
        if not self.workflow_path:
            return self._missing('dry_run')
        command = f"{shlex.quote(self.binary)} {shlex.quote(self.workflow_path)} --dry-run"
        result = run_command(command, self.timeout_seconds)
        ok = result.returncode == 0
        summary = result.stdout or result.stderr or '(no output)'
        return WorkflowResult(action='dry_run', ok=ok, mode='real', summary=summary, command=result.command, returncode=result.returncode, stdout=result.stdout, stderr=result.stderr)

    def status(self) -> WorkflowResult:
        if self.is_mock():
            return WorkflowResult(action='status', ok=True, mode='mock', summary='[MOCK Stokowski] status unavailable in mock mode; assume idle')
        if not self.workflow_path:
            return self._missing('status')
        command = f"{shlex.quote(self.binary)} --help"
        result = run_command(command, self.timeout_seconds)
        ok = result.returncode == 0
        summary = 'Stokowski reachable' if ok else (result.stderr or 'status check failed')
        return WorkflowResult(action='status', ok=ok, mode='real', summary=summary, command=result.command, returncode=result.returncode, stdout=result.stdout, stderr=result.stderr)

    def submit(self, task: str) -> WorkflowResult:
        if self.is_mock():
            return WorkflowResult(action='submit', ok=True, mode='mock', summary=f'[MOCK Stokowski] Would submit task: {task}', structured={'task': task})
        if not self.workflow_path:
            return self._missing('submit')
        command = f"{shlex.quote(self.binary)} {shlex.quote(self.workflow_path)} --task {shlex.quote(task)}"
        result = run_command(command, self.timeout_seconds)
        ok = result.returncode == 0
        summary = result.stdout or result.stderr or '(no output)'
        return WorkflowResult(action='submit', ok=ok, mode='real', summary=summary, command=result.command, returncode=result.returncode, stdout=result.stdout, stderr=result.stderr, structured={'task': task})
