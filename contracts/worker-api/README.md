# worker API

`my-PydanticAI` should use a small set of normalized schemas as its internal orchestration language.

## Core schema set

- `WorkerResult`
- `WorkflowResult`
- `RouteDecision`
- `ReviewResult`
- `OrchestrationReport`
- `PromptResponse`

These should be the stable language between:
- frontends
- orchestration runtime
- worker adapters
- bridge adapters
