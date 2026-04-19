import os
import unittest

from pydanticai_orchestrator.settings import AppSettings


class SettingsTests(unittest.TestCase):
    def test_defaults(self):
        settings = AppSettings()
        self.assertEqual(settings.orch_model, 'test')
        self.assertEqual(settings.orch_hermes_mode, 'mock')
        self.assertEqual(settings.orch_pi_mode, 'mock')
        self.assertEqual(settings.orch_stokowski_mode, 'mock')
