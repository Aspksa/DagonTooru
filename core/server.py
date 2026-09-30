"""Loopback-only HTTP API and web UI.

Автор: Матиенко Антон Александрович
E-mail: Aspksa@yandex.ru
"""

import json
import mimetypes
import os
import shutil
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from .ai import Ollama
from .storage import Storage

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "web" / "static"


def make_handler(storage, ai, port):
    class Handler(BaseHTTPRequestHandler):
        def send_json(self, data, status=200):
            body = json.dumps(data, ensure_ascii=False).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def trusted(self):
            host = self.headers.get("Host", "")
            return host in {f"127.0.0.1:{port}", f"localhost:{port}"}

        def do_GET(self):
            if not self.trusted():
                return self.send_json({"error": "Недопустимый Host"}, 403)
            url = urlsplit(self.path)
            query = parse_qs(url.query)
            try:
                if url.path == "/api/v1/system/status":
                    db = storage.health()
                    free = shutil.disk_usage(ROOT).free
                    return self.send_json({"core": "ok", **db, "storage": "ok" if free > 100_000_000 else "warning",
                                           "free_bytes": free, "ai": ai.health()})
                if url.path == "/api/v1/projects":
                    return self.send_json({"projects": storage.projects(query.get("scope", ["work"])[0])})
                if url.path == "/api/v1/memory":
                    return self.send_json({"memories": storage.memories(query.get("scope", ["personal"])[0],
                                                                         query.get("project_id", [None])[0])})
                if url.path == "/" or url.path.startswith("/static/"):
                    relative = "index.html" if url.path == "/" else url.path.removeprefix("/static/")
                    target = (STATIC / relative).resolve()
                    if not target.is_relative_to(STATIC) or not target.is_file():
                        return self.send_error(404)
                    body = target.read_bytes()
                    self.send_response(200)
                    self.send_header("Content-Type", mimetypes.guess_type(target)[0] or "application/octet-stream")
                    self.send_header("X-Content-Type-Options", "nosniff")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    return self.wfile.write(body)
                return self.send_json({"error": "Не найдено"}, 404)
            except ValueError as exc:
                return self.send_json({"error": str(exc)}, 400)

        def do_POST(self):
            if not self.trusted():
                return self.send_json({"error": "Недопустимый Host"}, 403)
            origin = self.headers.get("Origin")
            if origin not in {f"http://127.0.0.1:{port}", f"http://localhost:{port}"}:
                return self.send_json({"error": "Недопустимый Origin"}, 403)
            if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                return self.send_json({"error": "Требуется JSON"}, 415)
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 16000:
                    return self.send_json({"error": "Недопустимый размер"}, 413)
                data = json.loads(self.rfile.read(length))
                if not isinstance(data, dict):
                    raise ValueError("Ожидается объект JSON")
                if self.path == "/api/v1/projects":
                    return self.send_json(storage.add_project(data["name"], data["scope"]), 201)
                if self.path == "/api/v1/memory":
                    return self.send_json(storage.add_memory(data["text"], data["scope"],
                                                             data.get("project_id")), 201)
                if self.path == "/api/v1/chat":
                    message = data["message"].strip()
                    if not 1 <= len(message) <= 4000:
                        raise ValueError("Сообщение должно содержать от 1 до 4000 символов")
                    context = [m["text"] for m in storage.memories(data["scope"], data.get("project_id"))[:20]]
                    return self.send_json({"reply": ai.chat(message, context)})
                if self.path == "/api/v1/backups":
                    return self.send_json(storage.backup(), 201)
                return self.send_json({"error": "Не найдено"}, 404)
            except (KeyError, TypeError, ValueError, json.JSONDecodeError) as exc:
                return self.send_json({"error": "Неверные данные: " + str(exc)}, 400)
            except RuntimeError as exc:
                return self.send_json({"error": str(exc)}, 503)

    return Handler


def main():
    port = int(os.environ.get("TOORU_PORT", "8765"))
    if not 1024 <= port <= 65535:
        raise ValueError("TOORU_PORT должен быть в диапазоне 1024–65535")
    storage = Storage(ROOT)
    server = ThreadingHTTPServer(("127.0.0.1", port), make_handler(storage, Ollama(), port))
    print(f"Дракончик Тоору: http://127.0.0.1:{port}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
