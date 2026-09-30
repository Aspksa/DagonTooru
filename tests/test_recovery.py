"""Crash recovery state checks.

Дракончик Тоору
Автор: Матиенко Антон Александрович
E-mail: Aspksa@yandex.ru
"""

import json
import tempfile
import unittest
from pathlib import Path

from core.recovery import RuntimeState


def instance(pid=100, port=8765, instance_id="test-instance"):
    return {"pid": pid, "port": port, "instance_id": instance_id}


class RecoveryTests(unittest.TestCase):
    def test_clean_lifecycle_marks_shutdown(self):
        with tempfile.TemporaryDirectory() as directory:
            state = RuntimeState(Path(directory))
            current = state.begin(instance())
            self.assertFalse(current["previous_unclean_shutdown"])
            self.assertFalse(current["clean_shutdown"])
            final = state.finish()
            self.assertTrue(final["clean_shutdown"])
            self.assertEqual(final["state"], "stopped")
            persisted = json.loads(state.path.read_text(encoding="utf-8"))
            self.assertTrue(persisted["clean_shutdown"])

    def test_unclean_previous_run_is_detected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = RuntimeState(root)
            first.begin(instance(pid=101, instance_id="first"))
            second = RuntimeState(root)
            current = second.begin(instance(pid=102, instance_id="second"))
            self.assertTrue(current["previous_unclean_shutdown"])
            self.assertEqual(current["recovery_count"], 1)
            self.assertEqual(current["recovery_status"], "pending")
            second.record_recovery("ok")
            self.assertEqual(second.snapshot()["recovery_status"], "ok")
            second.finish("normal")

    def test_corrupt_state_is_replaced_and_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "runtime_state" / "state.json"
            path.parent.mkdir(parents=True)
            path.write_text("{not-json", encoding="utf-8")
            state = RuntimeState(root)
            current = state.begin(instance())
            self.assertTrue(current["previous_unclean_shutdown"])
            self.assertEqual(current["previous_state_issue"], "corrupt")
            self.assertEqual(current["recovery_count"], 1)
            self.assertFalse(state.temporary.exists())
            state.finish()

    def test_recovery_error_is_persisted(self):
        with tempfile.TemporaryDirectory() as directory:
            state = RuntimeState(Path(directory))
            state.begin(instance())
            current = state.record_recovery("error")
            self.assertEqual(current["recovery_status"], "error")
            self.assertEqual(current["recovery_database"], "error")
            state.finish("recovery_failed")


if __name__ == "__main__":
    unittest.main()
