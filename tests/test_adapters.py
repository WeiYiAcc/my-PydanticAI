import unittest

from pydanticai_orchestrator.adapters.codex_mcp import CodexMcpAdapter
from pydanticai_orchestrator.adapters.hermes import HermesAdapter
from pydanticai_orchestrator.adapters.pi import PiAdapter
from pydanticai_orchestrator.adapters.stokowski import StokowskiAdapter


class AdapterTests(unittest.TestCase):
    def test_mock_codex(self):
        adapter = CodexMcpAdapter(mode='mock', timeout_seconds=10, command_template='npx mcporter call codex prompt={prompt} sandbox="workspace-write" approval-policy="never" cwd="/home/weiyiacc/projects/pydanticai-orchestrator" --stdio "codex mcp-server" --name codex-mcp --output json')
        result = adapter.run_task('hello')
        self.assertTrue(result.ok)
        self.assertEqual(result.worker, 'codex')
        self.assertEqual(result.mode, 'mock')

    def test_mock_hermes(self):
        adapter = HermesAdapter(mode='mock', timeout_seconds=10, command_template='npx mcporter call run_task prompt={prompt} --stdio "node /home/weiyiacc/.pi/agent/git/github.com/WeiYiAcc/pi-mcp-adapter/hermes-task-mcp-serve.js" --name hermes-task --output json')
        result = adapter.run_task('hello')
        self.assertTrue(result.ok)
        self.assertEqual(result.worker, 'hermes')
        self.assertEqual(result.mode, 'mock')

    def test_mock_pi(self):
        adapter = PiAdapter(mode='mock', timeout_seconds=10, command_template='npx mcporter call run_prompt prompt={prompt} --stdio "node /home/weiyiacc/.pi/agent/git/github.com/WeiYiAcc/pi-mcp-adapter/pi-mcp-serve.js" --name pi-agent --output json')
        result = adapter.run_task('hello')
        self.assertTrue(result.ok)
        self.assertEqual(result.worker, 'pi')
        self.assertEqual(result.mode, 'mock')

    def test_mock_stokowski(self):
        adapter = StokowskiAdapter(mode='mock', timeout_seconds=10, binary='stokowski', workflow_path='', submit_template='stokowski {workflow} --dry-run')
        result = adapter.dry_run()
        self.assertTrue(result.ok)
        self.assertEqual(result.action, 'dry_run')
        self.assertEqual(result.mode, 'mock')
