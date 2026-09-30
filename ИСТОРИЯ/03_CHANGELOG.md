# Изменения

Автор: Матиенко Антон Александрович · Aspksa@yandex.ru

## 0.1.0 — первая реализация

Созданы ядро, SQLite, локальный API и веб-интерфейс. Добавлены исходные проекты, изоляция памяти, локальная Ollama, Windows launcher и интеграционные проверки.

Добавлены online backup SQLite с `PRAGMA integrity_check` и SHA-256, миграции `database/migrations/NNN_*.sql`, восстановление SQLite из `backups/` с safety-backup, а также защита одного экземпляра Tooru Core.

`SETUP.bat` реализует проверяемую подготовку portable Python 3.14.7 из официального embeddable package с зафиксированными SHA-256, staging и rollback. Windows/SSD-проверка installer ещё требуется.

Добавлен базовый Crash Recovery в `core/recovery.py`. `runtime_state/state.json` хранит clean-shutdown marker, состояние `starting/running/stopped`, данные предыдущего завершения, `recovery_count` и результат recovery-проверки. Запись выполняется атомарно через временный файл и `os.replace`.

После незавершённой или неизвестной предыдущей сессии ядро до обычного старта HTTP-сервера проверяет SQLite. Успешная проверка фиксируется как `recovery_status=ok`; ошибка останавливает обычный запуск с кодом 4.

Исправлена семантика аварий: необработанный `startup_error` не может записать `clean_shutdown=true`. Обработанный конфликт порта фиксируется как контролируемое завершение. Незавершённый recovery-сигнал не теряется из-за обработанной неуспешной попытки запуска.

`/api/v1/system/status` теперь возвращает `crash_recovery` и `recovery`. Раздел «Настройки» отображает состояние Crash Recovery, предыдущее завершение и результат recovery-проверки.

Добавлено 10 тестов Crash Recovery. Полная Linux-регрессия: 28/28 тестов; `compileall` и `node --check web/static/app.js` успешно.
