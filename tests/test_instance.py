"""Single-instance integration checks.

Дракончик Тоору
Автор: Матиенко Антон Александрович
E-mail: Aspksa@yandex.ru
"""

import json
import os
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from core.instance import InstanceAlreadyRunning, InstanceLock, SERVICE_ID
from core.server import make_handler, probe


class InstanceTests(unittest.TestCase):
    def test_second_lock_is_rejected_and_lock_can_be_reused(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            first = InstanceLock(root, 8765).acquire()
            try:
                with self.assertRaises(InstanceAlreadyRunning):
                    InstanceLock(root, 8765).acquire()
            finally:
                first.release()

            second = InstanceLock(root, 8765).acquire()
            second.release()

    def test_lock_metadata_records_running_and_stopped_states(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            lock = InstanceLock(root, 8765)
            with lock:
                metadata = json.loads(lock.path.read_text(encoding="utf-8"))
                self.assertEqual(metadata["service"], SERVICE_ID)
                self.assertEqual(metadata["state"], "running")
                self.assertEqual(metadata["pid"], os.getpid())
                self.assertEqual(metadata["port"], 8765)
                self.assertTrue(metadata["instance_id"])
            metadata = json.loads(lock.path.read_text(encoding="utf-8"))
            self.assertEqual(metadata["state"], "stopped")
            self.assertTrue(metadata["stopped_at"])

    def test_probe_accepts_tooru_identity(self):
        server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(None, None, 0))
        server.RequestHandlerClass = make_handler(None, None, server.server_port)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            self.assertTrue(probe(server.server_port))
        finally:
            server.shutdown()
            server.server_close()

    def test_probe_rejects_foreign_service(self):
        class ForeignHandler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                body = json.dumps(
                    {
                        "service": "not-tooru",
                        "protocol": 1,
                        "port": self.server.server_port,
                    }
                ).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        server = ThreadingHTTPServer(("127.0.0.1", 0), ForeignHandler)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            self.assertFalse(probe(server.server_port))
        finally:
            server.shutdown()
            server.server_close()


if __name__ == "__main__":
    unittest.main()
