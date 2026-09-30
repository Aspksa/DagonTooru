"""Crash Recovery lifecycle checks.

Дракончик Тоору
Автор: Матиенко Антон Александрович
E-mail: Aspksa@yandex.ru
"""

import json
import os
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.request import urlopen

from core.instance import SERVICE_ID
from core.recovery import RecoveryState
from core.server import main, make_handler


class FakeStorage:
    def health(self):
        return {"database": "ok", "schema_version": 1}


class FakeAI:
    def health(self):
        return {"status": "offline", "models": [], "selected": ""}


def instance(instance_id="test-instance"):
    return {
        "service": SERVICE_ID,
        "instance_id": instance_id,
        "pid": 12345,
        "port": 8765,
        "started_at": "2026-09-30T00:00:00+00:00",
    }


class RecoveryTests(unittest.TestCase):
    def test_first_start_running_and_clean_shutdown(self):
        with tempfile.TemporaryDirectory() as directory:
            recovery = RecoveryState(Path(directory))
            started = recovery.start(instance())
            self.assertEqual(started["state"], "starting")
            self.assertFalse(started["clean_shutdown"])
            self.assertEqual(started["previous_shutdown"], "first_start")
            self.assertFalse(started["previous_crash"])
            self.assertFalse(started["recovery_needed"])
            self.assertEqual(started["recovery_status"], "not_needed")

            running = recovery.mark_running()
            self.assertEqual(running["state"], "running")
            self.assertFalse(running["clean_shutdown"])

            stopped = recovery.mark_clean_shutdown("test")
            self.assertEqual(stopped["state"], "stopped")
            self.assertTrue(stopped["clean_shutdown"])
            self.assertEqual(stopped["shutdown_reason"], "test")
            self.assertFalse(recovery.temporary.exists())

    def test_next_start_recognizes_previous_clean_shutdown(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = RecoveryState(root)
            first.start(instance("first"))
            first.mark_running()
            first.mark_clean_shutdown()

            second = RecoveryState(root)
            current = second.start(instance("second"))
            self.assertEqual(current["previous_shutdown"], "clean")
            self.assertFalse(current["previous_crash"])
            self.assertFalse(current["recovery_needed"])
            self.assertEqual(current["previous"]["instance_id"], "first")
            self.assertTrue(current["previous"]["clean_shutdown"])

    def test_unclean_previous_session_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = RecoveryState(root)
            first.start(instance("crashed"))
            first.mark_running()

            second = RecoveryState(root)
            current = second.start(instance("next"))
            self.assertEqual(current["previous_shutdown"], "unclean")
            self.assertTrue(current["previous_crash"])
            self.assertTrue(current["recovery_needed"])
            self.assertEqual(current["recovery_status"], "pending")
            self.assertEqual(current["recovery_count"], 1)
            self.assertEqual(current["previous"]["state"], "running")
            self.assertFalse(current["previous"]["clean_shutdown"])

    def test_database_recovery_check_success_resolves_warning(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = RecoveryState(root)
            first.start(instance("crashed"))
            first.mark_running()
            second = RecoveryState(root)
            second.start(instance("next"))
            checked = second.record_recovery("ok")
            self.assertEqual(checked["recovery_status"], "ok")
            self.assertEqual(checked["recovery_database"], "ok")
            self.assertFalse(checked["recovery_needed"])
            self.assertTrue(checked["recovery_checked_at"])

    def test_database_recovery_check_error_remains_pending_for_attention(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = RecoveryState(root)
            first.start(instance("crashed"))
            first.mark_running()
            second = RecoveryState(root)
            second.start(instance("next"))
            checked = second.record_recovery("error")
            self.assertEqual(checked["recovery_status"], "error")
            self.assertEqual(checked["recovery_database"], "error")
            self.assertTrue(checked["recovery_needed"])

    def test_unresolved_recovery_survives_handled_startup_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            crashed = RecoveryState(root)
            crashed.start(instance("crashed"))
            crashed.mark_running()

            failed_start = RecoveryState(root)
            detected = failed_start.start(instance("port-failure"))
            self.assertTrue(detected["recovery_needed"])
            failed_start.mark_clean_shutdown(
                "port_unavailable", resolve_recovery=False
            )

            next_start = RecoveryState(root)
            current = next_start.start(instance("next"))
            self.assertEqual(current["previous_shutdown"], "clean")
            self.assertFalse(current["previous_crash"])
            self.assertTrue(current["recovery_needed"])

    def test_status_api_reports_recovery_warning_after_unclean_session(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = RecoveryState(root)
            first.start(instance("crashed"))
            first.mark_running()
            current = RecoveryState(root)
            current.start(instance("next"))

            server = ThreadingHTTPServer(
                ("127.0.0.1", 0),
                make_handler(FakeStorage(), FakeAI(), 0),
            )
            server.RequestHandlerClass = make_handler(
                FakeStorage(),
                FakeAI(),
                server.server_port,
                instance("next"),
                current,
            )
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            try:
                with urlopen(
                    f"http://127.0.0.1:{server.server_port}/api/v1/system/status"
                ) as response:
                    status = json.load(response)
                self.assertEqual(status["crash_recovery"], "warning")
                self.assertTrue(status["recovery"]["previous_crash"])
                self.assertTrue(status["recovery"]["recovery_needed"])
            finally:
                server.shutdown()
                server.server_close()

    def test_invalid_previous_state_warns_without_blocking_start(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            state_dir = root / "runtime_state"
            state_dir.mkdir(parents=True)
            (state_dir / "state.json").write_text("{broken", encoding="utf-8")

            recovery = RecoveryState(root)
            current = recovery.start(instance())
            self.assertEqual(current["previous_shutdown"], "unknown")
            self.assertFalse(current["previous_crash"])
            self.assertTrue(current["recovery_needed"])
            self.assertEqual(current["previous_state_error"], "invalid_state_file")
            persisted = json.loads(recovery.path.read_text(encoding="utf-8"))
            self.assertEqual(persisted["state"], "starting")

    def test_unhandled_startup_error_does_not_write_clean_shutdown(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch("core.server.ROOT", root), patch(
                "core.server.Storage", side_effect=RuntimeError("startup boom")
            ), patch.dict(os.environ, {"TOORU_PORT": "18765"}, clear=False):
                with self.assertRaisesRegex(RuntimeError, "startup boom"):
                    main([])
            persisted = json.loads(
                (root / "runtime_state" / "state.json").read_text(encoding="utf-8")
            )
            self.assertFalse(persisted["clean_shutdown"])
            self.assertEqual(persisted["state"], "starting")

    def test_handled_port_conflict_writes_clean_shutdown(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch("core.server.ROOT", root), patch(
                "core.server.Storage", return_value=FakeStorage()
            ), patch("core.server.Ollama", return_value=FakeAI()), patch(
                "core.server.ThreadingHTTPServer", side_effect=OSError("busy")
            ), patch.dict(os.environ, {"TOORU_PORT": "18766"}, clear=False):
                self.assertEqual(main([]), 3)
            persisted = json.loads(
                (root / "runtime_state" / "state.json").read_text(encoding="utf-8")
            )
            self.assertTrue(persisted["clean_shutdown"])
            self.assertEqual(persisted["shutdown_reason"], "port_unavailable")


if __name__ == "__main__":
    unittest.main()
