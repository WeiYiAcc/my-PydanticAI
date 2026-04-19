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
    orch_stokowski_mode: Literal['mock', 'real'] = 'mock'

    orch_hermes_command_template: str = 'npx mcporter call run_task prompt={prompt} --stdio "node /home/weiyiacc/.pi/agent/git/github.com/WeiYiAcc/pi-mcp-adapter/hermes-task-mcp-serve.js" --name hermes-task --output json'
    orch_pi_command_template: str = 'npx mcporter call run_prompt prompt={prompt} --stdio "node /home/weiyiacc/.pi/agent/git/github.com/WeiYiAcc/pi-mcp-adapter/pi-mcp-serve.js" --name pi-agent --output json'
    orch_stokowski_bin: str = 'stokowski'
    orch_stokowski_workflow_path: str = ''
    orch_stokowski_submit_template: str = 'stokowski {workflow} --dry-run'
    orch_worker_timeout_seconds: int = 120
    orch_max_parallel_workers: int = 2

    orch_hermes_mcp_stdio: str = 'hermes mcp serve'
    orch_pi_mcp_stdio: str = 'node /home/weiyiacc/.pi/agent/git/github.com/WeiYiAcc/pi-mcp-adapter/pi-mcp-serve.js'
    orch_codex_mcp_stdio: str = 'codex mcp-server'
    orch_codex_command_template: str = 'npx mcporter call codex prompt={prompt} sandbox="workspace-write" approval-policy="never" cwd="/home/weiyiacc/projects/pydanticai-orchestrator" --stdio "codex mcp-server" --name codex-mcp --output json'
    orch_mcporter_bin: str = 'npx mcporter'
    orch_codex_mcp_import: bool = True
    orch_claude_code_mcp_import: bool = True

    telegram_bot_token: str = ''


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
