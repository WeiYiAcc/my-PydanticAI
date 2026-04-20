# WorkerResult contract

## Purpose
Represents the normalized outcome of invoking one worker backend.

## Expected semantics

A worker result should carry enough information to:
- detect success/failure
- show a concise summary
- preserve structured metadata for review/routing
- remain transport-agnostic

## Current backend examples

- Hermes worker adapter
- Pi worker adapter
- Codex MCP worker adapter
- future Claude/OpenAgent/OpenClaw adapters

## Stability rule

New worker adapters should normalize into this shape rather than inventing backend-specific top-level result formats.
