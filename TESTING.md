# Testing Checklist

Environment:
```bash
source /home/weiyiacc/.venvs/pydanticai/bin/activate
cd /home/weiyiacc/projects/pydanticai-orchestrator
```

## Smoke tests already verified
These passed locally:
```bash
pydanticai-orchestrator doctor
pydanticai-orchestrator worker codex 'analyze auth module'
pydanticai-orchestrator worker pi 'review build assumptions'
pydanticai-orchestrator worker hermes 'show Hermes MCP status'
# real mode uses MCP transport via mcporter (Codex/Pi/Hermes task bridge)
pydanticai-orchestrator stokowski dry-run
pydanticai-orchestrator stokowski status
pydanticai-orchestrator prompt 'Use Codex for coding analysis and summarize the result'
pydanticai-orchestrator route 'compare hermes and pi on this repo'
python -m unittest discover -s tests -v
python -c 'import pydanticai_orchestrator.telegram_bot as t; print(bool(t))'
```

## Telegram test
Set a token and run polling:
```bash
export TELEGRAM_BOT_TOKEN='YOUR_TOKEN'
export ORCH_MODEL=test
pydanticai-orchestrator-telegram
```

Then message the bot with:
- `/start`
- `/doctor`
- `/hermes analyze auth module`
- `/pi review build assumptions`
- `/stokowski_status`
- `/stokowski_dryrun`
- `/route compare hermes and pi on this repo`
- any plain text message

## Real backend wiring later
Codex:
```bash
# uses: codex mcp-server via mcporter
```

Pi:
```bash
export ORCH_PI_MODE=real
# uses: node ~/.pi/agent/git/github.com/WeiYiAcc/pi-mcp-adapter/pi-mcp-serve.js via mcporter
```

Hermes:
```bash
export ORCH_HERMES_MODE=real
# uses: node ~/.pi/agent/git/github.com/WeiYiAcc/pi-mcp-adapter/hermes-task-mcp-serve.js via mcporter
```

Stokowski:
```bash
export ORCH_STOKOWSKI_MODE=real
export ORCH_STOKOWSKI_WORKFLOW_PATH=/path/to/workflow.yaml
```
