from __future__ import annotations

import shlex
import subprocess
from dataclasses import dataclass


@dataclass
class CommandRun:
    command: str
    returncode: int
    stdout: str
    stderr: str


def render_command(template: str, **kwargs: str) -> str:
    escaped = {k: shlex.quote(v) for k, v in kwargs.items()}
    return template.format(**escaped)


def run_command(command: str, timeout_seconds: int) -> CommandRun:
    proc = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )
    return CommandRun(
        command=command,
        returncode=proc.returncode,
        stdout=proc.stdout.strip(),
        stderr=proc.stderr.strip(),
    )
