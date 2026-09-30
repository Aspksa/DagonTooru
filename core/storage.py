"""SQLite storage with explicit memory scope policy.

Автор: Матиенко Антон Александрович
E-mail: Aspksa@yandex.ru
"""

import sqlite3
import uuid
import hashlib
import os
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

SCOPES = {"personal", "home", "work"}


def now():
    return datetime.now(timezone.utc).isoformat()


class Storage:
    def __init__(self, root: Path):
        self.root = root
        self.path = root / "database" / "tooru.db"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self):
        con = sqlite3.connect(self.path, timeout=10)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON")
        return con

    def initialize(self):
        with self.connect() as con:
            con.executescript("""
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY, name TEXT NOT NULL, scope TEXT NOT NULL
                        CHECK(scope IN ('home','work')), created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS memories (
                    id TEXT PRIMARY KEY, text TEXT NOT NULL, scope TEXT NOT NULL
                        CHECK(scope IN ('personal','home','work')),
                    project_id TEXT REFERENCES projects(id),
                    source TEXT NOT NULL DEFAULT 'user',
                    status TEXT NOT NULL DEFAULT 'VERIFIED',
                    created_at TEXT NOT NULL,
                    CHECK ((scope = 'personal' AND project_id IS NULL) OR scope != 'personal')
                );
                CREATE INDEX IF NOT EXISTS memories_scope_project
                    ON memories(scope, project_id, created_at);
            """)
            for pid, name in (
                ("toori-network-drive", "Сетевой диск Тоори"),
                ("dragon-torri", "Детский король / Дракончик Торри"),
            ):
                con.execute("INSERT OR IGNORE INTO projects VALUES (?, ?, 'work', ?)",
                            (pid, name, now()))

    def projects(self, scope):
        if scope not in {"home", "work"}:
            raise ValueError("Недопустимая область проекта")
        with self.connect() as con:
            return [dict(row) for row in con.execute(
                "SELECT id, name, scope FROM projects WHERE scope=? ORDER BY name", (scope,))]

    def add_project(self, name, scope):
        name = name.strip()
        if scope not in {"home", "work"} or not 1 <= len(name) <= 120:
            raise ValueError("Укажите название до 120 символов и область home/work")
        pid = str(uuid.uuid4())
        with self.connect() as con:
            con.execute("INSERT INTO projects VALUES (?, ?, ?, ?)", (pid, name, scope, now()))
        return {"id": pid, "name": name, "scope": scope}

    def validate_context(self, scope, project_id):
        if scope not in SCOPES:
            raise ValueError("Недопустимая область памяти")
        if scope == "personal" and project_id is not None:
            raise ValueError("Личная память не принадлежит проекту")
        if scope != "personal" and project_id is not None:
            with self.connect() as con:
                project = con.execute("SELECT scope FROM projects WHERE id=?", (project_id,)).fetchone()
            if project is None or project["scope"] != scope:
                raise ValueError("Проект не принадлежит выбранной области")

    def memories(self, scope, project_id=None):
        self.validate_context(scope, project_id)
        with self.connect() as con:
            if project_id is None:
                rows = con.execute("SELECT id, text, scope, project_id, created_at FROM memories "
                                   "WHERE scope=? AND project_id IS NULL ORDER BY created_at DESC LIMIT 100", (scope,))
            else:
                rows = con.execute("SELECT id, text, scope, project_id, created_at FROM memories "
                                   "WHERE scope=? AND project_id=? ORDER BY created_at DESC LIMIT 100",
                                   (scope, project_id))
            return [dict(row) for row in rows]

    def add_memory(self, text, scope, project_id=None):
        self.validate_context(scope, project_id)
        text = text.strip()
        if not 1 <= len(text) <= 4000:
            raise ValueError("Запись должна содержать от 1 до 4000 символов")
        item = {"id": str(uuid.uuid4()), "text": text, "scope": scope,
                "project_id": project_id, "created_at": now()}
        with self.connect() as con:
            con.execute("INSERT INTO memories(id,text,scope,project_id,created_at) VALUES (?,?,?,?,?)",
                        (item["id"], text, scope, project_id, item["created_at"]))
        return item

    def health(self):
        with self.connect() as con:
            integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
            version = con.execute("PRAGMA user_version").fetchone()[0]
        return {"database": "ok" if integrity == "ok" else "error", "schema_version": version}

    def backup(self):
        """Create a consistent snapshot while the core is running."""
        directory = self.root / "backups"
        directory.mkdir(parents=True, exist_ok=True)
        name = "tooru-" + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S") + "-" + uuid.uuid4().hex[:8] + ".db"
        target = directory / name
        temporary = directory / (name + ".tmp")
        checksum_tmp = directory / (name + ".sha256.tmp")
        try:
            with closing(self.connect()) as source, closing(sqlite3.connect(temporary)) as destination:
                source.backup(destination)
                integrity = destination.execute("PRAGMA integrity_check").fetchone()[0]
                if integrity != "ok":
                    raise RuntimeError("Проверка резервной копии не прошла")
            digest = hashlib.sha256()
            with temporary.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                    digest.update(chunk)
            checksum_tmp.write_text(digest.hexdigest() + "  " + name + "\n", encoding="ascii")
            os.replace(temporary, target)
            os.replace(checksum_tmp, directory / (name + ".sha256"))
            return {"file": "backups/" + name, "sha256": digest.hexdigest(), "bytes": target.stat().st_size}
        except (sqlite3.Error, OSError) as exc:
            target.unlink(missing_ok=True)
            raise RuntimeError("Не удалось создать копию базы. Проверьте свободное место и доступ к диску") from exc
        finally:
            temporary.unlink(missing_ok=True)
            checksum_tmp.unlink(missing_ok=True)
