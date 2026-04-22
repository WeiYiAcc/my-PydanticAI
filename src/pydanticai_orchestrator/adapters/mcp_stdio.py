"""Shared MCP stdio client for adapters that talk to native MCP servers.

Used by: HermesAdapter, CodexMcpAdapter, ClaudeCodeAdapter.

These workers expose real MCP servers over stdio (e.g. `hermes mcp serve`,
`codex mcp-server`, `claude mcp serve`).  This module handles the JSON-RPC
protocol to initialize, call a tool, and shut down the server process.
"""
from __future__ import annotations

import json
import shlex
import subprocess
import threading
from dataclasses import dataclass, field
from typing import Any

from pydanticai_orchestrator.schemas import (
    BridgeEnvelope,
    BridgeMetadata,
    BridgeReturnValue,
    WorkerResult,
)


@dataclass
class McpStdioResult:
    server_command: str
    tool_name: str
    ok: bool
    content: str = ''
    structured: dict[str, Any] = field(default_factory=dict)
    error: str = ''
    raw_stdout: str = ''
    raw_stderr: str = ''


def _jsonrpc_request(method: str, params: dict | None = None, req_id: int = 1) -> bytes:
    msg = {'jsonrpc': '2.0', 'id': req_id, 'method': method}
    if params is not None:
        msg['params'] = params
    return json.dumps(msg).encode() + b'\n'


def _jsonrpc_notification(method: str, params: dict | None = None) -> bytes:
    msg = {'jsonrpc': '2.0', 'method': method}
    if params is not None:
        msg['params'] = params
    return json.dumps(msg).encode() + b'\n'


def _read_jsonrpc_response(stdout_lines: list[str], req_id: int) -> dict | None:
    for line in stdout_lines:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(msg, dict) and msg.get('id') == req_id:
            return msg
    return None


def _extract_content_text(result: dict) -> str:
    content = result.get('content', [])
    if isinstance(content, list):
        texts = []
        for item in content:
            if isinstance(item, dict) and item.get('type') == 'text':
                texts.append(item.get('text', ''))
        return '\n'.join(texts).strip()
    if isinstance(content, str):
        return content.strip()
    return ''


def call_mcp_stdio(
    *,
    server_command: str,
    tool_name: str,
    arguments: dict[str, Any],
    timeout_seconds: int,
) -> McpStdioResult:
    """Spawn an MCP server over stdio, call one tool, return result."""
    args = shlex.split(server_command)

    try:
        proc = subprocess.Popen(
            args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except FileNotFoundError:
        return McpStdioResult(
            server_command=server_command,
            tool_name=tool_name,
            ok=False,
            error=f'Command not found: {args[0]}',
        )

    stdout_lines: list[str] = []
    stderr_text = ''

    def _read_stderr():
        nonlocal stderr_text
        stderr_text = proc.stderr.read().decode(errors='replace')

    stderr_thread = threading.Thread(target=_read_stderr, daemon=True)
    stderr_thread.start()

    try:
        # 1. Initialize
        proc.stdin.write(_jsonrpc_request('initialize', {
            'protocolVersion': '2024-11-05',
            'capabilities': {},
            'clientInfo': {'name': 'my-pydanticai', 'version': '0.1.0'},
        }, req_id=1))
        proc.stdin.flush()

        # 2. Send initialized notification
        proc.stdin.write(_jsonrpc_notification('notifications/initialized'))
        proc.stdin.flush()

        # 3. Call tool
        proc.stdin.write(_jsonrpc_request('tools/call', {
            'name': tool_name,
            'arguments': arguments,
        }, req_id=2))
        proc.stdin.flush()

        # Close stdin to signal we're done
        proc.stdin.close()

        # Read all stdout
        raw_stdout = proc.stdout.read().decode(errors='replace')
        stdout_lines = raw_stdout.splitlines()

        proc.wait(timeout=timeout_seconds)
        stderr_thread.join(timeout=5)

    except subprocess.TimeoutExpired:
        proc.kill()
        stderr_thread.join(timeout=2)
        return McpStdioResult(
            server_command=server_command,
            tool_name=tool_name,
            ok=False,
            error=f'Timeout after {timeout_seconds}s',
            raw_stderr=stderr_text,
        )
    except Exception as exc:
        proc.kill()
        stderr_thread.join(timeout=2)
        return McpStdioResult(
            server_command=server_command,
            tool_name=tool_name,
            ok=False,
            error=str(exc),
            raw_stderr=stderr_text,
        )

    # Parse tool call response (id=2)
    response = _read_jsonrpc_response(stdout_lines, req_id=2)

    if not response:
        return McpStdioResult(
            server_command=server_command,
            tool_name=tool_name,
            ok=False,
            error='No JSON-RPC response for tool call',
            raw_stdout='\n'.join(stdout_lines),
            raw_stderr=stderr_text,
        )

    if 'error' in response:
        err = response['error']
        return McpStdioResult(
            server_command=server_command,
            tool_name=tool_name,
            ok=False,
            error=err.get('message', str(err)),
            structured=response,
            raw_stdout='\n'.join(stdout_lines),
            raw_stderr=stderr_text,
        )

    result = response.get('result', {})
    is_error = result.get('isError', False)
    content_text = _extract_content_text(result)

    return McpStdioResult(
        server_command=server_command,
        tool_name=tool_name,
        ok=not is_error,
        content=content_text,
        structured=result,
        raw_stdout='\n'.join(stdout_lines),
        raw_stderr=stderr_text,
    )


def worker_result_from_mcp_stdio(*, worker: str, result: McpStdioResult) -> WorkerResult:
    """Convert McpStdioResult to WorkerResult with BridgeEnvelope."""
    envelope = BridgeEnvelope(
        return_value=BridgeReturnValue(
            ok=result.ok,
            answer=result.content or result.error,
        ),
        content=result.content or result.error,
        metadata=BridgeMetadata(
            stdout=result.raw_stdout,
            stderr=result.raw_stderr,
            raw_payload=result.structured if result.structured else None,
        ),
    )

    summary = result.content or result.error or '(no output)'
    return WorkerResult(
        worker=worker,
        ok=result.ok,
        mode='real',
        summary=summary,
        command=result.server_command,
        returncode=0 if result.ok else 1,
        stdout=envelope.metadata.stdout,
        stderr=envelope.metadata.stderr,
        structured=envelope.model_dump(),
    )
