"""Core integration checks. Автор: Матиенко Антон Александрович · Aspksa@yandex.ru"""

import json
import os
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from core.server import make_handler
from core.storage import Storage
from core.ai import Ollama


class FakeAI:
    def health(self):
        return {"status": "offline", "models": [], "selected": ""}

    def chat(self, message, context):
        return " | ".join(context)


class CoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Storage(Path(self.temp.name))
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(self.db, FakeAI(), 0))
        # Handler validates the actual ephemeral port.
        self.server.RequestHandlerClass = make_handler(self.db, FakeAI(), self.server.server_port)
        self.worker = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.worker.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(self.server.shutdown)

    def request(self, path, data=None, origin=True):
        headers = {}
        if data is not None:
            headers["Content-Type"] = "application/json"
            if origin:
                headers["Origin"] = f"http://127.0.0.1:{self.server.server_port}"
        req = Request(f"http://127.0.0.1:{self.server.server_port}/api/v1/{path}",
                      None if data is None else json.dumps(data).encode(), headers)
        try:
            with urlopen(req) as response:
                return response.status, json.load(response)
        except HTTPError as exc:
            return exc.code, json.load(exc)

    def test_memory_isolation_through_api_and_ai_context(self):
        home = self.request("projects", {"name": "Дом", "scope": "home"})[1]["id"]
        work = "toori-network-drive"
        self.request("memory", {"text": "личный секрет", "scope": "personal"})
        self.request("memory", {"text": "домашняя запись", "scope": "home", "project_id": home})
        self.request("memory", {"text": "рабочая запись", "scope": "work", "project_id": work})
        code, result = self.request("memory?scope=work&project_id=" + work)
        self.assertEqual(code, 200)
        self.assertEqual([m["text"] for m in result["memories"]], ["рабочая запись"])
        code, result = self.request("chat", {"message": "тест", "scope": "work", "project_id": work})
        self.assertEqual(result["reply"], "рабочая запись")
        code, _ = self.request("memory", {"text": "утечка", "scope": "work", "project_id": home})
        self.assertEqual(code, 400)
        code, result = self.request("chat", {"message": "тест", "scope": "personal"})
        self.assertEqual(result["reply"], "личный секрет")

    def test_cross_origin_write_rejected(self):
        code, _ = self.request("memory", {"text": "чужое", "scope": "personal"}, origin=False)
        self.assertEqual(code, 403)
        self.assertEqual(self.request("memory?scope=personal")[1]["memories"], [])

    def test_database_integrity_and_initial_projects(self):
        self.assertEqual(self.request("system/status")[1]["database"], "ok")
        self.assertEqual(len(self.request("projects?scope=work")[1]["projects"]), 2)


class OllamaTests(unittest.TestCase):
    def test_installed_model_is_selected_and_chat_uses_it(self):
        captured = []

        class Stub(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_GET(self):
                self.assert_path("/api/tags")
                self.answer({"models": [{"name": "tooru-local:4b"}]})

            def do_POST(self):
                self.assert_path("/api/chat")
                captured.append(json.loads(self.rfile.read(int(self.headers["Content-Length"]))))
                self.answer({"message": {"content": "Привет, я Тоору"}})

            def assert_path(self, expected):
                if self.path != expected:
                    raise AssertionError(self.path)

            def answer(self, result):
                body = json.dumps(result).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        server = ThreadingHTTPServer(("127.0.0.1", 0), Stub)
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        try:
            with patch.dict(os.environ, {"TOORU_OLLAMA_URL": f"http://127.0.0.1:{server.server_port}"}, clear=False):
                ai = Ollama()
                self.assertEqual(ai.health()["status"], "ok")
                self.assertEqual(ai.chat("Привет", ["личная запись"]), "Привет, я Тоору")
            self.assertEqual(captured[0]["model"], "tooru-local:4b")
            self.assertEqual(captured[0]["options"]["num_predict"], 256)
            self.assertIs(captured[0]["think"], False)
            self.assertIn("личная запись", captured[0]["messages"][0]["content"])
        finally:
            server.shutdown()
            server.server_close()

    def test_remote_ai_address_is_rejected(self):
        with patch.dict(os.environ, {"TOORU_OLLAMA_URL": "http://example.com:11435"}):
            with self.assertRaises(ValueError):
                Ollama()

    def test_timeout_reports_actual_cause(self):
        with patch("core.ai.urlopen", side_effect=TimeoutError("timed out")):
            with self.assertRaisesRegex(RuntimeError, "не ответила вовремя"):
                Ollama().chat("Привет", [])


if __name__ == "__main__":
    unittest.main()
