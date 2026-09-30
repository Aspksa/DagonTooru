# Состояние проекта

Автор: Матиенко Антон Александрович · Aspksa@yandex.ru

Версия 0.1.0. Статус проекта: IN_PROGRESS.

IMPLEMENTED: локальный Python HTTP API, SQLite, разделение памяти personal/home/work и по проектам, два исходных рабочих проекта, создание проектов, локальный Ollama-адаптер, веб-интерфейс, частичная диагностика, online резервная копия SQLite с SHA-256, миграции SQLite, восстановление проверенной копии базы через API и защита одного экземпляра Tooru Core.

Single-instance protection использует OS-level lock `runtime_state/core.lock`. Launcher проверяет настоящий Tooru Core через `/api/v1/system/identity` и режим `python -m core.server --probe`.

Portable Python installer: IN_PROGRESS. `SETUP.bat` теперь умеет выбрать архитектуру Windows (AMD64/ARM64/x86), скачать официальный Python 3.14.7 embeddable ZIP с python.org, проверить зафиксированный SHA-256 через `certutil`, распаковать через `tar.exe` в staging, добавить корень проекта в штатный `python*._pth`, проверить `import core.server` и только затем активировать `runtime/python`. Предыдущий runtime сохраняется для отката до успешной финальной проверки. PowerShell не используется.

Зафиксированные SHA-256 взяты из официального Windows release manifest Python 3.14.7. Контрактные тесты `tests/test_setup_contract.py` проверяют URLs, hashes, переносимые пути, отсутствие PowerShell-команды, staging и rollback.

Схема SQLite сейчас версии 1. Перед восстановлением автоматически создаётся safety-backup текущей базы.

Адаптер настроен на локальный Ollama `127.0.0.1:11435` с моделью `tooru-local:4b`.

Не подтверждено на пользовательской Windows/SSD: фактическая загрузка Python через новый `SETUP.bat`, распаковка штатным `tar.exe`, настройка `._pth`, rollback и повторный запуск launcher. Поэтому portable installer пока не переводится в полностью IMPLEMENTED.

PLANNED: полноценные AI provider/model manager, Internet Gateway/почта, очередь, события, мобильные приложения, публичная многопользовательская версия, полный Backup Manager, Crash Recovery/Safe Mode/Maintenance Mode, обновление и подписанные релизы.
