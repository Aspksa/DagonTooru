"""Crash-recovery state journal for Tooru Core.

Дракончик Тоору
Автор: Матиенко Антон Александрович
E-mail: Aspksa@yandex.ru
"""

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from .instance import SERVICE_ID

STATE_VERSION = 1


def now():
    return datetime.now(timezone.utc).isoformat()


class RecoveryState:
    """Track lifecycle history separately from the single-instance OS lock."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.directory = self.root / "runtime_state"
        self.path = self.directory / "state.json"
        self.temporary = self.directory / "state.json.tmp"
        self.data = {}

    def _read_previous(self):
        if not self.path.is_file():
            return None, None
        try:
            value = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError):
            return None, "invalid_state_file"
        if not isinstance(value, dict):
            return None, "invalid_state_file"
        return value, None

    @staticmethod
    def _previous_shutdown(previous, error):
        if error:
            return "unknown"
        if previous is None:
            return "first_start"
        if previous.get("clean_shutdown") is True:
            return "clean"
        return "unclean"

    @staticmethod
    def _count(value):
        try:
            return max(0, int(value))
        except (TypeError, ValueError):
            return 0

    def _write(self):
        self.directory.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(
            self.data, ensure_ascii=False, indent=2, sort_keys=True
        ) + "\n"
        try:
            with self.temporary.open("w", encoding="utf-8", newline="\n") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(self.temporary, self.path)
        except OSError as exc:
            self.temporary.unlink(missing_ok=True)
            raise RuntimeError(
                "Не удалось записать runtime_state/state.json"
            ) from exc

    def start(self, instance):
        previous, error = self._read_previous()
        previous_shutdown = self._previous_shutdown(previous, error)
        immediate_recovery = previous_shutdown in {"unclean", "unknown"}
        inherited_recovery = bool(previous and previous.get("recovery_needed"))
        recovery_needed = immediate_recovery or inherited_recovery
        recovery_count = self._count(previous and previous.get("recovery_count"))
        if immediate_recovery:
            recovery_count += 1

        previous_summary = None
        if previous:
            previous_summary = {
                key: previous.get(key)
                for key in (
                    "instance_id",
                    "pid",
                    "port",
                    "started_at",
                    "stopped_at",
                    "state",
                    "clean_shutdown",
                    "shutdown_reason",
                    "recovery_status",
                    "recovery_needed",
                )
                if key in previous
            }

        self.data = {
            "version": STATE_VERSION,
            "service": SERVICE_ID,
            "instance_id": instance.get("instance_id"),
            "pid": instance.get("pid"),
            "port": instance.get("port"),
            "started_at": instance.get("started_at") or now(),
            "updated_at": now(),
            "state": "starting",
            "clean_shutdown": False,
            "previous_shutdown": previous_shutdown,
            "previous_crash": previous_shutdown == "unclean",
            "recovery_needed": recovery_needed,
            "recovery_status": "pending" if recovery_needed else "not_needed",
            "recovery_count": recovery_count,
        }
        if previous_summary:
            self.data["previous"] = previous_summary
        if error:
            self.data["previous_state_error"] = error
        self._write()
        return self.snapshot()

    def record_recovery(self, database_status):
        if not self.data:
            raise RuntimeError("Crash Recovery не инициализирован")
        status = "ok" if database_status == "ok" else "error"
        self.data.update(
            recovery_status=status,
            recovery_database=database_status,
            recovery_checked_at=now(),
            recovery_needed=status != "ok",
            updated_at=now(),
        )
        self._write()
        return self.snapshot()

    def mark_running(self):
        if not self.data:
            raise RuntimeError("Crash Recovery не инициализирован")
        self.data.update(
            state="running",
            clean_shutdown=False,
            updated_at=now(),
        )
        self._write()
        return self.snapshot()

    def mark_clean_shutdown(self, reason="normal", resolve_recovery=True):
        if not self.data:
            return {}
        timestamp = now()
        self.data.update(
            state="stopped",
            clean_shutdown=True,
            shutdown_reason=reason,
            stopped_at=timestamp,
            updated_at=timestamp,
        )
        if resolve_recovery:
            self.data["recovery_needed"] = False
            if self.data.get("recovery_status") == "pending":
                self.data["recovery_status"] = "resolved"
        self._write()
        return self.snapshot()

    def snapshot(self):
        return dict(self.data)
