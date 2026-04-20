# my-PydanticAI × Stokowski merge blueprint

This document describes the **priority integration path** between `apps/my-PydanticAI` and `upstreams/stokowski`.

Goal:
- keep Stokowski usable as-is today
- define the schema boundary required for later convergence
- let `my-PydanticAI` absorb workflow-orchestration capabilities without tightly coupling to Stokowski internals

---

## 1. Why Stokowski is the first merge target

Compared with other backends, Stokowski is the closest to a workflow controller:
- state machine
- issue tracker integration (Linear)
- workspace lifecycle
- retry/backoff logic
- gate/rework semantics
- web dashboard / operational state

`my-PydanticAI` already has placeholders for workflow control:
- `stokowski_dry_run`
- `stokowski_status`
- `stokowski_submit`
- `WorkflowResult`

So the merge priority should be schema-first.

---

## 2. Stokowski surfaces that matter

### 2.1 Config surface
From `stokowski/config.py`:
- `TrackerConfig`
- `PollingConfig`
- `WorkspaceConfig`
- `HooksConfig`
- `ClaudeConfig`
- `AgentConfig`
- `ServerConfig`
- `LinearStatesConfig`
- `PromptsConfig`
- `StateConfig`
- `ServiceConfig`

### 2.2 Domain surface
From `stokowski/models.py`:
- `Issue`
- `BlockerRef`
- `RunAttempt`
- `RetryEntry`

### 2.3 Operational surface
From `stokowski/main.py` and README:
- dry-run validation
- status
- orchestration run
- dashboard/web mode

### 2.4 Runner surface
From `stokowski/runner.py`:
- Claude runner
- Codex runner
- before/after hook lifecycle
- timeout / stall / pid management

---

## 3. Recommended contract split

### 3.1 Keep `my-PydanticAI` canonical schemas
Do **not** replace `WorkflowResult` or `OrchestrationReport` with raw Stokowski models.

Instead:
- Stokowski config/domain objects are upstream-native
- `my-PydanticAI` schemas remain the canonical orchestration/report language

### 3.2 Introduce a mapping layer
Planned future location:

```text
apps/my-PydanticAI/adapters/workers/stokowski.py
apps/my-PydanticAI/adapters/external-services/stokowski/
apps/my-PydanticAI/contracts/stokowski-merge-blueprint.md
```

Mapping responsibility:
- Stokowski raw CLI/config/domain output
  -> normalized `WorkflowResult`
- optionally Stokowski issue/run state
  -> normalized orchestration metadata

---

## 4. Merge strategy

### Phase 1 — façade integration (already started)
Use Stokowski through:
- CLI execution
- `dry-run`
- `status`
- `submit`

Return normalized `WorkflowResult`.

### Phase 2 — schema alignment
Document and stabilize mappings for:
- Stokowski workflow action -> `WorkflowResult.action`
- issue/workspace/run metadata -> `structured`
- failure/exit semantics -> `ok`, `returncode`, `stderr`

### Phase 3 — state machine absorption
If desired later, migrate selected Stokowski concepts into `my-PydanticAI` runtime modules:
- workflow state transitions
- gate/rework policy
- workspace lifecycle
- retry scheduling

But only after contracts are stable.

### Phase 4 — optional runtime fusion
At that point, Stokowski can either remain:
- an upstream engine with a stable adapter

or become:
- a partially absorbed workflow runtime inside `my-PydanticAI`

---

## 5. What should not be merged early

Do not early-merge these into canonical internal schema:
- Linear GraphQL response shapes
- raw Stokowski dataclasses
- runner-specific CLI args
- hook script text blobs
- dashboard-only state representations

These belong in adapters or upstream-native config docs unless proven reusable.

---

## 6. Immediate documentation tasks

Before code changes, write these docs next:

1. `contracts/worker-api/workflow-result.md` ✅
2. `contracts/stokowski-merge-blueprint.md` ✅
3. future: `contracts/bridge-api/stokowski-cli-mapping.md`
4. future: `contracts/worker-api/workflow-structured-fields.md`

---

## 7. Practical rule for future refactors

When touching Stokowski integration code, always ask:

- Is this a Stokowski-native concern?
  - keep it in the adapter / upstream docs
- Is this a generic workflow orchestration concern?
  - elevate it into `my-PydanticAI` contract/runtime docs

This keeps the merge disciplined instead of accidental.
