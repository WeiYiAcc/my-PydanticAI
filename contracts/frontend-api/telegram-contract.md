# Telegram frontend contract

Current bot intent:
- expose orchestration actions through message commands
- return normalized orchestration results in chat-safe text form

## Refactor rule

Telegram should remain a frontend only. It should not own orchestration semantics.
