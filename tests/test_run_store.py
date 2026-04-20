from __future__ import annotations

import json
import unittest
from tempfile import TemporaryDirectory

from pydanticai_orchestrator.schemas import (
    OrchestrationEvent,
    OrchestrationRunState,
    RouteDecision,
)
from pydanticai_orchestrator.service import OrchestratorService
from pydanticai_orchestrator.settings import AppSettings
from pydanticai_orchestrator.state_store import FileRunStore


class FileRunStoreTests(unittest.TestCase):
    def test_save_and_load_run_state_and_events(self):
        with TemporaryDirectory() as tmpdir:
            store = FileRunStore(tmpdir)
            state = OrchestrationRunState(
                run_id="run-test-1",
                prompt="implement a tiny function",
                status="running",
                current_node="routing",
                route=RouteDecision(target="hermes", task="implement a tiny function", rationale="test"),
            )

            store.save_state(state)
            store.append_event(
                "run-test-1",
                OrchestrationEvent(
                    seq=1,
                    event_type="route_decided",
                    node="routing",
                    payload={"target": "hermes"},
                ),
            )

            loaded = store.load_state("run-test-1")
            self.assertEqual(loaded.run_id, "run-test-1")
            self.assertEqual(loaded.current_node, "routing")
            self.assertEqual(loaded.route.target, "hermes")

            events = store.load_events("run-test-1")
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0].event_type, "route_decided")
            self.assertEqual(events[0].payload["target"], "hermes")

    def test_list_runs_and_latest_run_id(self):
        with TemporaryDirectory() as tmpdir:
            store = FileRunStore(tmpdir)
            first = OrchestrationRunState(run_id="run-a", prompt="first")
            second = OrchestrationRunState(run_id="run-b", prompt="second")
            store.save_state(first)
            store.save_state(second)

            self.assertEqual(store.latest_run_id(), "run-b")
            runs = store.list_runs()
            self.assertEqual([run.run_id for run in runs], ["run-b", "run-a"])


class ServicePersistenceTests(unittest.TestCase):
    def test_handle_request_persists_run_state_and_event_log(self):
        with TemporaryDirectory() as tmpdir:
            settings = AppSettings(orch_state_dir=tmpdir)
            service = OrchestratorService(settings)

            result = service.handle_request("implement a tiny python function that returns 42")

            self.assertTrue(result.run_id)
            run_dir = FileRunStore(tmpdir).run_dir(result.run_id)
            self.assertTrue((run_dir / "state.json").exists())
            self.assertTrue((run_dir / "events.jsonl").exists())

            state_doc = json.loads((run_dir / "state.json").read_text(encoding="utf-8"))
            self.assertEqual(state_doc["run_id"], result.run_id)
            self.assertEqual(state_doc["status"], "completed")
            self.assertEqual(state_doc["route"]["target"], "hermes")
            self.assertEqual(state_doc["answer"], result.answer)

            events = FileRunStore(tmpdir).load_events(result.run_id)
            event_types = [event.event_type for event in events]
            self.assertIn("run_started", event_types)
            self.assertIn("route_decided", event_types)
            self.assertIn("run_completed", event_types)

    def test_service_can_fetch_state_and_list_runs(self):
        with TemporaryDirectory() as tmpdir:
            settings = AppSettings(orch_state_dir=tmpdir)
            service = OrchestratorService(settings)
            first = service.handle_request("implement a tiny python function that returns 42")
            second = service.handle_request("compare hermes and pi for this task")

            fetched = service.get_run_state(first.run_id)
            self.assertEqual(fetched.run_id, first.run_id)
            self.assertEqual(fetched.status, "completed")

            latest = service.get_latest_run_state()
            self.assertIsNotNone(latest)
            self.assertEqual(latest.run_id, second.run_id)

            runs = service.list_runs()
            self.assertEqual([run.run_id for run in runs], [second.run_id, first.run_id])

            summaries = service.list_run_summaries()
            self.assertEqual([summary.run_id for summary in summaries], [second.run_id, first.run_id])
            self.assertEqual(summaries[0].status, 'completed')
            self.assertEqual(summaries[0].route_target, 'multi_worker')
            self.assertTrue(summaries[0].answer_preview)

    def test_continue_run_replays_waiting_run_to_completion(self):
        with TemporaryDirectory() as tmpdir:
            settings = AppSettings(orch_state_dir=tmpdir)
            service = OrchestratorService(settings)
            store = FileRunStore(tmpdir)

            state = OrchestrationRunState(
                run_id="run-waiting-1",
                prompt="implement a tiny python function that returns 42",
                status="waiting",
                current_node="routing",
                route=RouteDecision(target="hermes", task="implement a tiny python function that returns 42", rationale="test"),
                waiting_for="resume",
            )
            store.save_state(state)

            resumed = service.continue_run("run-waiting-1")

            self.assertEqual(resumed.run_id, "run-waiting-1")
            self.assertEqual(resumed.route.target, "hermes")
            persisted = service.get_run_state("run-waiting-1")
            self.assertEqual(persisted.status, "completed")
            self.assertEqual(persisted.current_node, "completed")
            event_types = [event.event_type for event in service.get_run_events("run-waiting-1")]
            self.assertIn("run_resumed", event_types)
            self.assertIn("run_completed", event_types)

    def test_continue_run_rejects_completed_run(self):
        with TemporaryDirectory() as tmpdir:
            settings = AppSettings(orch_state_dir=tmpdir)
            service = OrchestratorService(settings)
            result = service.handle_request("implement a tiny python function that returns 42")

            with self.assertRaisesRegex(ValueError, "already completed"):
                service.continue_run(result.run_id)

    def test_continue_run_rejects_missing_route_for_non_init_state(self):
        with TemporaryDirectory() as tmpdir:
            settings = AppSettings(orch_state_dir=tmpdir)
            service = OrchestratorService(settings)
            store = FileRunStore(tmpdir)
            store.save_state(
                OrchestrationRunState(
                    run_id="run-bad-1",
                    prompt="implement a tiny python function that returns 42",
                    status="waiting",
                    current_node="worker_execution",
                )
            )

            with self.assertRaisesRegex(ValueError, "missing route"):
                service.continue_run("run-bad-1")

    def test_continue_run_from_init_routes_and_completes(self):
        with TemporaryDirectory() as tmpdir:
            settings = AppSettings(orch_state_dir=tmpdir)
            service = OrchestratorService(settings)
            store = FileRunStore(tmpdir)
            store.save_state(
                OrchestrationRunState(
                    run_id="run-init-1",
                    prompt="implement a tiny python function that returns 42",
                    status="waiting",
                    current_node="init",
                    waiting_for="resume",
                )
            )

            resumed = service.continue_run("run-init-1")
            self.assertEqual(resumed.run_id, "run-init-1")
            self.assertEqual(resumed.route.target, "hermes")
            self.assertEqual(service.get_run_state("run-init-1").status, "completed")

    def test_mark_run_waiting_updates_state_and_event_log(self):
        with TemporaryDirectory() as tmpdir:
            settings = AppSettings(orch_state_dir=tmpdir)
            service = OrchestratorService(settings)
            result = service.handle_request("implement a tiny python function that returns 42")

            waiting = service.mark_run_waiting(result.run_id, reason="need approval")
            self.assertEqual(waiting.status, "waiting")
            self.assertEqual(waiting.current_node, "review")
            self.assertEqual(waiting.waiting_for, "need approval")

            events = service.get_run_events(result.run_id)
            event_types = [event.event_type for event in events]
            self.assertIn("run_waiting", event_types)

    def test_mark_run_waiting_rejects_unknown_run(self):
        with TemporaryDirectory() as tmpdir:
            settings = AppSettings(orch_state_dir=tmpdir)
            service = OrchestratorService(settings)

            with self.assertRaises(FileNotFoundError):
                service.mark_run_waiting("run-missing", reason="no run")

    def test_continue_run_after_mark_waiting_uses_existing_route(self):
        with TemporaryDirectory() as tmpdir:
            settings = AppSettings(orch_state_dir=tmpdir)
            service = OrchestratorService(settings)
            result = service.handle_request("compare hermes and pi for this task")
            waiting = service.mark_run_waiting(result.run_id, reason="manual review")
            self.assertEqual(waiting.status, "waiting")

            resumed = service.continue_run(result.run_id)
            self.assertEqual(resumed.run_id, result.run_id)
            self.assertEqual(resumed.route.target, "multi_worker")
            final_state = service.get_run_state(result.run_id)
            self.assertEqual(final_state.status, "completed")
            self.assertIsNotNone(final_state.review)
