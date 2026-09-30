"""SQLite storage with explicit memory scope policy and migrations.

Дракончик Тоору
Автор: Матиенко Антон Александрович
E-mail: Aspksa@yandex.ru
"""

import hashlib
import os
import sqlite3
import uuid
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path

SCOPES = {"personal", "home", "work"}
MIGRATIONS_DIR = Path("database") / "migrations"


def now():
    return datetime.now(timezone.utc).isoformat()


class Storage:
    def __init__(self, root: Path):
        self.root = root
        self.path = root / "database" / "tooru.db"
        self.migrations_path = root / MIGRATIONS_DIR
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self, path=None):
        con = sqlite3.connect(path or self.path, timeout=10)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON")
        return con

    def _migrations(self):
        if not self.migrations_path.is_dir():
            raise RuntimeError("Не найдена папка database/migrations")
        migrations = []
        seen = set()
        for path in sorted(self.migrations_path.glob("[0-9][0-9][0-9]_*.sql")):
            version = int(path.name[:3])
            if version in seen:
                raise RuntimeError(f"Повторяется версия миграции {version}")
            seen.add(version)
            migrations.append((version, path))
        expected = list(range(1, len(migrations) + 1))
        actual = [version for version, _ in migrations]
        if actual != expected:
            raise RuntimeError("Миграции SQLite должны идти непрерывно с версии 001")
        return migrations

    def initialize(self):
        migrations = self._migrations()
        latest = migrations[-1][0] if migrations else 0
        with self.connect() as con:
            current = con.execute("PRAGMA user_version").fetchone()[0]
            if current > latest:
                raise RuntimeError(
                    f"База имеет схему {current}, а это ядро поддерживает только до {latest}"
                )
            for version, path in migrations:
                if version <= current:
                    continue
                script = path.read_text(encoding="utf-8")
                try:
                    con.executescript(
                        "BEGIN IMMEDIATE;\n"
                        + script
                        + f"\nPRAGMA user_version = {version};\nCOMMIT;\n"
                    )
                except sqlite3.Error:
                    try:
                        con.execute("ROLLBACK")
                    except sqlite3.Error:
                        pass
                    raise
                current = version
            for pid, name in (
                ("toori-network-drive", "Сетевой диск Тоори"),
                ("dragon-torri", "Детский король / Дракончик Торри"),
            ):
                con.execute(
                    "INSERT OR IGNORE INTO projects VALUES (?, ?, 'work', ?)",
                    (pid, name, now()),
                )

    def schema_version(self):
        with self.connect() as con:
            return con.execute("PRAGMA user_version").fetchone()[0]

    def projects(self, scope):
        if scope not in {"home", "work"}:
            raise ValueError("Недопустимая область проекта")
        with self.connect() as con:
            return [
                dict(row)
                for row in con.execute(
                    "SELECT id, name, scope FROM projects WHERE scope=? ORDER BY name",
                    (scope,),
                )
            ]

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
                project = con.execute(
                    "SELECT scope FROM projects WHERE id=?", (project_id,)
                ).fetchone()
            if project is None or project["scope"] != scope:
                raise ValueError("Проект не принадлежит выбранной области")

    def memories(self, scope, project_id=None):
        self.validate_context(scope, project_id)
        with self.connect() as con:
            if project_id is None:
                rows = con.execute(
                    "SELECT id, text, scope, project_id, created_at FROM memories "
                    "WHERE scope=? AND project_id IS NULL ORDER BY created_at DESC LIMIT 100",
                    (scope,),
                )
            else:
                rows = con.execute(
                    "SELECT id, text, scope, project_id, created_at FROM memories "
                    "WHERE scope=? AND project_id=? ORDER BY created_at DESC LIMIT 100",
                    (scope, project_id),
                )
            return [dict(row) for row in rows]

    def add_memory(self, text, scope, project_id=None):
        self.validate_context(scope, project_id)
        text = text.strip()
        if not 1 <= len(text) <= 4000:
            raise ValueError("Запись должна содержать от 1 до 4000 символов")
        item = {
            "id": str(uuid.uuid4()),
            "text": text,
            "scope": scope,
            "project_id": project_id,
            "created_at": now(),
        }
        with self.connect() as con:
            con.execute(
                "INSERT INTO memories(id,text,scope,project_id,created_at) VALUES (?,?,?,?,?)",
                (item["id"], text, scope, project_id, item["created_at"]),
            )
        return item

    def health(self):
        with self.connect() as con:
            integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
            version = con.execute("PRAGMA user_version").fetchone()[0]
        return {
            "database": "ok" if integrity == "ok" else "error",
            "schema_version": version,
        }

    @staticmethod
    def _sha256(path):
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def backup(self):
        """Create a consistent snapshot while the core is running."""
        directory = self.root / "backups"
        directory.mkdir(parents=True, exist_ok=True)
        name = (
            "tooru-"
            + datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
            + "-"
            + uuid.uuid4().hex[:8]
            + ".db"
        )
        target = directory / name
        temporary = directory / (name + ".tmp")
        checksum_tmp = directory / (name + ".sha256.tmp")
        try:
            with closing(self.connect()) as source, closing(
                sqlite3.connect(temporary)
            ) as destination:
                source.backup(destination)
                integrity = destination.execute("PRAGMA integrity_check").fetchone()[0]
                if integrity != "ok":
                    raise RuntimeError("Проверка резервной копии не прошла")
            digest = self._sha256(temporary)
            checksum_tmp.write_text(digest + "  " + name + "\n", encoding="ascii")
            os.replace(temporary, target)
            os.replace(checksum_tmp, directory / (name + ".sha256"))
            return {
                "file": "backups/" + name,
                "sha256": digest,
                "bytes": target.stat().st_size,
                "schema_version": self.schema_version(),
            }
        except (sqlite3.Error, OSError) as exc:
            target.unlink(missing_ok=True)
            raise RuntimeError(
                "Не удалось создать копию базы. Проверьте свободное место и доступ к диску"
            ) from exc
        finally:
            temporary.unlink(missing_ok=True)
            checksum_tmp.unlink(missing_ok=True)

    def _resolve_backup(self, file_name):
        directory = (self.root / "backups").resolve()
        requested = Path(file_name)
        if requested.is_absolute():
            raise ValueError("Укажите файл из папки backups")
        if requested.parts and requested.parts[0] == "backups":
            requested = Path(*requested.parts[1:])
        if len(requested.parts) != 1 or requested.suffix.lower() != ".db":
            raise ValueError("Укажите файл .db из папки backups")
        target = (directory / requested.name).resolve()
        if not target.is_relative_to(directory) or not target.is_file():
            raise ValueError("Резервная копия не найдена")
        return target

    def _validate_snapshot(self, path, expected_sha256=None):
        actual_sha256 = self._sha256(path)
        if expected_sha256:
            if actual_sha256.lower() != expected_sha256.strip().lower():
                raise RuntimeError("SHA-256 резервной копии не совпадает")
        else:
            sidecar = Path(str(path) + ".sha256")
            if not sidecar.is_file():
                raise RuntimeError("Для резервной копии отсутствует файл SHA-256")
            expected = sidecar.read_text(encoding="ascii").split()[0]
            if actual_sha256.lower() != expected.lower():
                raise RuntimeError("SHA-256 резервной копии не совпадает")
        with closing(sqlite3.connect(path)) as con:
            integrity = con.execute("PRAGMA integrity_check").fetchone()[0]
            version = con.execute("PRAGMA user_version").fetchone()[0]
        migrations = self._migrations()
        latest = migrations[-1][0] if migrations else 0
        if integrity != "ok":
            raise RuntimeError("Резервная копия SQLite повреждена")
        if version > latest:
            raise RuntimeError(
                f"Резервная копия имеет схему {version}, а это ядро поддерживает только до {latest}"
            )
        return actual_sha256, version

    def restore_backup(self, file_name, expected_sha256=None):
        """Restore a verified backup and keep an automatic pre-restore snapshot."""
        source = self._resolve_backup(file_name)
        actual_sha256, source_version = self._validate_snapshot(source, expected_sha256)
        safety = self.backup()
        staging = self.path.with_name(self.path.name + ".restore.tmp")
        try:
            with closing(sqlite3.connect(source)) as src, closing(
                sqlite3.connect(staging)
            ) as dst:
                src.backup(dst)
                if dst.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                    raise RuntimeError("Не удалось подготовить базу для восстановления")
            os.replace(staging, self.path)
            self.initialize()
            if self.health()["database"] != "ok":
                raise RuntimeError("Восстановленная база не прошла проверку")
            return {
                "restored_from": "backups/" + source.name,
                "sha256": actual_sha256,
                "source_schema_version": source_version,
                "schema_version": self.schema_version(),
                "safety_backup": safety["file"],
            }
        except (sqlite3.Error, OSError, RuntimeError) as exc:
            try:
                safety_source = self.root / safety["file"]
                with closing(sqlite3.connect(safety_source)) as src, closing(
                    sqlite3.connect(staging)
                ) as dst:
                    src.backup(dst)
                os.replace(staging, self.path)
                self.initialize()
            except (sqlite3.Error, OSError, RuntimeError):
                pass
            if isinstance(exc, RuntimeError):
                raise
            raise RuntimeError("Не удалось восстановить резервную копию") from exc
        finally:
            staging.unlink(missing_ok=True)
