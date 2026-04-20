# OrchestrationReport outline

Current fields from `schemas.py`:

```python
route: RouteDecision
worker_results: list[WorkerResult]
workflow_results: list[WorkflowResult]
review: ReviewResult | None
answer: str
```

## Field intent

- `route` — why the request went where it did
- `worker_results` — direct worker backend outcomes
- `workflow_results` — workflow-controller outcomes (e.g. Stokowski actions)
- `review` — approval/rejection summary when review loop is used
- `answer` — final outward-facing synthesized response
