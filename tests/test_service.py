import unittest

from pydanticai_orchestrator.service import OrchestratorService
from pydanticai_orchestrator.settings import AppSettings


class ServiceTests(unittest.TestCase):
    def test_doctor(self):
        service = OrchestratorService(AppSettings())
        info = service.doctor()
        self.assertEqual(info['model'], 'test')
        self.assertEqual(info['hermes_mode'], 'mock')
        self.assertEqual(info['max_parallel_workers'], 2)

    def test_direct_worker_calls(self):
        service = OrchestratorService(AppSettings())
        self.assertIn('MOCK Hermes', service.hermes('analyze').summary)
        self.assertIn('MOCK Pi', service.pi('review').summary)
        self.assertIn('MOCK Stokowski', service.stokowski_dry_run().summary)

    def test_route_request(self):
        service = OrchestratorService(AppSettings())
        self.assertEqual(service.route_request('please use pi to inspect repo').target, 'pi')
        self.assertEqual(service.route_request('run workflow dry-run').target, 'stokowski_dry_run')
        self.assertEqual(service.route_request('compare hermes and pi').target, 'multi_worker')

    def test_handle_request_multi_worker(self):
        service = OrchestratorService(AppSettings())
        result = service.handle_request('compare hermes and pi for this task')
        self.assertEqual(result.route.target, 'multi_worker')
        self.assertEqual(len(result.worker_results), 2)
        self.assertIsNotNone(result.review)

    def test_agent_smoke(self):
        service = OrchestratorService(AppSettings())
        result = service.run_prompt_sync('hello')
        self.assertTrue(result.answer)
