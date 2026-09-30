# Следующее действие

Автор: Матиенко Антон Александрович · Aspksa@yandex.ru

Версия: 0.1.0.

Сделано в текущей сессии: реализован базовый Crash Recovery через `core/recovery.py` и `runtime_state/state.json`. Сохранён безопасный порядок запуска: `OS-lock → bind рабочего localhost-порта → Crash Recovery state → Storage/migrations → recovery-check → Ollama → server`.

После незавершённой или повреждённой предыдущей сессии выполняется `Storage.health()` для SQLite. При `database=ok` recovery фиксируется как успешный; при ошибке обычный запуск останавливается с кодом 4. Необработанная startup/runtime ошибка не пишет clean shutdown.

Добавлены `crash_recovery` и `recovery` в `/api/v1/system/status`. В web-разделе «Настройки» отображаются Crash Recovery, тип предыдущего завершения и результат recovery-проверки.

Проверено в Linux 2026-09-30: `python -m unittest discover -s tests -v` — 28/28; `python -m compileall -q core tests` — успешно; `node --check web/static/app.js` — успешно. Отдельно проверено, что при конфликте рабочего порта новый процесс не меняет `state.json` и не открывает Storage/SQLite.

Изменённые файлы: `core/recovery.py`, `core/server.py`, `tests/test_recovery.py`, `web/static/app.js`, README и документация `ИСТОРИЯ/`.

Не закончено: фактическая Windows/SSD-проверка Crash Recovery, portable installer, `msvcrt.locking` и конфликта порта; Safe Mode; Maintenance Mode; полный Backup Manager.

Технический долг: Linux-регрессия на Python 3.13 выдаёт `ResourceWarning` о незакрытых SQLite connection во время существующих backup/restore тестов. Тесты проходят, но lifecycle соединений нужно отдельно проверить и исправить.

Следующая практическая проверка на Windows: запустить ядро, принудительно завершить процесс без штатного shutdown, снова запустить `ДракончикТоору.bat` и убедиться, что в «Настройках» видно предыдущее аварийное завершение и SQLite recovery `ok`; затем проверить штатное закрытие/повторный запуск, повторный launcher и конфликт `TOORU_PORT`.

Следующая задача разработки: Safe Mode на основе `recovery_needed/recovery_status`, затем Maintenance Mode. Safe Mode не должен автоматически менять пользовательские данные; он должен запускать минимальный набор компонентов и диагностику.

Следующий ChatGPT обязан сначала прочитать `AGENTS.md`, всю `ИСТОРИЯ/`, затем `core/recovery.py`, `core/instance.py`, `core/server.py`, launcher и тесты.
