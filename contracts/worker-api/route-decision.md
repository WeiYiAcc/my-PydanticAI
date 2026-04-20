# RouteDecision contract

## Purpose
Captures the orchestrator's decision about where a request should go.

## Current target families

- direct worker target (`hermes`, `pi`, `codex`)
- workflow control target (`stokowski_status`, `stokowski_dry_run`)
- multi-worker target (`multi_worker`)
- fallback/direct answer target (`direct_answer`)

## Stability rule

Routing policy may change; route *shape* should remain stable for callers and logs.
