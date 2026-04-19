#!/usr/bin/env node

import { spawn } from 'node:child_process';
import process from 'node:process';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';

function parseJsonLines(text) {
  const events = [];
  for (const rawLine of text.split(/\r?\n/)) {
    const line = rawLine.trim();
    if (!line) continue;
    try {
      events.push(JSON.parse(line));
    } catch {
      // ignore non-JSON lines
    }
  }
  return events;
}

function extractAssistantPayload(events) {
  let best = null;
  for (const event of events) {
    const msg = event?.message;
    if (msg?.role === 'assistant') {
      best = msg;
    }
  }
  if (!best) return null;

  const content = Array.isArray(best.content) ? best.content : [];
  const answer = content
    .filter((part) => part?.type === 'text' && typeof part?.text === 'string')
    .map((part) => part.text)
    .join('\n')
    .trim();

  return {
    answer,
    provider: best.provider ?? null,
    model: best.model ?? null,
    api: best.api ?? null,
    usage: best.usage ?? null,
    response_id: best.responseId ?? null,
    stop_reason: best.stopReason ?? null,
  };
}

function wrapEnvelope(result, stdout, stderr, eventCount) {
  return {
    return_value: {
      ok: true,
      answer: result.answer,
      provider: result.provider,
      model: result.model,
      api: result.api,
      usage: result.usage,
      response_id: result.response_id,
      stop_reason: result.stop_reason,
      event_count: eventCount,
    },
    content: result.answer || '(empty answer)',
    metadata: {
      stdout,
      stderr,
      raw_payload: {
        eventCount,
      },
    },
  };
}

function runPiPrompt({ prompt, provider, model, thinking, offline }) {
  return new Promise((resolve, reject) => {
    const piBin = process.env.PI_BIN || 'pi';
    const args = ['--mode', 'json', '--no-session'];
    if (offline) args.push('--offline');
    if (provider) args.push('--provider', provider);
    if (model) args.push('--model', model);
    if (thinking) args.push('--thinking', thinking);
    args.push('-p', prompt);

    const child = spawn(piBin, args, {
      stdio: ['ignore', 'pipe', 'pipe'],
      env: { ...process.env },
    });

    let stdout = '';
    let stderr = '';

    child.stdout.on('data', (chunk) => {
      stdout += chunk.toString();
    });
    child.stderr.on('data', (chunk) => {
      stderr += chunk.toString();
    });
    child.on('error', reject);
    child.on('close', (code) => {
      const events = parseJsonLines(stdout);
      const assistant = extractAssistantPayload(events);
      if (code !== 0) {
        reject(new Error(`pi exited with code ${code}\n${stderr || stdout}`));
        return;
      }
      if (!assistant) {
        reject(new Error(`Could not extract assistant payload from pi JSON output\n${stdout}`));
        return;
      }
      resolve(wrapEnvelope(assistant, stdout.trim(), stderr.trim(), events.length));
    });
  });
}

const server = new McpServer({
  name: 'pi-agent',
  version: '0.1.0',
});

server.registerTool(
  'doctor',
  {
    description: 'Report basic Pi MCP bridge configuration and executable resolution.',
    inputSchema: {
      piBin: z.string().optional().describe('Optional override path for the pi executable'),
    },
  },
  async ({ piBin }) => ({
    content: [{ type: 'text', text: `pi bridge ready (${piBin || process.env.PI_BIN || 'pi'})` }],
    structuredContent: {
      return_value: {
        ok: true,
        answer: `pi bridge ready (${piBin || process.env.PI_BIN || 'pi'})`,
      },
      content: `pi bridge ready (${piBin || process.env.PI_BIN || 'pi'})`,
      metadata: {
        stdout: '',
        stderr: '',
        raw_payload: {
          piBin: piBin || process.env.PI_BIN || 'pi',
          cwd: process.cwd(),
        },
      },
    },
  }),
);

server.registerTool(
  'run_prompt',
  {
    description: 'Run a one-shot Pi prompt via pi --mode json and return structured final output.',
    inputSchema: {
      prompt: z.string().describe('Prompt to send to Pi'),
      provider: z.string().optional().describe('Optional Pi provider override'),
      model: z.string().optional().describe('Optional Pi model override'),
      thinking: z.enum(['off', 'minimal', 'low', 'medium', 'high', 'xhigh']).optional().describe('Optional Pi thinking level override'),
      offline: z.boolean().optional().describe('Run Pi with --offline / PI_OFFLINE behavior'),
    },
  },
  async ({ prompt, provider, model, thinking, offline }) => ({
    content: [{ type: 'text', text: 'Pi task completed' }],
    structuredContent: await runPiPrompt({ prompt, provider, model, thinking, offline: offline ?? true }),
  }),
);

const transport = new StdioServerTransport();
await server.connect(transport);
