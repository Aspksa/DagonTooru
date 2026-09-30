# Архитектура

Автор: Матиенко Антон Александрович · Aspksa@yandex.ru

`core.server` запускает один локальный HTTP сервер на 127.0.0.1. `core.storage` управляет SQLite и политикой контекста. `core.ai` вызывает только локальный Ollama. `web/static` работает через `/api/v1/`. Данные пользователя, модели и секреты исключены из Git.

До инициализации SQLite `core.server` захватывает `InstanceLock` в `runtime_state/core.lock`. Windows использует `msvcrt.locking`, Unix-платформы — `fcntl.flock`. OS-lock является источником истины о работающем экземпляре; JSON в lock-файле — только диагностика.

После захвата instance lock создаётся `RecoveryState` из `core/recovery.py`. Он ведёт `runtime_state/state.json` и пишет его атомарно через временный файл, flush/fsync и `os.replace`. Только после этого инициализируется Storage.

Сессия сначала имеет `state=starting` и `clean_shutdown=false`. После успешной подготовки HTTP-сервера состояние переводится в `running`. Только контролируемое завершение (`KeyboardInterrupt`, штатная остановка или обработанный конфликт порта) может записать `clean_shutdown=true`. Необработанные startup/runtime исключения оставляют marker незавершённым.

При `previous_shutdown=unclean` или неизвестном/повреждённом предыдущем state ядро запускает базовую recovery-проверку SQLite. `Storage.health()` должен вернуть `database=ok`; результат сохраняется как `recovery_status` и `recovery_database`. Если SQLite не проходит проверку, обычный запуск прекращается с кодом 4. Safe Mode и Maintenance Mode пока не включаются автоматически.

`GET /api/v1/system/status` возвращает `crash_recovery` и объект `recovery`; web-настройки отображают текущий recovery-status и тип предыдущего завершения.

Схема SQLite управляется последовательными `database/migrations/NNN_*.sql` через `PRAGMA user_version`. Backup использует SQLite online backup API, `PRAGMA integrity_check` и SHA-256; restore проверяет источник и создаёт safety-backup.

Доступ пока рассчитан на одного владельца на одном компьютере. Аутентификация отсутствует; сервер не должен выставляться в сеть.
