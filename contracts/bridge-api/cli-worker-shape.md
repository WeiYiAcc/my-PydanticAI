# CLI worker shape

## Purpose
Describe the fallback contract when a backend is invoked through CLI rather than MCP.

## Minimal expectations

- deterministic exit code
- structured stdout when possible
- backend-specific stderr tolerated but not relied on semantically
- wrapper adapter responsible for normalization into `WorkerResult`
