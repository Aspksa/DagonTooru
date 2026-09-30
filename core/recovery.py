"""Runtime state and crash-recovery markers for Tooru Core.

Дракончик Тоору
Автор: Матиенко Антон Александрович
E-mail: Aspksa@yandex.ru
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from .instance import SERVICE_ID

STATE_SCHEMA = 1


def now():
    return datetime.now(timezone.utc).isoformat()


class RuntimeState:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.path = self.root / "runtime_state" / "state.json"
        self.temporary = self.path.with_suffix(".json.tmp")
        self.current = {}

    def _read_previous(self):
        if not self.path.is_file():
            return {}, None
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}, "corrupt"
        if not isinstance(data, dict):
            return {}, "invalid"
        return data, None

    @staticmethod
    def _count(value):
        try:
            return max(0, int(value))
        except (TypeError, ValueError):
            return 0

    def _write(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(
            self.current, ensure_ascii=False, sort_keys=True, indent=2
        ) + "\n"
        try:
            with self.temporary.open("w", encoding="utf-8", newline="\n") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(self.temporary, self.path)
        finally:
            self.temporary.unlink(missing_ok=True)

    def begin(self, instance):
        previous, issue = self._read_previous()
        unclean = bool(issue) or (
            bool(previous) and not bool(previous.get("clean_shutdown"))
        )
        recovery_count = self._count(previous.get("recovery_count"))
        if unclean:
            recovery_count += 1

        self.current = {
            "schema": STATE_SCHEMA,
            "service": SERVICE_ID,
            "state": "running",
            "clean_shutdown": False,
            "pid": instance.get("pid"),
            "port": instance.get("port"),
            "instance_id": instance.get("instance_id"),
            "started_at": now(),
            "previous_unclean_shutdown": unclean,
            "previous_state_issue": issue,
            "previous_started_at": previous.get("started_at"),
            "previous_stopped_at": previous.get("stopped_at"),
            "previous_exit_reason": previous.get("exit_reason"),
            "recovery_count": recovery_count,
            "recovery_status": "pending" if unclean else "not_needed",
        }
        self._write()
        return self.snapshot()

    def record_recovery(self, database_status):
        if not self.current:
            raise RuntimeError("RuntimeState.begin() ещё не выполнен")
        self.current["recovery_status"] = (
            "ok" if database_status == "ok" else "error"
        )
        self.current["recovery_database"] = database_status
        self.current["recovery_checked_at"] = now()
        self._write()
        return self.snapshot()

    def finish(self, exit_reason="normal"):
        if not self.current:
            return {}
        self.current.update(
            {
                "state": "stopped",
                "clean_shutdown": True,
                "stopped_at": now(),
                "exit_reason": exit_reason,
            }
        )
        self._write()
        return self.snapshot()

    def snapshot(self):
        return dict(self.current)
