from __future__ import annotations

import json
from pathlib import Path

from pydanticai_orchestrator.schemas import OrchestrationEvent, OrchestrationRunState


class FileRunStore:
    def __init__(self, root: str | Path):
        self.root = Path(root).expanduser()
        self.root.mkdir(parents=True, exist_ok=True)

    def runs_dir(self) -> Path:
        path = self.root / 'runs'
        path.mkdir(parents=True, exist_ok=True)
        return path

    def run_dir(self, run_id: str) -> Path:
        path = self.runs_dir() / run_id
        path.mkdir(parents=True, exist_ok=True)
        return path

    def state_path(self, run_id: str) -> Path:
        return self.run_dir(run_id) / 'state.json'

    def events_path(self, run_id: str) -> Path:
        return self.run_dir(run_id) / 'events.jsonl'

    def latest_run_pointer_path(self) -> Path:
        return self.root / 'latest_run.txt'

    def save_state(self, state: OrchestrationRunState) -> Path:
        path = self.state_path(state.run_id)
        path.write_text(state.model_dump_json(indent=2), encoding='utf-8')
        self.latest_run_pointer_path().write_text(state.run_id, encoding='utf-8')
        return path

    def load_state(self, run_id: str) -> OrchestrationRunState:
        return OrchestrationRunState.model_validate_json(self.state_path(run_id).read_text(encoding='utf-8'))

    def latest_run_id(self) -> str | None:
        path = self.latest_run_pointer_path()
        if not path.exists():
            return None
        run_id = path.read_text(encoding='utf-8').strip()
        return run_id or None

    def load_latest_state(self) -> OrchestrationRunState | None:
        run_id = self.latest_run_id()
        if run_id is None:
            return None
        return self.load_state(run_id)

    def list_runs(self) -> list[OrchestrationRunState]:
        runs: list[OrchestrationRunState] = []
        for state_file in sorted(self.runs_dir().glob('*/state.json'), reverse=True):
            runs.append(OrchestrationRunState.model_validate_json(state_file.read_text(encoding='utf-8')))
        runs.sort(key=lambda run: run.updated_at, reverse=True)
        return runs

    def append_event(self, run_id: str, event: OrchestrationEvent) -> Path:
        path = self.events_path(run_id)
        with path.open('a', encoding='utf-8') as fh:
            fh.write(json.dumps(event.model_dump(mode='json'), ensure_ascii=False) + '\n')
        return path

    def load_events(self, run_id: str) -> list[OrchestrationEvent]:
        path = self.events_path(run_id)
        if not path.exists():
            return []
        events: list[OrchestrationEvent] = []
        with path.open('r', encoding='utf-8') as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                events.append(OrchestrationEvent.model_validate(json.loads(line)))
        return events
