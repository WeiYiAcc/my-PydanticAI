# my-PydanticAI responsibility narrowing

## Current decision

Temporarily **defer optimization and expansion of `my-PydanticAI` as a user-facing control plane**.

For the near term:
- **Hermes** should own Telegram (and similar messaging/frontdoor) duties.
- `my-PydanticAI` should be treated as an orchestration/bridge kernel under incubation.

This reduces overlap and keeps the system easier to operate while contracts are still being documented.

---

## Temporary role split

### Hermes owns
- Telegram control plane
- Email / messaging gateway frontdoor duties
- user-facing chat/session handling
- gateway/platform routing
- host/runtime-level subagent execution where Hermes alone is sufficient

### my-PydanticAI keeps
- normalized worker abstraction (`WorkerResult`, `WorkflowResult`, etc.)
- route policy experiments across heterogeneous workers
- Pi / Hermes / Codex / Stokowski bridge experimentation
- future orchestration kernel for multi-backend comparison/review flows
- schema-first merge target for Stokowski-related workflow logic

### my-PydanticAI should NOT own right now
- Telegram bot as primary operational frontdoor
- duplicated messaging control plane already handled by Hermes
- broad operational ownership of every host runtime before contracts settle

---

## Why this split is better right now

1. Hermes already supports Telegram and multi-platform messaging natively.
2. Hermes already has skills, memory, gateway, and subagent capabilities.
3. `my-PydanticAI` still needs contract stabilization before it can become a clean universal control plane.
4. Narrowing the scope prevents double-frontdoor complexity.
5. It keeps future integration possible:
   - Hermes as frontdoor
   - `my-PydanticAI` as orchestration kernel

---

## Temporary operating model

```text
Telegram / Email / user-facing entry
        ↓
      Hermes
        ↓
  (optional) my-PydanticAI
        ↓
 Pi / Codex / Stokowski / future workers
```

### Interpretations

- If Hermes alone can handle the task, do not force `my-PydanticAI` into the loop.
- Use `my-PydanticAI` only when heterogeneous worker orchestration or normalized bridge behavior is actually needed.

---

## Revisit conditions

Re-open `my-PydanticAI` optimization when one or more of these become true:

1. You need stable cross-backend routing between Hermes / Pi / Codex / Stokowski.
2. You need a unified structured result contract across workers.
3. You want Hermes/OpenClaw/OpenAgent to share one orchestration kernel.
4. Stokowski merge work begins in earnest.
5. Telegram/email frontdoor is no longer enough and orchestration-specific frontends are justified.

Until then, prefer documentation and contract extraction over implementation growth.
