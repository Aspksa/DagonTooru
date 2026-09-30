"""Core integration checks.

Дракончик Тоору
Автор: Матиенко Антон Александрович
E-mail: Aspksa@yandex.ru
"""

import hashlib
import json
import os
import shutil
import sqlite3
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from core.ai import Ollama
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
        root = Path(self.temp.name)
        migrations = root / "database" / "migrations"
        migrations.mkdir(parents=True)
        source_migrations = Path(__file__).resolve().parents[1] / "database" / "migrations"
        for source in source_migrations.glob("*.sql"):
            shutil.copy2(source, migrations / source.name)
        self.db = Storage(root)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(self.db, FakeAI(), 0))
        self.server.RequestHandlerClass = make_handler(
            self.db, FakeAI(), self.server.server_port
        )
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
        req = Request(
            f"http://127.0.0.1:{self.server.server_port}/api/v1/{path}",
            None if data is None else json.dumps(data).encode(),
            headers,
        )
        try:
            with urlopen(req) as response:
                return response.status, json.load(response)
        except HTTPError as exc:
            return exc.code, json.load(exc)

    def test_memory_isolation_through_api_and_ai_context(self):
        home = self.request("projects", {"name": "Дом", "scope": "home"})[1]["id"]
        work = "toori-network-drive"
        self.request("memory", {"text": "личный секрет", "scope": "personal"})
        self.request(
            "memory", {"text": "домашняя запись", "scope": "home", "project_id": home}
        )
        self.request(
            "memory", {"text": "рабочая запись", "scope": "work", "project_id": work}
        )
        code, result = self.request("memory?scope=work&project_id=" + work)
        self.assertEqual(code, 200)
        self.assertEqual([m["text"] for m in result["memories"]], ["рабочая запись"])
        code, result = self.request(
            "chat", {"message": "тест", "scope": "work", "project_id": work}
        )
        self.assertEqual(result["reply"], "рабочая запись")
        code, _ = self.request(
            "memory", {"text": "утечка", "scope": "work", "project_id": home}
        )
        self.assertEqual(code, 400)
        code, result = self.request("chat", {"message": "тест", "scope": "personal"})
        self.assertEqual(result["reply"], "личный секрет")

    def test_cross_origin_write_rejected(self):
        code, _ = self.request(
            "memory", {"text": "чужое", "scope": "personal"}, origin=False
        )
        self.assertEqual(code, 403)
        self.assertEqual(self.request("memory?scope=personal")[1]["memories"], [])

    def test_database_integrity_initial_projects_and_schema_version(self):
        status = self.request("system/status")[1]
        self.assertEqual(status["database"], "ok")
        self.assertEqual(status["schema_version"], 1)
        self.assertEqual(len(self.request("projects?scope=work")[1]["projects"]), 2)

    def test_migration_from_existing_version_zero_preserves_data(self):
        root = Path(self.temp.name) / "legacy"
        migrations = root / "database" / "migrations"
        migrations.mkdir(parents=True)
        source_migrations = Path(__file__).resolve().parents[1] / "database" / "migrations"
        for source in source_migrations.glob("*.sql"):
            shutil.copy2(source, migrations / source.name)
        db_path = root / "database" / "tooru.db"
        with sqlite3.connect(db_path) as con:
            con.executescript(
                """
                CREATE TABLE projects (
                    id TEXT PRIMARY KEY, name TEXT NOT NULL, scope TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE memories (
                    id TEXT PRIMARY KEY, text TEXT NOT NULL, scope TEXT NOT NULL,
                    project_id TEXT, source TEXT NOT NULL DEFAULT 'user',
                    status TEXT NOT NULL DEFAULT 'VERIFIED', created_at TEXT NOT NULL
                );
                INSERT INTO memories(id,text,scope,project_id,created_at)
                VALUES ('legacy','сохранить','personal',NULL,'2026-09-30T00:00:00+00:00');
                """
            )
        migrated = Storage(root)
        self.assertEqual(migrated.schema_version(), 1)
        self.assertEqual(migrated.memories("personal")[0]["text"], "сохранить")

    def test_backup_contains_live_memory_and_passes_integrity(self):
        self.request("memory", {"text": "важное", "scope": "personal"})
        code, result = self.request("backups", {})
        self.assertEqual(code, 201)
        backup = Path(self.temp.name) / result["file"]
        self.assertTrue(backup.is_file())
        self.assertTrue(Path(str(backup) + ".sha256").is_file())
        self.assertEqual(hashlib.sha256(backup.read_bytes()).hexdigest(), result["sha256"])
        self.assertEqual(result["schema_version"], 1)
        with sqlite3.connect(backup) as con:
            self.assertEqual(con.execute("PRAGMA integrity_check").fetchone()[0], "ok")
            self.assertEqual(con.execute("SELECT text FROM memories").fetchone()[0], "важное")
        self.request("memory", {"text": "после копии", "scope": "personal"})
        with sqlite3.connect(backup) as con:
            self.assertEqual(con.execute("SELECT COUNT(*) FROM memories").fetchone()[0], 1)

    def test_restore_backup_reverts_database_and_creates_safety_backup(self):
        self.request("memory", {"text": "до копии", "scope": "personal"})
        backup = self.request("backups", {})[1]
        self.request("memory", {"text": "после копии", "scope": "personal"})
        code, restored = self.request(
            "backups/restore", {"file": backup["file"], "sha256": backup["sha256"]}
        )
        self.assertEqual(code, 200)
        self.assertTrue((Path(self.temp.name) / restored["safety_backup"]).is_file())
        memories = self.request("memory?scope=personal")[1]["memories"]
        self.assertEqual([m["text"] for m in memories], ["до копии"])
        self.assertEqual(restored["schema_version"], 1)

    def test_restore_rejects_wrong_checksum_without_touching_live_data(self):
        self.request("memory", {"text": "до копии", "scope": "personal"})
        backup = self.request("backups", {})[1]
        self.request("memory", {"text": "живые данные", "scope": "personal"})
        code, _ = self.request(
            "backups/restore", {"file": backup["file"], "sha256": "0" * 64}
        )
        self.assertEqual(code, 503)
        memories = self.request("memory?scope=personal")[1]["memories"]
        self.assertEqual([m["text"] for m in memories], ["живые данные", "до копии"])


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
            with patch.dict(
                os.environ,
                {"TOORU_OLLAMA_URL": f"http://127.0.0.1:{server.server_port}"},
                clear=False,
            ):
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
