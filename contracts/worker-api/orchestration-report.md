# OrchestrationReport contract

## Purpose
Top-level orchestration output returned by request handling.

## Expected contents

- the chosen route
- any worker results
- any workflow results
- optional review decision
- final synthesized answer

## Why it matters

This is the cleanest boundary for:
- future control-plane integrations
- remote invocation from OpenClaw or other hosts
- durable logging / replay / testing
