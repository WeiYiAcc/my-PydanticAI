from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydanticai_orchestrator.schemas import WorkerResult


Mode = Literal['mock', 'real']


@dataclass
class BaseAdapter:
    name: str
    mode: Mode
    timeout_seconds: int

    def is_mock(self) -> bool:
        return self.mode == 'mock'

    def mock_result(self, summary: str) -> WorkerResult:
        return WorkerResult(worker=self.name, ok=True, mode='mock', summary=summary)
