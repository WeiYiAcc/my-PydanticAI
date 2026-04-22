from __future__ import annotations

import json
import subprocess

from pydanticai_orchestrator.adapters.base import BaseAdapter
from pydanticai_orchestrator.schemas import (
    BridgeEnvelope,
    BridgeMetadata,
    BridgeReturnValue,
    WorkerResult,
)


def _parse_pi_json_output(stdout: str) -> dict:
    """Parse pi --mode json output: JSONL event stream, extract last assistant message."""
    events = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    # Find last assistant message
    assistant = None
    for event in reversed(events):
        msg = event.get('message') if isinstance(event, dict) else None
        if isinstance(msg, dict) and msg.get('role') == 'assistant':
            assistant = msg
            break

    if not assistant:
        return {'ok': False, 'answer': '', 'event_count': len(events)}

    content = assistant.get('content', [])
    if isinstance(content, list):
        answer = '\n'.join(
            part['text'] for part in content
            if isinstance(part, dict) and part.get('type') == 'text' and isinstance(part.get('text'), str)
        ).strip()
    else:
        answer = str(content).strip()

    return {
        'ok': True,
        'answer': answer,
        'provider': assistant.get('provider'),
        'model': assistant.get('model'),
        'api': assistant.get('api'),
        'usage': assistant.get('usage'),
        'response_id': assistant.get('responseId'),
        'stop_reason': assistant.get('stopReason'),
        'event_count': len(events),
    }


class PiAdapter(BaseAdapter):
    def __init__(self, *, mode: str, timeout_seconds: int, pi_bin: str = 'pi') -> None:
        super().__init__(name='pi', mode=mode, timeout_seconds=timeout_seconds)
        self.pi_bin = pi_bin

    def run_task(self, prompt: str, *, provider: str | None = None, model: str | None = None) -> WorkerResult:
        if self.is_mock():
            return self.mock_result(f'[MOCK Pi] Would handle task: {prompt}')

        args = [self.pi_bin, '--mode', 'json', '--no-session']
        if provider:
            args.extend(['--provider', provider])
        if model:
            args.extend(['--model', model])
        args.extend(['-p', prompt])

        command_str = ' '.join(args)
        proc = subprocess.run(args, capture_output=True, text=True, timeout=self.timeout_seconds)
        parsed = _parse_pi_json_output(proc.stdout)

        envelope = BridgeEnvelope(
            return_value=BridgeReturnValue(
                ok=parsed.get('ok', False),
                answer=parsed.get('answer', ''),
                provider=parsed.get('provider'),
                model=parsed.get('model'),
                api=parsed.get('api'),
                usage=parsed.get('usage'),
                response_id=parsed.get('response_id'),
                stop_reason=parsed.get('stop_reason'),
                event_count=parsed.get('event_count'),
            ),
            content=parsed.get('answer', ''),
            metadata=BridgeMetadata(
                stdout=proc.stdout.strip(),
                stderr=proc.stderr.strip(),
            ),
        )

        summary = envelope.content or proc.stderr or proc.stdout or '(no output)'
        return WorkerResult(
            worker='pi',
            ok=(proc.returncode == 0 and parsed.get('ok', False)),
            mode='real',
            summary=summary,
            command=command_str,
            returncode=proc.returncode,
            stdout=envelope.metadata.stdout,
            stderr=envelope.metadata.stderr,
            structured=envelope.model_dump(),
        )
