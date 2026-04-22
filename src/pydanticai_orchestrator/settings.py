from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file_encoding='utf-8', extra='ignore')

    orch_model: str = 'test'

    orch_hermes_mode: Literal['mock', 'real'] = 'mock'
    orch_pi_mode: Literal['mock', 'real'] = 'mock'
    orch_codex_mode: Literal['mock', 'real'] = 'mock'
    orch_claude_code_mode: Literal['mock', 'real'] = 'mock'
    orch_stokowski_mode: Literal['mock', 'real'] = 'mock'

    # MCP stdio servers (Hermes, Codex, Claude Code have native MCP)
    orch_hermes_mcp_command: str = 'hermes mcp serve'
    orch_codex_mcp_command: str = 'codex mcp-server'
    orch_claude_code_mcp_command: str = 'claude mcp serve'

    # Pi — direct CLI (no native MCP server)
    orch_pi_bin: str = 'pi'

    # Stokowski — CLI
    orch_stokowski_bin: str = 'stokowski'
    orch_stokowski_workflow_path: str = ''

    # General
    orch_worker_timeout_seconds: int = 120
    orch_max_parallel_workers: int = 2
    orch_state_dir: str = '.orchestrator-state'

    telegram_bot_token: str = ''

    @property
    def orch_state_path(self) -> Path:
        return Path(self.orch_state_dir).expanduser()


def _load_env_vars(env_file: str = '.env') -> None:
    path = Path(env_file)
    if not path.exists():
        return
    for line in path.read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#') or '=' not in line:
            continue
        key, value = line.split('=', 1)
        os.environ.setdefault(key.strip(), value.strip())


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    _load_env_vars('.env')
    return AppSettings(_env_file='.env')
