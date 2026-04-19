# PydanticAI Orchestrator Architecture

Current layered design:

1. Frontends
- Telegram bot (`telegram_bot.py`)
- CLI (`cli.py`)
- Future: Hermes/OpenClaw/web frontends

2. Service / orchestration layer
- `service.py`
- owns adapters, routing policy, multi-worker execution, review loop scaffolding

3. Agent layer
- `agent.py`
- PydanticAI agent as semantic router and summarizer

4. Adapters
- `adapters/hermes.py`
- `adapters/pi.py`
- `adapters/stokowski.py`

5. Future LangGraph upgrade path
- Keep adapters unchanged
- Move routing/review loop/state transitions into graph nodes
- Keep Telegram/CLI frontends unchanged, just swap the service implementation

Mapping to a future graph runtime:
- `route_request()` -> routing node
- `run_workers_parallel()` -> fan-out/fan-in nodes
- `review_results()` -> review gate node
- `stokowski_submit/status` -> workflow control nodes
- conversation/thread state -> checkpointer-backed graph state
