#!/usr/bin/env node

import { spawn } from 'node:child_process';
import process from 'node:process';
import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';

function wrapEnvelope(answer, sessionId, stdout, stderr) {
  return {
    return_value: {
      ok: true,
      answer,
      session_id: sessionId,
    },
    content: answer || '(empty answer)',
    metadata: {
      stdout,
      stderr,
      raw_payload: {
        session_id: sessionId,
      },
    },
  };
}

function runHermes({ prompt, cwd, model }) {
  return new Promise((resolve, reject) => {
    const hermesBin = process.env.HERMES_BIN || 'hermes';
    const args = ['chat', '-q', prompt, '--quiet'];
    if (model) {
      args.push('--model', model);
    }
    const child = spawn(hermesBin, args, {
      cwd: cwd || process.cwd(),
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
      const combined = `${stderr}\n${stdout}`;
      const lines = combined.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
      let sessionId = null;
      let answer = '';
      for (const line of lines) {
        if (line.startsWith('session_id:')) {
          sessionId = line.slice('session_id:'.length).trim();
          continue;
        }
        answer = line;
      }
      if (code !== 0) {
        reject(new Error(`hermes exited with code ${code}\n${combined}`));
        return;
      }
      resolve(wrapEnvelope(answer, sessionId, stdout.trim(), stderr.trim()));
    });
  });
}

const server = new McpServer({
  name: 'hermes-task',
  version: '0.1.0',
});

server.registerTool(
  'doctor',
  {
    description: 'Report basic Hermes task bridge configuration and executable resolution.',
    inputSchema: {
      hermesBin: z.string().optional().describe('Optional override path for the hermes executable'),
    },
  },
  async ({ hermesBin }) => ({
    content: [{ type: 'text', text: `hermes task bridge ready (${hermesBin || process.env.HERMES_BIN || 'hermes'})` }],
    structuredContent: {
      return_value: {
        ok: true,
        answer: `hermes task bridge ready (${hermesBin || process.env.HERMES_BIN || 'hermes'})`,
      },
      content: `hermes task bridge ready (${hermesBin || process.env.HERMES_BIN || 'hermes'})`,
      metadata: {
        stdout: '',
        stderr: '',
        raw_payload: {
          hermesBin: hermesBin || process.env.HERMES_BIN || 'hermes',
          cwd: process.cwd(),
        },
      },
    },
  }),
);

server.registerTool(
  'run_task',
  {
    description: 'Run a one-shot Hermes task via hermes chat -q --quiet and return structured final output.',
    inputSchema: {
      prompt: z.string().describe('Prompt to send to Hermes'),
      cwd: z.string().optional().describe('Working directory override'),
      model: z.string().optional().describe('Optional Hermes model override'),
    },
  },
  async ({ prompt, cwd, model }) => ({
    content: [{ type: 'text', text: 'Hermes task completed' }],
    structuredContent: await runHermes({ prompt, cwd, model }),
  }),
);

const transport = new StdioServerTransport();
await server.connect(transport);
