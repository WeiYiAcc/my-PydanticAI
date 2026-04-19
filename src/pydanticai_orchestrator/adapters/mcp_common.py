from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from typing import Any

from pydanticai_orchestrator.schemas import BridgeEnvelope, BridgeMetadata, BridgeReturnValue, WorkerResult


@dataclass
class McpCallResult:
    tool_name: str
    command: str
    returncode: int
    stdout: str
    stderr: str
    payload: dict | None


def _extract_payload(stdout: str) -> dict | None:
    text = stdout.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    for raw_line in reversed(text.splitlines()):
        line = raw_line.strip()
        if not line:
            continue
        try:
            return json.loads(line)
        except json.JSONDecodeError:
            continue
    return None


def call_mcp_tool(*, command: str, timeout_seconds: int) -> McpCallResult:
    proc = subprocess.run(
        command,
        shell=True,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )
    payload = _extract_payload(proc.stdout)
    tool_name = ''
    if payload and isinstance(payload, dict):
        tool_name = str(payload.get('tool_name', ''))
    return McpCallResult(
        tool_name=tool_name,
        command=command,
        returncode=proc.returncode,
        stdout=proc.stdout.strip(),
        stderr=proc.stderr.strip(),
        payload=payload,
    )


def _bridge_envelope_from_payload(payload: dict | None, *, stdout: str, stderr: str) -> BridgeEnvelope:
    payload = payload if isinstance(payload, dict) else {}
    content_field = payload.get('content')
    content_text = ''
    if isinstance(content_field, list):
        texts: list[str] = []
        for item in content_field:
            if isinstance(item, dict) and item.get('type') == 'text' and isinstance(item.get('text'), str):
                texts.append(item['text'])
        content_text = '\n'.join(texts).strip()
    elif isinstance(content_field, str):
        content_text = content_field.strip()

    return_value = payload.get('return_value') if isinstance(payload.get('return_value'), dict) else {}
    metadata = payload.get('metadata') if isinstance(payload.get('metadata'), dict) else {}

    if not return_value:
        return_value = {
            'ok': not bool(payload.get('isError')),
            'answer': payload.get('answer') or content_text or payload.get('result') or '',
            'provider': payload.get('provider'),
            'model': payload.get('model'),
            'api': payload.get('api'),
            'usage': payload.get('usage'),
            'response_id': payload.get('responseId'),
            'session_id': payload.get('session_id'),
            'thread_id': payload.get('threadId') or payload.get('conversationId'),
            'stop_reason': payload.get('stopReason'),
            'event_count': payload.get('eventCount'),
        }

    if not metadata:
        metadata = {
            'stdout': stdout,
            'stderr': stderr,
            'raw_payload': payload,
        }

    return BridgeEnvelope(
        return_value=BridgeReturnValue.model_validate(return_value),
        content=content_text or str(return_value.get('answer') or ''),
        metadata=BridgeMetadata.model_validate(metadata),
    )


def worker_result_from_mcp(*, worker: str, mode: str, mcp_result: McpCallResult) -> WorkerResult:
    payload = mcp_result.payload or {}
    is_error = bool(payload.get('isError')) if isinstance(payload, dict) else False
    envelope = _bridge_envelope_from_payload(payload, stdout=mcp_result.stdout, stderr=mcp_result.stderr)
    summary = envelope.content or envelope.return_value.answer or mcp_result.stderr or mcp_result.stdout or '(no output)'
    return WorkerResult(
        worker=worker,
        ok=(mcp_result.returncode == 0 and not is_error and envelope.return_value.ok),
        mode=mode,
        summary=summary,
        command=mcp_result.command,
        returncode=mcp_result.returncode,
        stdout=envelope.metadata.stdout,
        stderr=envelope.metadata.stderr,
        structured=envelope.model_dump(),
    )
