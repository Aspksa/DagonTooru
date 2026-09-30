# Изменения

Автор: Матиенко Антон Александрович · Aspksa@yandex.ru

## 0.1.0 — первая реализация

Созданы ядро, SQLite, локальный API и веб-интерфейс. Добавлены исходные проекты, изоляция памяти, подключение к локальной Ollama, Windows launcher и интеграционные проверки. Исходная спецификация помещена в `docs/`.

Добавлены резервная копия SQLite с `PRAGMA integrity_check` и SHA-256, миграции `database/migrations/NNN_*.sql` с `PRAGMA user_version`, а также восстановление SQLite из `backups/` с обязательной проверкой и safety-backup текущей базы.

Добавлена защита одного экземпляра Tooru Core. Новый модуль `core/instance.py` удерживает OS-level lock `runtime_state/core.lock`: Windows использует `msvcrt.locking`, Linux/macOS — `fcntl.flock`. Повторный запуск останавливается до открытия SQLite.

Добавлен `GET /api/v1/system/identity` и режим `python -m core.server --probe`. Launcher теперь проверяет identity Тоору, а не просто наличие HTTP-ответа на порту.

Порядок запуска усилен до `instance lock → bind localhost port → Storage/migrations → AI → serve`. Это исключает открытие SQLite новым ядром, если порт ещё занят старой версией Тоору или другой программой.

Launcher теперь использует тот же `TOORU_PORT`, что и ядро, включая URL открываемого браузера и диагностическое сообщение.

Добавлены 4 теста single-instance/identity. В Linux отдельно проверено автоматическое освобождение OS-lock после принудительного завершения процесса-владельца.
