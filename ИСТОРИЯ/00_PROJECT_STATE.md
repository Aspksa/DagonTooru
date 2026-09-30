# Состояние проекта

Автор: Матиенко Антон Александрович · Aspksa@yandex.ru

Версия 0.1.0. Статус проекта: IN_PROGRESS.

IMPLEMENTED: локальный Python HTTP API, SQLite, разделение памяти personal/home/work и по проектам, два исходных рабочих проекта, создание проектов, локальный Ollama-адаптер, веб-интерфейс, частичная диагностика, online backup SQLite с SHA-256, миграции SQLite, восстановление проверенной копии базы через API, защита одного экземпляра Tooru Core и базовый Crash Recovery.

Crash Recovery ведёт `runtime_state/state.json` после успешного захвата OS-level single-instance lock. Состояние записывается атомарно через `state.json.tmp` + `os.replace`. Фиксируются `starting/running/stopped`, `clean_shutdown`, причина штатного завершения, предыдущее завершение, число обнаруженных recovery-событий и результат проверки.

Если предыдущая сессия была незавершённой либо `state.json` повреждён, ядро до запуска HTTP-сервера проверяет SQLite через `Storage.health()`. При успешной проверке recovery помечается `ok`; при ошибке ядро не продолжает обычный запуск и возвращает код 4. Необработанная startup-ошибка намеренно не пишет clean-shutdown marker, чтобы следующий запуск снова обнаружил аварию.

Статус Crash Recovery доступен через `/api/v1/system/status` и отображается в разделе «Настройки»: состояние восстановления, предыдущее завершение и результат recovery-проверки.

Portable Python installer остаётся IN_PROGRESS до фактической проверки `SETUP.bat` на Windows и внешнем SSD.

Проверено в Linux 2026-09-30: `python -m unittest discover -s tests -v` — 28/28; `python -m compileall -q core tests` — успешно; `node --check web/static/app.js` — успешно. Во время старых backup/restore тестов Python 3.13 выдаёт `ResourceWarning` о незакрытых SQLite connection; тесты не падают, проблема зафиксирована отдельно.

PLANNED: Safe Mode, Maintenance Mode, полный Backup Manager, AI provider/model manager, Internet Gateway/почта, очередь, события, мобильные приложения, публичная многопользовательская версия, updater и подписанные релизы.
