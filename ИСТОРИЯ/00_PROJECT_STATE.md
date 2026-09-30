# Состояние проекта

Автор: Матиенко Антон Александрович · Aspksa@yandex.ru

Версия 0.1.0. Статус проекта: IN_PROGRESS.

IMPLEMENTED: локальный Python HTTP API, SQLite, разделение памяти personal/home/work и по проектам, два исходных рабочих проекта, создание проектов, локальный Ollama-адаптер, веб-интерфейс, частичная диагностика, online backup SQLite с SHA-256, миграции SQLite, восстановление проверенной копии базы через API, защита одного экземпляра Tooru Core и базовый Crash Recovery.

Single-instance protection использует OS-level lock `runtime_state/core.lock`. Launcher проверяет настоящий Tooru Core через `/api/v1/system/identity` и режим `python -m core.server --probe`.

Фактический порядок запуска: `InstanceLock → bind 127.0.0.1:TOORU_PORT → Crash Recovery state → Storage/migrations → SQLite recovery-check при необходимости → Ollama → serve_forever`. Поэтому конфликт порта завершается до изменения recovery-state текущей попыткой и до открытия SQLite.

Crash Recovery ведёт `runtime_state/state.json` атомарно через `state.json.tmp` + `os.replace`. Фиксируются `starting/running/stopped`, `clean_shutdown`, причина штатного завершения, предыдущее завершение, `recovery_count`, необходимость восстановления и результат проверки.

Если предыдущая сессия была незавершённой либо `state.json` повреждён, ядро до обычного запуска сервера проверяет SQLite через `Storage.health()`. При `database=ok` recovery фиксируется как `ok`; при ошибке обычный запуск прекращается с кодом 4. Необработанная startup/runtime ошибка не записывает clean-shutdown marker.

`/api/v1/system/status` возвращает `crash_recovery` и `recovery`; раздел «Настройки» отображает Crash Recovery, предыдущее завершение и результат recovery-проверки.

Portable Python installer: IN_PROGRESS. `SETUP.bat` подготавливает официальный Python 3.14.7 embeddable package для AMD64/ARM64/x86, проверяет SHA-256, использует staging и rollback без PowerShell. Реальная Windows/SSD-проверка installer ещё не выполнена.

Updater: IN_PROGRESS. В репозитории добавлен `docs/UPDATE_SYSTEM.md` с release-контрактом, protected paths, двухфазной моделью и требованиями SHA-256 + Ed25519. Локальный прототип updater прошёл 7/7 security-тестов, но код скачивания/применения обновления не merged в репозиторий: подключённый GitHub-инструмент заблокировал запись самоприменяющегося updater-кода. Реального `security/public_key.pem` пока нет; создавать фиктивный ключ запрещено.

Проверено в Linux 2026-09-30: `python -m unittest discover -s tests -v` — 28/28; `python -m compileall -q core tests` — успешно; `node --check web/static/app.js` — успешно. Отдельно локальный прототип updater: 7/7 тестов.

PLANNED: Safe Mode, Maintenance Mode, полный Backup Manager, AI provider/model manager, Internet Gateway/почта, очередь, события, мобильные приложения, публичная многопользовательская версия и завершение подписанного updater.
