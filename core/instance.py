"""Cross-platform single-instance lock for Tooru Core.

Дракончик Тоору
Автор: Матиенко Антон Александрович
E-mail: Aspksa@yandex.ru
"""

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

SERVICE_ID = "dragon-tooru-core"


def now():
    return datetime.now(timezone.utc).isoformat()


class InstanceAlreadyRunning(RuntimeError):
    """Raised when another Tooru Core process already owns the lock."""


class InstanceLock:
    def __init__(self, root: Path, port: int):
        self.root = Path(root)
        self.port = port
        self.path = self.root / "runtime_state" / "core.lock"
        self.handle = None
        self.metadata = None

    def _lock(self):
        self.handle.seek(0)
        if os.name == "nt":
            import msvcrt

            if os.fstat(self.handle.fileno()).st_size == 0:
                self.handle.write(b"{}")
                self.handle.flush()
            self.handle.seek(0)
            msvcrt.locking(self.handle.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl

            fcntl.flock(self.handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)

    def _unlock(self):
        if os.name == "nt":
            import msvcrt

            self.handle.seek(0)
            msvcrt.locking(self.handle.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            import fcntl

            fcntl.flock(self.handle.fileno(), fcntl.LOCK_UN)

    def _write_metadata(self, **extra):
        metadata = dict(self.metadata or {})
        metadata.update(extra)
        data = json.dumps(metadata, ensure_ascii=False, sort_keys=True).encode("utf-8")
        self.handle.seek(0)
        self.handle.write(data)
        self.handle.truncate()
        self.handle.flush()
        os.fsync(self.handle.fileno())
        self.metadata = metadata

    def acquire(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(self.path, os.O_RDWR | os.O_CREAT, 0o600)
        self.handle = os.fdopen(fd, "r+b")
        try:
            self._lock()
        except OSError as exc:
            self.handle.close()
            self.handle = None
            raise InstanceAlreadyRunning(
                "Дракончик Тоору уже запущен для этого экземпляра проекта"
            ) from exc

        self.metadata = {
            "service": SERVICE_ID,
            "instance_id": str(uuid.uuid4()),
            "pid": os.getpid(),
            "port": self.port,
            "started_at": now(),
            "state": "running",
        }
        try:
            self._write_metadata()
        except Exception:
            try:
                self._unlock()
            finally:
                self.handle.close()
                self.handle = None
            raise
        return self

    def release(self):
        if self.handle is None:
            return
        try:
            self._write_metadata(state="stopped", stopped_at=now())
        except OSError:
            pass
        try:
            self._unlock()
        finally:
            self.handle.close()
            self.handle = None

    def __enter__(self):
        return self.acquire()

    def __exit__(self, exc_type, exc, tb):
        self.release()
        return False

    def snapshot(self):
        return dict(self.metadata or {})
