"""Core integration checks. Автор: Матиенко Антон Александрович · Aspksa@yandex.ru"""

import json
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from core.server import make_handler
from core.storage import Storage


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


if __name__ == "__main__":
    unittest.main()
