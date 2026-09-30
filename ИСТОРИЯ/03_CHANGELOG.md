# Изменения

Автор: Матиенко Антон Александрович · Aspksa@yandex.ru

## 0.1.0 — первая реализация

Созданы ядро, SQLite, локальный API и веб-интерфейс. Добавлены исходные проекты, изоляция памяти, подключение к локальной Ollama, Windows launcher и интеграционные проверки.

Добавлены резервная копия SQLite с `PRAGMA integrity_check` и SHA-256, миграции `database/migrations/NNN_*.sql` с `PRAGMA user_version`, а также восстановление SQLite из `backups/` с обязательной проверкой и safety-backup текущей базы.

Добавлена защита одного экземпляра Tooru Core через OS-level lock `runtime_state/core.lock`. Добавлены identity endpoint и режим `python -m core.server --probe`; launcher больше не принимает любой HTTP-ответ на порту 8765 за ядро Тоору.

`SETUP.bat` переработан из справочного файла в проверяемый portable installer. Он:
- определяет AMD64/ARM64/x86;
- скачивает официальный Python 3.14.7 embeddable package с python.org;
- сверяет SHA-256 с зафиксированным значением;
- распаковывает во временный `runtime/python.new`;
- добавляет относительный путь к корню проекта в штатный `python*._pth`;
- проверяет `import core.server`;
- сохраняет предыдущий runtime до финальной проверки и выполняет rollback при ошибке;
- не использует PowerShell.

Добавлен `tests/test_setup_contract.py` с 4 контрактными тестами installer-конфигурации. В локальном Linux harness они прошли 4/4. Функциональная Windows/SSD-проверка нового SETUP ещё требуется.
