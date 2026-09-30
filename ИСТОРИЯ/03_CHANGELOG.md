# Изменения

Автор: Матиенко Антон Александрович · Aspksa@yandex.ru

## 0.1.0 — первая реализация

Созданы ядро, SQLite, локальный API и веб-интерфейс. Добавлены исходные проекты, изоляция памяти, подключение к локальной Ollama, Windows launcher и интеграционные проверки.

Добавлены online backup SQLite с `PRAGMA integrity_check` и SHA-256, миграции `database/migrations/NNN_*.sql`, восстановление SQLite из `backups/` с обязательной проверкой и safety-backup.

Добавлена защита одного экземпляра Tooru Core через OS-level lock `runtime_state/core.lock`. Launcher проверяет identity ядра и согласован с `TOORU_PORT`.

Закрыта гонка запуска: порядок начинается с `instance lock → bind localhost port`; конфликт рабочего порта завершается до изменения Crash Recovery state и до открытия SQLite.

`SETUP.bat` реализует проверяемую подготовку portable Python 3.14.7 из официального embeddable package с зафиксированными SHA-256, staging и rollback без PowerShell. Функциональная Windows/SSD-проверка installer ещё требуется.

Добавлен базовый Crash Recovery в `core/recovery.py`. `runtime_state/state.json` хранит состояния `starting/running/stopped`, clean-shutdown marker, данные предыдущего завершения, `recovery_count`, необходимость восстановления и результат проверки. Запись выполняется атомарно через временный файл и `os.replace`.

После незавершённой или неизвестной предыдущей сессии ядро до обычного запуска HTTP-сервера проверяет SQLite. Успешная проверка фиксируется как `recovery_status=ok`; ошибка прекращает обычный запуск с кодом 4.

Необработанные startup/runtime исключения не записывают `clean_shutdown=true`. Раздел «Настройки» показывает состояние Crash Recovery, предыдущее завершение и результат recovery-проверки.

Добавлено 10 тестов Crash Recovery. Итоговая Linux-регрессия: 28/28 тестов; `compileall` и `node --check web/static/app.js` успешно.
