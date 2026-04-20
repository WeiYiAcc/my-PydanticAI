# MCP worker shape

## Goal
Converge worker backends toward a generic MCP worker form.

## Desired traits

- one-shot task invocation
- stable machine-readable output
- summary/content/metadata separation
- no spinner/banner pollution in the result payload
- explicit tool names and argument schema

## Current reference points

- Codex MCP worker is the cleanest baseline
- Pi uses a custom MCP bridge and should converge toward the same shape
- Hermes uses a custom MCP task bridge and should converge toward the same shape
