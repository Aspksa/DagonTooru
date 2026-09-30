# Архитектура

Автор: Матиенко Антон Александрович · Aspksa@yandex.ru

`core.server` запускает один локальный HTTP сервер на 127.0.0.1. `core.storage` управляет SQLite и политикой контекста. `core.ai` вызывает локальный Ollama. `web/static` работает через `/api/v1/`. Данные пользователя, модели и секреты исключены из Git.

До доступа к пользовательской базе `core.server` захватывает `InstanceLock` в `runtime_state/core.lock`. Windows использует `msvcrt.locking`, Unix-платформы — `fcntl.flock`. OS-lock является источником истины о работающем экземпляре; JSON внутри lock-файла используется только для диагностики.

Порядок запуска ядра: `InstanceLock → bind 127.0.0.1:TOORU_PORT → Crash Recovery state → Storage/migrations → SQLite recovery-check при необходимости → Ollama → serve_forever`. Поэтому если порт уже занят старой версией Тоору или другой программой, новый процесс завершится до изменения `state.json` текущей попыткой и до открытия SQLite.

`core.recovery.RecoveryState` ведёт `runtime_state/state.json`. Запись выполняется атомарно через `state.json.tmp`, flush/fsync и `os.replace`. Сессия сначала получает `state=starting` и `clean_shutdown=false`; после успешной подготовки Storage, AI и HTTP handler состояние переводится в `running`.

Только контролируемое завершение работающего сервера записывает `clean_shutdown=true`. Необработанные startup/runtime исключения оставляют marker незавершённым, чтобы следующий запуск обнаружил аварийную сессию.

При `previous_shutdown=unclean` либо неизвестном/повреждённом предыдущем state ядро выполняет `Storage.health()` до обычного запуска. Если SQLite сообщает `database=ok`, recovery фиксируется как успешный. Если проверка не проходит, обычный запуск прекращается с кодом 4. Safe Mode и Maintenance Mode пока не включаются автоматически.

`GET /api/v1/system/status` возвращает `crash_recovery` и объект `recovery`. Web-раздел «Настройки» отображает состояние Crash Recovery, тип предыдущего завершения и результат recovery-проверки.

Для launcher используется identity endpoint `GET /api/v1/system/identity`; `python -m core.server --probe` проверяет service id `dragon-tooru-core`, версию протокола и порт.

Схема SQLite управляется последовательными `database/migrations/NNN_*.sql` через `PRAGMA user_version`. Backup использует SQLite online backup API, `PRAGMA integrity_check` и SHA-256; restore проверяет источник и создаёт safety-backup.

Доступ пока рассчитан на одного владельца на одном компьютере. Аутентификация отсутствует; сервер не должен выставляться в сеть.
