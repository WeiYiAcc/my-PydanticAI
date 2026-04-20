# CLI contract

Current CLI subcommands:

- `doctor`
- `worker <backend> <task>`
- `stokowski <action> [task]`
- `prompt <text>`
- `route <text>`

## Refactor rule

Even if the implementation moves out of a single `service.py`, these CLI shapes should remain stable unless explicitly versioned.
